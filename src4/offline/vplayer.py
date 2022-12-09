import cv2
from PySide2 import QtGui
from PySide2.QtCore import Signal, QMutex, QObject, QThread
from enum import Enum, auto

import time

from PySide2.QtGui import QImage


class VPlayerStatus(Enum):
    STARTING = auto()
    STARTED = auto()
    STOPPING = auto()
    STOPPED = auto()
    PAUSING = auto()
    #PAUSED = auto()
    MOVING = auto() ## pausing으로 처리?starting?
    MOVED = auto()

class VPlayerThread(QThread):

    frameC = Signal(QImage)
    stateCh = Signal(int)

    def __init__(self, v_path: str, lock: QMutex, parent: QObject): #parent QObject
        super().__init__(parent=parent)
        self.v_path = v_path
        self.total_frame = 0
        self.total_length = 0
        self.present_frame = 0
        self.move_frame = 0 ## ui 내에서 처리?
        self.start_frame = 0
        self.data_lock = lock
        self.fps = 0
        self.vplayer_status = VPlayerStatus.STOPPED
        # lock mul

    def load_video(self):
        capture = cv2.VideoCapture(self.v_path)

    def run(self):
        ## thread run - player on
        capture = cv2.VideoCapture(self.v_path)
        
        print('fileopen', self.v_path)
        self.total_frame = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        self.total_length = capture.get(cv2.CAP_PROP_POS_MSEC)
        print('total frame: {self.total_frame}, total length: {self.total_length}')

        fps = capture.get(cv2.CAP_PROP_FPS)
        if self.fps != fps:
            self.fps = fps
            print(f'fps has been updated to {self.fps} according to the video')
        wtime = round(1/self.fps, 3)
        
        while not self.isInterruptionRequested():
            if self.vpalyer_status == VPlayerStatus.STOPPED:
                self.stateCh.emit(0) ## STOPPED to 0
            if self.vplayer_status == VPlayerStatus.STARTING:
                print("player start")
                ## set starting position
                capture.set(cv2.CAP_PROP_POS_FRAMES, self.present_frame)
                self.vplayer_status == VPlayerStatus.STARTED
            if self.vplayer_status == VPlayerStatus.STARTED:
                processing_start_time = time.time()
                ret, tmp_frame = capture.read()
                try:
                    if not ret:
                        self.present_frame = capture.get(cv2.CAP_PROP_POS_FRAMES) ## position - num?
                        print(f'present_frame: {self.present_frame}, counted_frame: {self.present_frame}')
                        raise Exception('video connection failed, check video connection')
                    else: 
                        temp_frame = cv2.cvtColor(tmp_frame, cv2.COLOR_BGR2RGB)
                        self.data_lock.lock()
                        self.frame = temp_frame
                        height, width, dim = self.frame.shape
                        bytesPerLine = dim * width
                        image = QImage(self.frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
                        self.data_lock.unlock()
                        self.frameC.emit(image)
                        ## frame count
                        self.present_frame += 1
                        print('frame: ', self.present_frame)
                        ## apply delay for FPS
                        processing_time = time.time() - processing_start_time
                        time.sleep(wtime - processing_time)
                except: break

            if self.vplayer_status == VPlayerStatus.STOPPING:
                self.present_frame = 0
                self.vplayer_status = VPlayerStatus.STOPPED
            
            if self.present_frame >= self.total_frame:
                print('End of the Video')
                self.vplayer_status = VPlayerStatus.STOPPING
                
            
            if self.vplayer_status == VPlayerStatus.MOVING: ## 필요없을지도 
                ## send image
                capture.set(cv2.CAP_PROP_POS_FRAMES, self.present_frame)
                ret, tmp_frame = capture.read()
                temp_frame = cv2.cvtColor(tmp_frame, cv2.COLOR_BGR2RGB)
                self.data_lock.lock()
                self.frame = temp_frame
                #height, width, dim * width
                image = QImage(self.frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
                self.data_Lock.unlock()
                self.frameC.emit(image)
                
                self.vplayer_status = VPlayerStatus.MOVED

            if self.vplayer_status == VPlayerStatus.PAUSING:
                    self.vplayer_status = VPlayerStatus.PAUSED
                    self.stateCh.emit(self.present_frame) ## frame count
                
        capture.release()

    def stop(self):
        print("Player Thread Stopped")
        self.requestInterruption()
        self.wait()

## current player version
class VPlayer(QThread):
    frameC = Signal(QtGui.QImage)
    stateCh = Signal(int)

    def __init__(self, v_path: str, lock: QMutex, parent: QObject):  # parent QtCore.QObject
        super().__init__(parent=parent)
        self.v_path = v_path
        self.total_frame = 0
        self.total_length = 0
        self.present_frame = 0
        self.move_frame = 0  ## ui 내에서 처리?
        self.start_frame = 0
        self.present_time = 0
        self.total_time = 0
        self.next_frame = 0  # buffer for interacting slider
        self.data_lock = lock
        self.fps = 0
        self.vplayer_status = VPlayerStatus.STOPPED
        self.ui = parent.ui
        self.capture = None
        self.frame_list = []
        self.load_project = False
        # lock mul

    def run(self):
        t1 = time.time()
        if not self.load_project:
            ## thread run - player on
            if self.v_path.__contains__('.avi'):
                self.load_avi()
            else:
                self.load_avi()  # pending for other file type

        try:
            wtime = round(1 / self.fps, 3)
            print('waitT: ', wtime)

        except ZeroDivisionError:
            print("-- zero fps --")
            self.fps = self.capture.get(cv2.CAP_PROP_FPS)
            wtime = round(1 / self.fps, 3)
            print('zero--fps: ', self.fps, wtime)  ###

        print('fps: ', self.fps)

        print('total_frame: ', self.total_frame)
        print('lenght: ', self.total_length)

        print('init time: ', time.time() - t1)
        while not self.isInterruptionRequested():
            ## show start
            ## image()_ first image

            if self.vplayer_status == VPlayerStatus.STARTING:
                start_time = time.time()

                if self.next_frame != 0:
                    self.present_frame = self.next_frame
                    self.next_frame = 0

                # update frame
                self.frame_update()

                #
                if self.present_frame == self.total_frame:
                    print('played all')
                    self.vplayer_status = VPlayerStatus.PAUSING
                    self.ui.pushButton_2.setText('play')
                    continue
                    # self.stateCh.emit(1)  ### signal - pause changed
                    # self.present_frame = self.start_frame

                self.present_frame += 1

                process_time = time.time() - start_time
                if process_time < wtime:
                    time.sleep(wtime - process_time)

            if self.vplayer_status == VPlayerStatus.PAUSING:
                time.sleep(0.01)

            if self.vplayer_status == VPlayerStatus.STOPPED:
                time.sleep(0.1)

            if self.vplayer_status == VPlayerStatus.STOPPING:
                self.p_stop()

        # self.capture.release()
        self.capture = None

        ### mainwindow 작업 --

    #   def frame_on(self, frame):
    ## frame 보내기
    ## remote

    # not used yet
    # def load_tiff(self):
    #     image_dir = "D:\\0_Project\\20211217_neurofinder\\neurofinder.00.00\\neurofinder.00.00\\images"
    #     num_images = 3024
    #     self.total_frame = num_images
    #     self.fps = 20
    #     self.total_length = self.total_frame
    #     self.total_time = self.total_frame / self.fps
    #     tmp = Movie.from_tiff_images("Example movie", image_dir, num_images, subsample=1)
    #     tmp = tmp._data
    #     d_max = np.max(tmp)
    #     self.frame_list = 255 / d_max * tmp
    #     self.frame_list = self.frame_list.astype(np.uint8)

    def load_avi(self):
        self.capture = cv2.VideoCapture(self.v_path)
        print('fileopen', self.v_path)
        self.total_frame = self.capture.get(cv2.CAP_PROP_FRAME_COUNT)
        self.total_length = self.capture.get(cv2.CAP_PROP_POS_MSEC)
        self.fps = self.capture.get(cv2.CAP_PROP_FPS)
        self.total_time = self.total_frame / self.fps
        print('tf, tl: ', self.total_frame, self.total_length)

        print("load start")
        timer = time.time()
        while True:
            ret, tmp_frame = self.capture.read()

            if not ret:
                break
            self.frame_list.append(tmp_frame)

        t = time.time() - timer
        print(f'load finished! Length: {len(self.frame_list)}, Total time: {t}')
        self.capture.release()

    def pause(self, p_frame: int):
        self.pause_frame = p_frame
        # self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.pause_frame)

    def p_stop(self):
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.present_frame = self.start_frame
        self.frame_update()
        self.vplayer_status = VPlayerStatus.PAUSING
        ## self.total_frame = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        ## print("totalframe2: ", self.total_frame)


    def stop(self):
        print("Player Thread Stopped")
        self.requestInterruption()
        self.wait()

    # slider time label
    # def slider_timer_update(self):
    #     self.present_time = self.total_time * self.present_frame/ self.total_frame
    #     timestr = "Time: " + str(round(self.present_time, 1)) + "/" + str(round(self.total_time, 1)) + "sec"
    #     self.ui.label_208.setText(timestr)
    #     timestr = self.time_format(int(self.present_time))
    #     self.ui.label_204.setText(timestr)

    # def frame_update(self):
    #     tmp_frame = self.frame_list[self.present_frame]
    #     self.data_lock.lock()
    #     self.frame = tmp_frame
    #     height, width = self.frame.shape
    #     bytesPerLine = width
    #     image = QtGui.QImage(self.frame, width, height, bytesPerLine, QtGui.QImage.Format_Grayscale8)
    #     self.data_lock.unlock()
    #     self.frameC.emit(image)

    def frame_update(self):
        tmp_frame = self.frame_list[self.present_frame]

        tmp_frame = cv2.cvtColor(tmp_frame, cv2.COLOR_BGR2RGB)
        self.data_lock.lock()
        self.frame = tmp_frame
        height, width, dim = self.frame.shape
        # print('h,w,d: ', height, width, dim)
        bytesPerLine = dim * width
        image = QtGui.QImage(self.frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
        self.data_lock.unlock()
        self.frameC.emit(image)

    def set_frame(self, index):
        self.present_frame = index

    def time_format(self, s):
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return ("%d:%02d:%02d" % (h, m, s)) if h else ("%d:%02d" % (m, s))