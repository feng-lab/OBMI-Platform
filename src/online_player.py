from enum import Enum, auto
from PySide2 import QtGui, QtCore
import cv2
import numpy as np
import queue

from PySide2.QtCore import QTimer, QObject, Qt

from mccc import MCC
import time
import torch

from src.cameraController import SimpleCameraController, MiniscopeController


class VideoSavingStatus(Enum):
    STARTING = auto()
    PAUSING = auto()
    STOPPING = auto()
    STOPPED = auto()

class OPlayer(QtCore.QThread):

    frameI = QtCore.Signal(QtGui.QPixmap)
    frameG = QtCore.Signal(list)
    fpsChanged = QtCore.Signal(float)
    roi_pos = QtCore.Signal(list)
    ## fImg = QtCore.Signal(np.ndarray)

    def __init__(self, camera: str,  ## temp
            lock: QtCore.QMutex, parent: QtCore.QObject, miniscope=False):
        super().__init__(parent=parent)
        self.data_lock = lock
        self.c_number = camera
        self.ged_template = None
        self.MC = None
        self.ROItable = parent.onroi_table
        self.parent = parent

        self.fps = 0
        self.cfps = 20
        self.sfps = 0
        self.loop_time = 0

        self.status = VideoSavingStatus.STARTING
        self.gain_status = 1  ##
        self.led_status = 0
        self.focus_status = 0
        self.buffer = []
        self.rtProcess = False
        self.cur_frame = 0
        self.total_frame = 0
        self.s_timer = 0

        if miniscope:
            self.controller = MiniscopeController('./configs/miniscopes.json')
        else:
            self.controller = SimpleCameraController()

        self.fakecapture = False
        self.file_save = False
        self.file_count = 1
        self.file_size = 5000

        self.isAutoROI = False
        self.autoROI = None

        self.cap_init()

        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.updates)
        self.timer.setTimerType(Qt.PreciseTimer)


        self.setPriority(QtCore.QThread.HighPriority)

        self.ptime = None
        self.timelist = []

        self.time_sum = 0
        self.mc_count = 0

    def cap_init(self):
        self.capture = cv2.VideoCapture(self.c_number + cv2.CAP_DSHOW)
        if self.fakecapture:
            # self.capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\Downloads\\Video\\demoMovie.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\demoMovie_out.avi")
            #self.capture = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\CaImAn_demo.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\msCam13_mcc.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\Desktop\\out_movie2.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\caiman_data\\example_movies\\msCam1.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\msCam1.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\demoMovie.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\CaImAn_demo.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\data_endoscope.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\\blood_vessel_10Hz.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\CaImAn_demo_out.avi")
            self.capture = cv2.VideoCapture("D:\\project\OBMI-Platform\\2_clip_mcc.avi")

        cap = self.capture

        args = self.controller.init_args(cap)
        self.width = args["width"]
        self.height = args["height"]
        self.gain = self.gain_status = args["gain"]
        self.fps = args["fps"]
        self.focus = args["focus"]
        self.led = args["led"]



    def setAutoROI(self, cm):
        self.autoROI = cm

    def updates(self):
        cap = self.capture
        st = time.time()
        ret, frame = cap.read()
        t1 = time.time()
        # print('frame start: ', st)
        # print('read:',t1-st)
        if not ret:
            if self.fakecapture:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
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

        if self.gain != self.gain_status:
            print(f'change gain {self.gain} -> {self.gain_status}')
            self.gain = self.gain_status
            self.controller.change_gain(cap, self.gain)
        if self.fps != self.cfps:
            print(f'change fps {self.fps} -> {self.cfps}')
            self.fps = self.cfps
            self.controller.change_fps(cap, self.fps)
        if self.focus != self.focus_status:
            print(f'change focus {self.focus} -> {self.focus_status}')
            self.focus = self.focus_status
            self.controller.change_focus(cap, self.focus)
        if self.led != self.led_status:
            print(f'change led {self.led} -> {self.led_status}')
            self.led = self.led_status
            self.controller.change_LED(cap, self.led)

        if type(self.ged_template) != type(None):
            t0 = time.time()
            # frame, _ = MCC(self.c_number, self).on_mc(self.ged_template, frame) ##,self.ged_template
            frame, _ = self.MC.on_mc(self.ged_template, frame)
            self.MC.c_onmc += 1
            # print('processed ', self.MC.c_onmc)
            t1 = time.time()
            # print('MC time: ', t1 - t0)
            self.time_sum += t1-t0
            self.mc_count += 1
            if self.mc_count % 900 == 0:
                print('MC process frame:', self.mc_count)
                print('MC current time:', t1-t0)
                print('MC average time:', self.time_sum/900)
                self.time_sum = 0


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
        self.frameI.emit(QtGui.QPixmap.fromImage(image))

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
        cap = cv2.VideoCapture(self.c_number, cv2.CAP_DSHOW)
        # capture = cv2.VideoCapture(self.c_number)
        if self.fakecapture:
            #capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\Downloads\\Video\\msCam4.avi")
            #capture = cv2.VideoCapture("C:\\Users\\ZJLAB\\Desktop\\out_movie.avi")
            cap = cv2.VideoCapture("C:\\Users\\ZJLAB\\caiman_data\\example_movies\\msCam1.avi")
            # self.capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\CaImAn_demo_out.avi")

        args = self.controller.init_args(cap)
        self.width = args["width"]
        self.height = args["height"]
        self.gain = self.gain_status = args["gain"]
        self.fps = args["fps"]
        self.focus = args["focus"]
        self.led = args["led"]

        tt = time.time()
        timelist= [tt]
        ptime = time.time()
        count = 0
        while not self.isInterruptionRequested():
            t0 = time.time()
            ret, frame = cap.read()
            t1 = time.time()
            print('read:', t1-t0)
            if not ret:
                if self.fakecapture:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break


            if self.rtProcess:
                if self.total_frame == 0:
                    self.s_timer = time.time()

                if self.status == VideoSavingStatus.STARTING:
                    self.cur_frame += 1
                self.total_frame += 1

            if self.gain != self.gain_status:
                print(f'change gain {self.gain} -> {self.gain_status}')
                self.gain = self.gain_status
                self.controller.change_gain(cap, self.gain)
            if self.fps != self.cfps:
                print(f'change fps {self.fps} -> {self.cfps}')
                self.fps = self.cfps
                self.controller.change_fps(cap, self.fps)
            if self.focus != self.focus_status:
                print(f'change focus {self.focus} -> {self.focus_status}')
                self.focus = self.focus_status
                self.controller.change_focus(cap, self.focus)
            if self.led != self.led_status:
                print(f'change led {self.led} -> {self.led_status}')
                self.led = self.led_status
                self.controller.change_LED(cap, self.led)

            if type(self.ged_template) != type(None):
                t0 = time.time()
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
            self.frameI.emit(QtGui.QPixmap.fromImage(image))


            dis = time.time() - ptime
            # print(f'online player frame {self.total_frame} start at {S}')
            print('frame duration: ', dis)
            if self.fakecapture:
                st = 1/30 - dis - 0.005
                if st > 0:
                    self.msleep(st*1000)
                    print('delayed: ', st)
                else:
                    self.msleep(1)
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



        cap.release() ##

    def stop(self):
        print('stopped - online')
        self.requestInterruption()
        self.wait()


    def fps_delay(self, dis):
        delay = self.loop_time - 0.005 - dis
        if delay > 0:
            self.msleep(delay*1000)

    def pause(self):
        self.status = VideoSavingStatus.PAUSING

    def play(self):
        self.status = VideoSavingStatus.STARTING

    @property
    def isPlaying(self):
        return self.status == VideoSavingStatus.STARTING
