from enum import Enum, auto  ## enum
import datetime

from PySide2 import QtCore
from PySide2 import QtGui
import cv2
import numpy as np

import time

from cameraController import MiniscopeController, SimpleCameraController


class VideoSavingStatus(Enum):
    STARTING = auto()
    STARTED = auto()
    STOPPING = auto()
    STOPPED = auto()


class CaptureThread(QtCore.QThread):
    frameCaptured = QtCore.Signal(QtGui.QPixmap)  ## data?- signal from Qimage
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
        self.fps = 0  ## 0.0 40
        self.cfps = 20  ##control
        self.sfps = 0  ##stastus
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
        if scopei:
            self.controller = MiniscopeController('./configs/miniscopes.json')
        else:
            self.controller = SimpleCameraController()

        self.exposure_status = 0  ##
        self.gain_status = 1  ##
        self.led_status = 0
        self.focus_status = 0

        self.fakecapture = False

    def run(self):
        cap = cv2.VideoCapture(self.camera_ID + cv2.CAP_DSHOW)
        if self.fakecapture:
            #cap = cv2.VideoCapture("C:\\Users\\ZJLAB\\Downloads\\Video\\msCam4.avi")
            if self.camera_ID == 701:
                cap = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\\msCam1.avi")
            else:
                cap = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\\msCam1.avi")

        args = self.controller.init_args(cap)
        self.frame_width = args["width"]
        self.frame_height = args["height"]
        self.gain = self.gain_status = args["gain"]
        self.fps = args["fps"]
        self.focus = args["focus"]
        self.led = args["led"]
        self.exposure = self.exposure_status = args["exposure"]


        self.count_frames = 0
        ## frame drop ##

        ptime = 0
        while not self.isInterruptionRequested():  ## 기능나누기|같이쓰기. scope behavier
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

            if self.exposure != self.exposure_status:
                print(f'change exposure {self.exposure} -> {self.exposure_status}')
                self.exposure = self.exposure_status
                self.controller.change_exposure(cap, self.exposure)
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


            tmp_frame = cv2.cvtColor(tmp_frame, cv2.COLOR_BGR2RGB)
            self.data_lock.lock()
            self.frame = tmp_frame
            height, width, dim = self.frame.shape
            bytesPerLine = dim * width
            image = QtGui.QImage(self.frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)  ##24bit rgb
            self.data_lock.unlock()
            self.frameCaptured.emit(QtGui.QPixmap.fromImage(image))


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

