from enum import Enum, auto
from multiprocessing import Process, Queue

from PySide2 import QtGui, QtCore
import cv2
import numpy as np
import queue

from PySide2.QtCore import QTimer, QObject

from mccc import MCC
import time
import torch
from caiman.utils.visualization import get_contours
def getFrame(q):
    print(1)
    pass

class VideoSavingStatus(Enum):
    STARTING = auto()
    PAUSING = auto()
    STOPPING = auto()
    STOPPED = auto()

class OProcess(Process):
    def __init__(self, camera: str):
        super(OProcess, self).__init__()
        self.c_number = camera
        self.ged_template = None
        self.MC = None

        self.fps = 0.0
        self.cfps = 30.0
        self.sfps = 0.0
        self.loop_time = 0

        self.status = VideoSavingStatus.STARTING
        self.exposure_status = 0  ##
        self.gain_status = 16  ##
        self.hue_status = 0
        self.buffer = []
        self.rtProcess = False
        self.cur_frame = 0
        self.total_frame = 0
        self.s_timer = 0

        self.fakecapture = True
        self.isAutoROI = False
        self.autoROI = None

        self.cap_init()

        self.q = Queue()

        self.ptime = None
        self.timelist = []

class OPlayer(QtCore.QThread):

    frameI = QtCore.Signal(QtGui.QImage)
    frameG = QtCore.Signal(list)
    roi_pos = QtCore.Signal(list)
    q = Queue()
    def __init__(self, camera: str,  ## temp
            lock: QtCore.QMutex, parent: QtCore.QObject):
        super().__init__(parent=parent)
        self.data_lock = lock
        self.c_number = camera
        self.ged_template = None
        self.MC = None
        self.ROItable = parent.onroi_table
        self.parent = parent

        self.fps = 0.0
        self.cfps = 30.0
        self.sfps = 0.0
        self.loop_time = 0

        self.status = VideoSavingStatus.STARTING
        self.exposure_status = 0  ##
        self.gain_status = 16  ##
        self.hue_status = 0
        self.buffer = []
        self.rtProcess = False
        self.cur_frame = 0
        self.total_frame = 0
        self.s_timer = 0

        self.fakecapture = True
        self.isAutoROI = False
        self.autoROI = None

        self.cap_init()

        self.q = Queue()


        self.ptime = None
        self.timelist = []
    def displayImage(self, q):
        while True:
            if q.empty():
                time.sleep(0.01)
                continue
            image = q.pop()
            self.parent.online_frame(image)

    def getFrames(self,q):
        capture = self.capture
        while True:
            t0 = time.time()
            ret, frame = capture.read()
            if not ret:
                if self.fakecapture:
                    capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

            if self.exposure_status != self.exposure:  ## > change to bool type?
                # print("before input t E: ", self.exposure)
                self.exposure = capture.get(cv2.CAP_PROP_BRIGHTNESS)
                # self.exposure = cap.get(cv2.CAP_PROP_EXPOSURE)
                print("pre-set,real:", self.exposure_status, self.exposure)
                # self.exposure_status == self.exposure
                self.exposure = self.exposure_status
                print("set,real:", self.exposure_status, self.exposure)
                self.change_exposure(capture, self.exposure_status)  ##
                print(capture.get(cv2.CAP_PROP_BRIGHTNESS))
                # print(cap.get(cv2.CAP_PROP_EXPOSURE))
            if self.gain_status != self.s_gain:
                print("B gain:", self.s_gain)  # -1
                self.s_gain = int(capture.get(cv2.CAP_PROP_GAIN))
                print("B gainS:", self.gain_status)  # 20
                self.s_gain = self.gain_status
                print("gain status:", self.gain_status)  # -1
                self.change_gain(capture, self.gain_status)
                print("get", capture.get(cv2.CAP_PROP_GAIN))
            if self.hue_value != self.hue_status:
                outV = self.change_led(capture, self.hue_value)  #
                capture.set(cv2.CAP_PROP_HUE, (outV >> 4) & 0x00FF)  #
                print("LED(v/s/h): ", self.hue_value, self.hue_status, capture.get(cv2.CAP_PROP_HUE))  ##
                self.hue_status = self.hue_value

            if self.cfps != self.sfps:
                self.sfps = self.cfps
                self.fps_switch(capture, self.sfps)
                self.loop_time = 1.0 / self.sfps
                print('sfps:', self.sfps)
                capture.set(cv2.CAP_PROP_FPS, self.sfps)
                print('fps changed:', self.sfps)

            if type(self.ged_template) != type(None):
                t0 = time.time()
                frame, _ = self.MC.on_mc(self.ged_template, frame)
                self.MC.c_onmc += 1
                print('processed ', self.MC.c_onmc)
                t1 = time.time()
                print('MC time: ', t1 - t0)


            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.frameG.emit(gray)

            tmp_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.data_lock.lock()
            self.frame = tmp_frame
            height, width, dim = self.frame.shape
            bytesPerLine = dim * width
            image = QtGui.QImage(self.frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
            self.data_lock.unlock()
            #self.frameI.emit(image)

            q.put(image)

            delay = time.time() - t0
            self.fps_delay(delay)
            print('single loop fps:', 1/(time.time()-t0))

            # print('frame trans time: ', time.time() - t2)
            # if not self.ptime:
            #     self.ptime = time.time()
            #     self.timelist.append(self.ptime)
            # else:
            #     ct = time.time()
            #     tt = ct - self.ptime
            #     self.ptime = ct
            #     self.timelist.append(ct)
            #     if len(self.timelist) > 100:
            #         self.timelist.pop(0)
            #     print('current fps:', 1 / tt)
            #     print('recent 100 fps:', len(self.timelist) / (ct - self.timelist[0]))
            #     # print('frame cycle time: ', tt)



    def cap_init(self):
        self.capture = cv2.VideoCapture(self.c_number + cv2.CAP_DSHOW)
        if self.fakecapture:
            # self.capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\Downloads\\Video\\demoMovie.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\demoMovie_out.avi")
            #self.capture = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\CaImAn_demo.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\msCam13_mcc.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\Desktop\\out_movie2.avi")
            self.capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\caiman_data\\example_movies\\msCam1.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\msCam1.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\demoMovie.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\CaImAn_demo.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\data_endoscope.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\\blood_vessel_10Hz.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\CaImAn_demo_out.avi")


        capture = self.capture
        self.exposure = int(capture.get(cv2.CAP_PROP_EXPOSURE))
        self.s_gain = int(capture.get(cv2.CAP_PROP_GAIN))
        self.hue_value = 0

        self.height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                # capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                # capture.set(cv2.CAP_PROP_FPS, 30)
                # capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))

    def setAutoROI(self, cm):
        self.autoROI = cm

    def updates(self):
        capture = self.capture
        st = time.time()
        ret, frame = capture.read()
        t1 = time.time()
        # print('frame start: ', st)
        # print('read:',t1-st)
        if not ret:
            if self.fakecapture:
                capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return
        # if self.ptime is not None:
        #     print('Interval:', time.time() - self.ptime)

        if self.rtProcess:
            self.timer.setInterval(1)
        # if self.rtProcess:
        #     if self.status == VideoSavingStatus.STARTING:
        #         self.cur_frame += 1
        #     self.total_frame += 1

        # frame = cv2.resize(frame, dsize=(400, 300), interpolation=cv2.INTER_CUBIC)

        if self.exposure_status != self.exposure:  ## > change to bool type?
            # print("before input t E: ", self.exposure)
            self.exposure = capture.get(cv2.CAP_PROP_BRIGHTNESS)
            # self.exposure = cap.get(cv2.CAP_PROP_EXPOSURE)
            print("pre-set,real:", self.exposure_status, self.exposure)
            # self.exposure_status == self.exposure
            self.exposure = self.exposure_status
            print("set,real:", self.exposure_status, self.exposure)
            self.change_exposure(capture, self.exposure_status)  ##
            print(capture.get(cv2.CAP_PROP_BRIGHTNESS))
            # print(cap.get(cv2.CAP_PROP_EXPOSURE))
        if self.gain_status != self.s_gain:
            print("B gain:", self.s_gain)  # -1
            self.s_gain = int(capture.get(cv2.CAP_PROP_GAIN))
            print("B gainS:", self.gain_status)  # 20
            self.s_gain = self.gain_status
            print("gain status:", self.gain_status)  # -1
            self.change_gain(capture, self.gain_status)
            print("get", capture.get(cv2.CAP_PROP_GAIN))
        if self.hue_value != self.hue_status:
            outV = self.change_led(capture, self.hue_value)  #
            capture.set(cv2.CAP_PROP_HUE, (outV >> 4) & 0x00FF)  #
            print("LED(v/s/h): ", self.hue_value, self.hue_status, capture.get(cv2.CAP_PROP_HUE))  ##
            self.hue_status = self.hue_value

        if self.cfps != self.sfps:
            self.sfps = self.cfps
            self.fps_switch(capture, self.sfps)
            self.loop_time = 1000 / self.sfps - 20
            print('sfps:', self.sfps)

            capture.set(cv2.CAP_PROP_FPS, self.sfps)
            print('fps changed:', self.sfps)

        if type(self.ged_template) != type(None):
            t0 = time.time()
            # frame, _ = MCC(self.c_number, self).on_mc(self.ged_template, frame) ##,self.ged_template
            frame, _ = self.MC.on_mc(self.ged_template, frame)
            self.MC.c_onmc += 1
            print('processed ', self.MC.c_onmc)
            t1 = time.time()
            print('MC time: ', t1 - t0)

        t2 = time.time()


        # print('1:',1/(time.time() - S))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.frameG.emit(gray)
        #
        # if self.isAutoROI:
        #     t0 = time.time()
        #     if self.autoROI.cnmf.N > self.ROItable.size():
        #         self.ROIupdate()
        #     t1 = time.time()
        #     print('ROI process time: ', t1 - t0)

        t3 = time.time()

        tmp_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.data_lock.lock()
        self.frame = tmp_frame
        height, width, dim = self.frame.shape
        bytesPerLine = dim * width
        image = QtGui.QImage(self.frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
        self.data_lock.unlock()
        self.frameI.emit(image)

        # print('frame trans time: ', time.time() - t2)
        if not self.ptime:
            self.ptime = time.time()
            self.timelist.append(self.ptime)
        else:
            ct = time.time()
            tt = ct - self.ptime
            self.ptime = ct
            self.timelist.append(ct)
            if len(self.timelist) > 100:
                self.timelist.pop(0)
            print('current fps:', 1 / tt)
            print('recent 100 fps:', len(self.timelist) / (ct - self.timelist[0]))
            # print('frame cycle time: ', tt)

        et = time.time()
        # print('frame end: ', et)
        # delay = 23-(et-st)*1000
        # print('delay:', delay)
        # if delay < 0:
        #     self.timer.setInterval(1)
        # else:
        #     self.timer.setInterval(int(delay))

    # def ROIupdate(self):
    #     t0 = time.time()
    #     dims = (self.height, self.width)
    #     mat = self.autoROI.cnmf.estimates.A[:,self.ROItable.size():]
    #     comps = get_contours(mat, dims)
    #     self.roi_pos.emit(comps)
    #     t1 = time.time()
    #     print('ROI Update Time:', t1 - t0)


    def run(self):
        readProcess = Process(target=self.getFrames, args=(self.q,))
        displayProcess = Process(target=self.displayImage, args=(self.q,))
        readProcess.start()
        displayProcess.start()

    def stop(self):
        print('stopped - online')
        self.requestInterruption()
        self.wait()

    def fps_switch(self, cap: cv2.VideoCapture, n: int):

        if n == 20:
            cap.set(cv2.CAP_PROP_SATURATION, 0x14)
            print("fps:20")
        elif n == 30:
            cap.set(cv2.CAP_PROP_SATURATION, 0x15)
            print("fps:30")
        elif n == 60:
            cap.set(cv2.CAP_PROP_SATURATION, 0x16)
            print("fps:60")
        elif n == 15:
            cap.set(cv2.CAP_PROP_SATURATION, 0x13)
            print("fps:15")
        elif n == 10:
            cap.set(cv2.CAP_PROP_SATURATION, 0x12)
            print("fps:10")
        elif n == 5:
            cap.set(cv2.CAP_PROP_SATURATION, 0x11)
            print("fps:5")
        else:
            cap.set(cv2.CAP_PROP_SATURATION, 0x14)
            print("fps:20")

        ## {5: f1, 10: f2, 15: f3, 20: f4, 30: f5, 60: f6}.get(n,20)

    def set_fps(self):
        self.fser = False
        print("kick")

    def fps_delay(self, dis):
        delay = self.loop_time - 0.003 - dis
        if delay > 0:
            self.msleep(delay*1000)

    def change_exposure(self, cap: cv2.VideoCapture, exp_value):

        exp_value = exp_value / 64 * 255
        cap.set(cv2.CAP_PROP_BRIGHTNESS, exp_value)
        print('changed brightness: ', cap.get(cv2.CAP_PROP_BRIGHTNESS))
        # cap.set(cv2.CAP_PROP_EXPOSURE, exp_value)
        # print('changed exposure: ', cap.get(cv2.CAP_PROP_EXPOSURE))

    def change_gain(self, cap: cv2.VideoCapture, ga_value):
        if ga_value >= 32 and (ga_value % 2) == 1:
            ga_value += 1
        cap.set(cv2.CAP_PROP_GAIN, ga_value)

    def change_led(self, cap: cv2.VideoCapture, l_value):
        outV = np.uint16(l_value * (0x0FFF) / 1000) | (0x3000)
        print(outV)
        return outV


    def pause(self):
        self.status = VideoSavingStatus.PAUSING

    def play(self):
        self.status = VideoSavingStatus.STARTING

    @property
    def isPlaying(self):
        return self.status == VideoSavingStatus.STARTING
