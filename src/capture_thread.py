from enum import Enum, auto  ## enum
import datetime

from PySide2 import QtCore
from PySide2 import QtGui
import cv2
import numpy as np

import time


class VideoSavingStatus(Enum):
    STARTING = auto()
    STARTED = auto()
    STOPPING = auto()
    STOPPED = auto()


class CaptureThread(QtCore.QThread):
    frameCaptured = QtCore.Signal(QtGui.QImage)  ## data?- signal from Qimage
    print("frameCaptured:", frameCaptured)
    fpsChanged = QtCore.Signal(float)
    print("fpsChanged:", fpsChanged)
    videoSaved = QtCore.Signal(str)  ## difference
    print("videoSaved:", videoSaved)

    ## qmutex multithread - sharing one various (mutual exclusion)/
    ## hwabt par처리
    def __init__(self, camera: int, video_path: str, lock: QtCore.QMutex, parent: QtCore.QObject, user_path: bool,
                 f_type: str, pj_name: str, scopei: bool):  ## type hint
        super().__init__(parent=parent)  ### -?-
        self.camera_ID = camera
        self.user_path = user_path
        self.video_path = video_path
        self.data_lock = lock
        self.fps_calculating = False  ### False 상태
        self.fps = 0.0  ## 0.0 40
        self.cfps = 20.0  ##control
        self.sfps = 0.0  ##stastus
        self.frame_width = 0
        self.frame_height = 0
        self.video_saving_status = VideoSavingStatus.STOPPED
        self.saved_video_name = ''
        self.video_writer = None
        self.save_one_screen_shot = False
        self.save_format = f_type
        self.project_dir = pj_name
        self.video_file = str  ## function get 으로 변경

        self.scopei = scopei
        self.fser = True

        ## camera control  ## get from .. slider? | disable (value)
        self.exposure_status = 0  ##

        self.gain_status = 16  ##
        self.hue_status = 0
        self.tfps = 0
        self.focus_status = 0

        self.fakecapture = False

    def run(self):
        cap = cv2.VideoCapture(self.camera_ID, cv2.CAP_DSHOW)
        if self.fakecapture:
            #cap = cv2.VideoCapture("C:\\Users\\ZJLAB\\Downloads\\Video\\msCam4.avi")
            if self.camera_ID == 701:
                cap = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\\msCam1.avi")
            else:
                cap = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\\msCam1.avi")

        self.frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))


        ##
        # self.exposure = int(cap.get(cv2.CAP_PROP_BRIGHTNESS)) ##exposure ##선?
        self.exposure = int(cap.get(cv2.CAP_PROP_EXPOSURE))  ##
        print("self exposure status: ", self.exposure_status)

        cap.set(cv2.CAP_PROP_GAIN, self.gain_status)  ##
        if self.scopei:  ## self.camera_ID == cv2.CAP_DSHOW + 0:
            cap.set(cv2.CAP_PROP_SATURATION, 0X03)  ##

        self.s_gain = int(cap.get(cv2.CAP_PROP_GAIN))
        # self.hue_value = cap.get(cv2.CAP_PROP_HUE)
        self.hue_value = 0
        self.s_focus = cap.get(cv2.CAP_PROP_FOCUS)

        self.ftime = 0  ###
        self.count_frames = 0
        ## frame drop ##

        ## self.get_fps(cap)
        ## fpser = QtCore.QTimer()
        ## fpser.setTimerType(QtCore.Qt.PreciseTimer)
        ## fpser.timeout.connect(self.set_fps)

        ptime = 0
        while not self.isInterruptionRequested():  ## 기능나누기|같이쓰기. scope behavier
            ## self.fser = True
            ## fpser.setInterval(10)
            ## fpser.start()

            ret, tmp_frame = cap.read()
            if not ret:
                if self.fakecapture:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break
            if self.video_saving_status == VideoSavingStatus.STARTING:
                self.start_saving_video(tmp_frame)
            if self.video_saving_status == VideoSavingStatus.STARTED:
                self.video_writer.write(tmp_frame)
                self.timestamp_file.write(str(time.time())+'\n')
                self.count_frames = self.count_frames + 1
            if self.video_saving_status == VideoSavingStatus.STOPPING:
                self.stop_saving_video()
            if self.save_one_screen_shot:
                self.save_screen_shot(tmp_frame)
                self.save_one_screen_shot = False

            ##
            if self.exposure_status != self.exposure:  ## > change to bool type?
                # print("before input t E: ", self.exposure)
                # self.exposure = cap.get(cv2.CAP_PROP_BRIGHTNESS)
                self.exposure = cap.get(cv2.CAP_PROP_EXPOSURE)
                print("pre-set,real:", self.exposure_status, self.exposure)
                # self.exposure_status == self.exposure
                self.exposure = self.exposure_status
                print("set,real:", self.exposure_status, self.exposure)
                self.change_exposure(cap, self.exposure_status)  ##
                # print(cap.get(cv2.CAP_PROP_BRIGHTNESS))
                print(cap.get(cv2.CAP_PROP_EXPOSURE))
            if self.gain_status != self.s_gain:
                print("B gain:", self.s_gain)  # -1
                self.s_gain = int(cap.get(cv2.CAP_PROP_GAIN))
                print("B gainS:", self.gain_status)  # 20
                self.s_gain = self.gain_status
                print("gain status:", self.gain_status)  # -1
                self.change_gain(cap, self.gain_status)
                print("get", cap.get(cv2.CAP_PROP_GAIN))
            if self.hue_value != self.hue_status:
                outV = self.change_led(cap, self.hue_value)  #
                cap.set(cv2.CAP_PROP_HUE, (outV >> 4) & 0x00FF)  #
                print("LED(v/s/h): ", self.hue_value, self.hue_status, cap.get(cv2.CAP_PROP_HUE))  ##
                self.hue_status = self.hue_value

            if self.focus_status != self.s_focus:
                self.s_focus = self.focus_status
                self.change_focus(cap, self.s_focus)
                print("Focus:", cap.get(cv2.CAP_PROP_FOCUS))

            if self.cfps != self.sfps:
                self.sfps = self.cfps
                self.fps_switch(cap, self.sfps)
                cap.set(cv2.CAP_PROP_FPS, self.sfps)
                print('sfps:', self.sfps)

                #cap.set(cv2.CAP_PROP_FPS, self.sfps)
                print(f'fps changed: {self.sfps}')

            tmp_frame = cv2.cvtColor(tmp_frame, cv2.COLOR_BGR2RGB)
            self.data_lock.lock()
            self.frame = tmp_frame
            height, width, dim = self.frame.shape
            bytesPerLine = dim * width
            image = QtGui.QImage(self.frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)  ##24bit rgb
            self.data_lock.unlock()
            self.frameCaptured.emit(image)


            delay = float(f'{(1/self.cfps) - (time.time() - ptime) -0.005 :.2f}')
            if delay > 0:
                time.sleep(delay)

            time.time()
            ttime = time.time()
            fps = round(1 / (ttime - ptime), 3)

            self.fpsChanged.emit(fps)
            ptime = ttime


        cap.release()

    def stop(self):  ###
        print("Capture Thread Stopped")
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

    def start_saving_video(self, first_frame):
        now = datetime.datetime.now()
        self.saved_video_name = now.strftime("%Y-%m-%d+%H-%M-%S")  ## %H:%M:%S") ## 멈춤 실패시 방지책 마련

        if self.user_path == False:
            user_movie_path = QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.MoviesLocation)[0]  ##
            movie_dir = QtCore.QDir(user_movie_path)  ##
        else:
            movie_dir = QtCore.QDir(self.video_path)  ##

        movie_dir.mkpath(self.project_dir)
        movie_dir = movie_dir.absoluteFilePath(self.project_dir)  ##  +data 이용하기
        print("movie_dir: ", movie_dir)

        cover = f'{movie_dir}/{self.saved_video_name}_cover{self.camera_ID}.jpg'
        cv2.imwrite(cover, first_frame)

        fn = f'{movie_dir}/{self.saved_video_name}_timestamp.jpg'
        self.timestamp_file = open(fn, 'w')


        self.fps = self.sfps
        # print(self.frame_width, self.frame_heigh

        if self.save_format == '.wmv':
            self.video_file = f'{movie_dir}/{self.saved_video_name}_{self.camera_ID}.wmv'
            self.video_writer = cv2.VideoWriter(
                self.video_file,
                cv2.VideoWriter_fourcc('W', 'M', 'V', '2'),  ## check
                self.fps if self.fps > 0 else 30,
                (self.frame_width, self.frame_height),
                True)
            self.video_saving_status = VideoSavingStatus.STARTED

        elif self.save_format == '.Mp4':  ## mp4로 수정 필요 ## check 필요 ## 특허주의
            ## OpenCV: FFMPEG: tag 0x44495658/'XVID' is not supported with codec id 12 and format 'mp4 / MP4 (MPEG-4 Part 14)'
            ## OpenCV: FFMPEG: fallback to use tag 0x7634706d/'mp4v'
            self.video_file = f'{movie_dir}/{self.saved_video_name}_{self.camera_ID}.mp4'
            self.video_writer = cv2.VideoWriter(
                self.video_file,
                ## cv2.VideoWriter_fourcc('M', 'P', '4', 'V'),  ## GNU gpl XVID to MP4V
                ## cv2.VideoWriter_fourcc(*'mpeg'),
                cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                self.fps if self.fps > 0 else 30,
                (self.frame_width, self.frame_height),
                True)
            self.video_saving_status = VideoSavingStatus.STARTED

        elif self.save_format == '.tiff':  ## check 필요
            ## OpenCV: FFMPEG: tag 0x66666974/'tiff' is not supported with codec id 96 and format 'image2 / image2 sequence'
            ## [image2 @ 0x7f2cf02f1f00] Could not get frame filename number 2 from pattern '/home/e08/Videos/rbmi/2020-09-15+16:23:35.tiff'. Use '-frames:v 1' for a single image, 
            ## or '-update' option, or use a pattern such as %03d within the filename.
            self.video_file = f'{movie_dir}/{self.saved_video_name}_{self.camera_ID}.tiff'
            self.video_writer = cv2.VideoWriter(
                self.video_file,
                cv2.VideoWriter_fourcc('t', 'i', 'f', 'f'),  ##
                self.fps if self.fps > 0 else 30,
                (self.frame_width, self.frame_height),
                True)
            self.video_saving_status = VideoSavingStatus.STARTED

        else:  ## self.save_format == '.avi':
            self.video_file = f'{movie_dir}/{self.saved_video_name}_{self.camera_ID}.avi'
            self.video_writer = cv2.VideoWriter(
                self.video_file,
                cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                self.fps if self.fps > 0 else 30,

                (self.frame_width, self.frame_height),
                True)
            self.video_saving_status = VideoSavingStatus.STARTED

    def stop_saving_video(self):
        self.video_saving_status = VideoSavingStatus.STOPPED
        self.video_writer.release()
        del self.video_writer
        self.video_writer = None
        self.timestamp_file.close()
        del self.timestamp_file
        self.videoSaved.emit(self.saved_video_name)  ## 에러조심

    ## x
    def save_screen_shot(self, frame):
        now = datetime.datetime.now()
        self.saved_video_name = now.strftime("%Y-%m-%d+%H-%M-%S")  ##%H:%M:%S
        if self.user_path == False:
            user_movie_path = QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.MoviesLocation)[0]
            movie_dir = QtCore.QDir(user_movie_path)
        else:
            movie_dir = self.video_path
        movie_dir.mkpath('rbmi')  ##
        movie_dir = movie_dir.absoluteFilePath('rbmi')  ##

        cover = f'{movie_dir}/{self.saved_video_name}_screenshot.jpg'
        cv2.imwrite(cover, frame)

    ##
    def change_exposure(self, cap: cv2.VideoCapture, exp_value):
        # cap.set(cv2.CAP_PROP_BRIGHTNESS, exp_value)  ## exposure
        # exp_value = exp_value/255*100
        # exp_value = exp_value / 64 * 10 - 10
        exp_value = exp_value / 64 * 255
        # cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, exp_value)
        cap.set(cv2.CAP_PROP_EXPOSURE, exp_value)
        print('changed exposure: ', cap.get(cv2.CAP_PROP_EXPOSURE))
        # print(cap.get(cv2.CAP_PROP_BRIGHTNESS))
        # print("change", cap.get(cv2.CAP_PROP_EXPOSURE))
        # print("self exposure status2: ",self.exposure_status)
        # print("self exposure2: ", self.exposure)
        # print("exp value", exp_value)

        # -1 status?
        # not changed

    def change_gain(self, cap: cv2.VideoCapture, ga_value):
        if ga_value >= 32 and (ga_value % 2) == 1:
            ga_value += 1
        cap.set(cv2.CAP_PROP_GAIN, ga_value)

    def change_led(self, cap: cv2.VideoCapture, l_value):
        outV = np.uint16(l_value * (0x0FFF) / 1000) | (0x3000)
        print(outV)
        return outV
        # cap.set(cv2.CAP_PROP_HUE,(outV>>4)&0x00FF)
        # print(outV)

        # outV = np.uint16(v*(0x0FFF)/1000))|(0x3000)

    def change_focus(self, cap: cv2.VideoCapture, focus):
        print('change focus:', focus)
        cap.set(cv2.CAP_PROP_FOCUS, focus)
