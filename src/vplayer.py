import cv2
from PySide2 import QtCore
from enum import Enum, auto
import numpy as np
import time

from PySide2 import QtGui


class VPlayerStatus(Enum):
    STARTING = auto()
    STARTED = auto()
    STOPPING = auto()
    STOPPED = auto()
    PAUSING = auto()
    #PAUSED = auto()
    MOVING = auto() ## pausing으로 처리?starting?
    #MOVED = auto()

class VPlayer(QtCore.QThread):

    frameC = QtCore.Signal(QtGui.QPixmap)
    stateCh = QtCore.Signal(int)

    def __init__(self, v_path: str, lock: QtCore.QMutex, parent: QtCore.QObject): #parent QtCore.QObject
        super().__init__(parent=parent)
        self.v_path = v_path
        self.total_frame = 0
        self.present_frame = 0
        self.move_frame = 0 ## ui 내에서 처리?
        self.start_frame = 0
        self.present_time = 0
        self.total_time = 0
        self.next_frame = 0 # buffer for interacting slider
        self.data_lock = lock
        self.fps = 0
        self.vplayer_status = VPlayerStatus.PAUSING
        self.ui = parent.ui
        self.capture = None
        self.frame_list = []
        self.load_mode = False
        # lock mul
        self.tlist = []
        self.speed = 1
        self.alpha = 0.99
        self.tlen = 30
        self.brightness = 0
        self.contrast = 1


    def datainit(self):
        t1 = time.time()
        if not self.load_mode:
            if self.v_path.__contains__('.tiff'):
                self.load_tiff()
            elif self.v_path.__contains__('.avi'):
                self.load_avi()
            else:
                self.load_avi() # pending for other file type

        try:
            self.wtime = 1 / self.fps
            print('waitT: ', self.wtime)

        except ZeroDivisionError:
            print("-- zero fps --")
            self.fps = self.capture.get(cv2.CAP_PROP_FPS)
            self.wtime = 1 / self.fps
            print('zero--fps: ', self.fps, self.wtime)  ###

        print('fps: ', self.fps)

        print('total_frame: ', self.total_frame)

        print('init time: ', time.time() - t1)

    def run(self):
        self.datainit()

        loop_time = time.perf_counter()
        while not self.isInterruptionRequested():
            ## show start
            ## image()_ first image

            if self.vplayer_status == VPlayerStatus.STARTING:
                st = time.perf_counter()

                if self.next_frame != 0:
                    # self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.next_frame)
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
                    #self.stateCh.emit(1)  ### signal - pause changed
                    #self.present_frame = self.start_frame

                self.present_frame += 1

                # process_time = time.time() - start_time
                process_time = time.perf_counter() - loop_time
                loop_time = time.perf_counter()
                if process_time < self.wtime:
                    # time.sleep(self.wtime - process_time)
                    self.usleep((self.wtime - process_time) * 1000000)

                self.tlist.append(loop_time)
                if len(self.tlist) == self.tlen:
                    avgf = self.tlen/(self.tlist[-1]-self.tlist[0])
                    print('avg fps:', self.tlen/(self.tlist[-1]-self.tlist[0]))
                    # target_fps = self.fps*self.speed
                    # if avgf > target_fps * 1.05:
                    #     self.wtime += self.wtime * (avgf/target_fps-1) * self.alpha
                    #     self.alpha *= 0.9
                    # elif avgf < target_fps * 0.95:
                    #     self.wtime -= self.wtime * (1-avgf/target_fps) * self.alpha
                    #     self.alpha *= 0.9
                    # else:
                    #     self.alpha *= 0.1
                    # print('self.wtime:', self.wtime)
                    self.tlist = []


            if self.vplayer_status == VPlayerStatus.PAUSING:
                self.frame_update()
                time.sleep(0.01)

            if self.vplayer_status == VPlayerStatus.STOPPING:
                self.p_stop()




    def playspeed(self, i):
        ll = [1, 2, 3, 5]
        self.speed = ll[i]
        self.wtime = 1/(self.fps * self.speed)
        self.alpha = 0.9
        self.tlist = []
        self.tlen = 30 * ll[i]
        if i == 2:
            self.wtime = 0.0127
        if i == 3:
            self.wtime = 0.00155
        # wt = [0.0166, 0.01, 0.0012, 0.0009]
        # self.wtime = wt[i]
        print(f'play speed change to {ll[i]}x')
        print('wtime:', self.wtime)


    def load_tiff(self):
        from hnccorr import Movie
        image_dir = "D:\\0_Project\\20211217_neurofinder\\neurofinder.00.00\\neurofinder.00.00\\images"
        num_images = 3024
        self.total_frame = num_images
        self.fps = 20
        self.total_time = self.total_frame / self.fps
        tmp = Movie.from_tiff_images("Example movie", image_dir, num_images, subsample=1)
        tmp = tmp._data
        d_max = np.max(tmp)
        self.frame_list = 255 / d_max * tmp
        self.frame_list = self.frame_list.astype(np.uint8)



    def load_avi(self):
        self.capture = cv2.VideoCapture(self.v_path)
        print('fileopen', self.v_path)
        self.total_frame = self.capture.get(cv2.CAP_PROP_FRAME_COUNT)
        self.fps = self.capture.get(cv2.CAP_PROP_FPS)
        self.total_time = self.total_frame / self.fps
        print('tf: ', self.total_frame)

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

    # def stop_from_list(self):
    #     self.present_frame = 0
    #     self.frameC.emit(self.image_list[self.present_frame])
    #     self.vplayer_status = VPlayerStatus.PAUSING

    def p_stop(self):
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.present_frame = self.start_frame
        self.frame_update()
        self.vplayer_status = VPlayerStatus.PAUSING
        ## self.total_frame = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        ## print("totalframe2: ", self.total_frame)
 #   def frame_off(self):
        ## stop


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
        if self.present_frame >= self.total_frame-1:
            self.present_frame = 0

        tmp_frame = self.frame_list[self.present_frame]

        tmp_frame = cv2.cvtColor(tmp_frame, cv2.COLOR_BGR2RGB)
        tmp_frame = cv2.convertScaleAbs(tmp_frame, alpha=self.contrast, beta=self.brightness)
        self.data_lock.lock()
        self.frame = tmp_frame
        height, width, dim = self.frame.shape
        #print('h,w,d: ', height, width, dim)
        bytesPerLine = dim * width
        image = QtGui.QImage(self.frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
        self.data_lock.unlock()
        self.frameC.emit(QtGui.QPixmap.fromImage(image))

        # timer update
        #self.slider_timer_update()

    def set_frame(self, index):
        self.present_frame = index

    def time_format(self, s):
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return ("%d:%02d:%02d" % (h, m, s)) if h else ("%d:%02d" % (m, s))

## path_ = "/HATA/hdocuments/BMI/bmi-gui/qt_python/rbmi-master/src/temptest/2020-09-22/msCam13.avi"
## capture = cv2.VideoCapture(path_)
## #fps = cv2.CAP_PROP_FPS
## #a = round(1000/fps)
## #print(a)
## 
## 
## 
## capture.open(path_)
## stop_frame = 200
## 
## capture.set(cv2.CAP_PROP_POS_FRAMES, stop_frame)
## a, frame=capture.read()
## while True:
## 
##     if cv2. waitKey(33) > 0: break
##     cv2.imshow('VideoFrame',frame) 
## 
## capture.release()
## cv2.destroyAllWindows()
