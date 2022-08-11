from enum import Enum, auto
from PySide2 import QtGui, QtCore
import cv2
import numpy as np
import queue

from PySide2.QtCore import QTimer

from mccc import MCC
import time
import torch
from caiman.utils.visualization import get_contours

class VideoSavingStatus(Enum):
    STARTING = auto()
    PAUSING = auto()
    STOPPING = auto()
    STOPPED = auto()

class OPlayer(QtCore.QThread):

    frameI = QtCore.Signal(QtGui.QImage)
    frameG = QtCore.Signal(list)
    fpsChanged = QtCore.Signal(float)
    roi_pos = QtCore.Signal(list)
    ## fImg = QtCore.Signal(np.ndarray)

    def __init__(self, camera: str,  ## temp
            lock: QtCore.QMutex, parent: QtCore.QObject):
        super().__init__(parent=parent)
        self.data_lock = lock
        self.c_number = camera
        self.ged_template = None
        self.MC = None
        self.ROItable = parent.onroi_table

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
        self.file_save = False
        self.file_count = 1
        self.file_size = 5000

        self.isAutoROI = False
        self.autoROI = None

        self.cap_init()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updates)
        self.timer.setInterval(30)

        self.ptime = None
        self.timelist = []

    def cap_init(self):
        self.capture = cv2.VideoCapture(self.c_number + cv2.CAP_DSHOW)
        if self.fakecapture:
            # self.capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\Downloads\\Video\\demoMovie.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\demoMovie_out.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\CaImAn_demo.mp4")
            # self.capture = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\msCam13_mcc.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\Desktop\\out_movie2.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\caiman_data\\example_movies\\msCam1.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\msCam1.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\demoMovie.avi")
            self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\CaImAn_demo.mp4")

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

        if self.rtProcess:
            if self.status == VideoSavingStatus.STARTING:
                self.cur_frame += 1
            self.total_frame += 1

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

        if self.isAutoROI:
            t0 = time.time()
            self.autoROI.frame_process(gray.data.obj)
            if self.autoROI.cnmf.N > self.ROItable.size():
                self.ROIupdate()
            t1 = time.time()
            print('ROI process time: ', t1 - t0)

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
            # print('current fps:', 1 / tt)
            # print('recent 100 fps:', len(self.timelist) / (ct - self.timelist[0]))
            # print('frame cycle time: ', tt)

        et = time.time()
        # print('frame end: ', et)
        # delay = (et-st)*1000
        # if delay < 0:
        #     self.timer.setInterval(0)
        # else:
        #     self.timer.setInterval(int(delay))

    def ROIupdate(self):
        t0 = time.time()
        dims = (self.height, self.width)
        mat = self.autoROI.cnmf.estimates.A[:,self.ROItable.size():]
        comps = get_contours(mat, dims)
        self.roi_pos.emit(comps)
        t1 = time.time()
        print('ROI Update Time:', t1 - t0)


    def run(self):
        capture = cv2.VideoCapture(self.c_number, cv2.CAP_DSHOW)
        # capture = cv2.VideoCapture(self.c_number)
        if self.fakecapture:
            #capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\Downloads\\Video\\msCam4.avi")
            #capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\Desktop\\out_movie.avi")
            capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\caiman_data\\example_movies\\msCam1.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\demoMovie.avi")
        self.exposure = int(capture.get(cv2.CAP_PROP_EXPOSURE))
        self.s_gain = int(capture.get(cv2.CAP_PROP_GAIN))
        self.hue_value = 0


        self.height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))

        tt = time.time()
        timelist= [tt]
        ptime = time.time()
        count = 0
        while not self.isInterruptionRequested():
            t0 = time.time()
            ret, frame = capture.read()
            t1 = time.time()
            print('read:', t1-t0)
            if not ret:
                if self.fakecapture:
                    capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break


            if self.rtProcess:
                if self.total_frame == 0:
                    self.s_timer = time.time()

                if self.status == VideoSavingStatus.STARTING:
                    self.cur_frame += 1
                self.total_frame += 1



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
                self.loop_time = 1 / self.sfps
                print('sfps:', self.sfps)

                capture.set(cv2.CAP_PROP_FPS, self.sfps)
                print('fps changed: ', self.sfps)

            if type(self.ged_template) != type(None):
                t0 = time.time()
                # frame, _ = MCC(self.c_number, self).on_mc(self.ged_template, frame) ##,self.ged_template 
                frame, _ = self.MC.on_mc(self.ged_template, frame)
                self.MC.c_onmc += 1
                print('processed ', self.MC.c_onmc)
                t1 = time.time()
                print('MC time: ', t1-t0)

            #print('1:',1/(time.time() - S))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.frameG.emit(gray)

            tmp_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.data_lock.lock()
            self.frame = tmp_frame
            height, width, dim = self.frame.shape
            bytesPerLine = dim * width
            image = QtGui.QImage(self.frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
            self.data_lock.unlock()
            self.frameI.emit(image)


            dis = time.time() - ptime
            # print(f'online player frame {self.total_frame} start at {S}')
            # print('frame duration: ', dis)
            if self.fakecapture:
                st = 1/30 - dis - 0.005
                if st > 0:
                    time.sleep(st)
                    print('delayed: ', st)
            else:
                self.fps_delay(dis)
            et = time.time()
            count += 1
            print('current fps: ', 1/(et-ptime))
            #print('avg fps: ', count/(et-tt))
            print('recent 100 fps: ', len(timelist)/(et-timelist[0]))
            timelist.append(et)
            if len(timelist) > 100:
                timelist.pop(0)
            ptime = et



        capture.release() ##

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

    def cal_FPS(self, dur):
        fps = round(1 / dur, 3)
        self.fpsChanged.emit(fps)

    def calculate_FPS(self, cap: cv2.VideoCapture):  ## cap 할 때..
        count_to_read = 10
        timer = QtCore.QElapsedTimer()  ##QtCore.QTimer
        timer.start()
        for i in range(count_to_read):
            ret, frame = cap.read()
        elapsed_ms = timer.elapsed()
        self.fps = count_to_read / (elapsed_ms / 1000.0)
        self.fps_calculating = False
        self.fpsChanged.emit(self.fps)  ## signal 방출

    def get_fps(self, cap: cv2.VideoCapture):
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.fpsChanged.emit(self.fps)

    def fps_delay(self, dis):
        if self.loop_time - 0.005 > dis:
            time.sleep(self.loop_time-dis - 0.005)

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
