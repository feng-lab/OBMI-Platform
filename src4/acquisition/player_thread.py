import cv2
from PySide2 import QtCore
from enum import Enum, auto
import time
from PySide2 import QtGui

class VPlayerStatus(Enum):
    STOPPED = auto()
    STARTED = auto()
    STARTING = auto()
    STOPPING = auto()
    PAUSING = auto()
    PAUSED = auto()

class VPlayer(QtCore.QThread):
    frameC = QtCore.Signal(QtGui.QImage)
    stopS = QtCore.Signal(bool)
    def __init__(self, user_path: str, lock: QtCore.QMutex, parent: QtCore.QObject):
        super().__init__(parent=parent)
        self.user_path = user_path
        self.vplayer_status = VPlayerStatus.STOPPED
        self.init_frame = 0
        self.data_lock = lock

        self.brightness = 0
        self.contrast = 0
        
        if type(self.user_path) == QtCore.QDir:
            self.user_path = self.user_path.path()

        self.capture = cv2.VideoCapture(self.user_path)
        print('vplayer capture: ', self.capture)
        self.total_frame = self.capture.get(cv2.CAP_PROP_FRAME_COUNT)
        self.fps = self.capture.get(cv2.CAP_PROP_FPS)
        print('vplayer total frame: ', self.total_frame)
        print('vplayer fps: ', self.fps)
    
    def run(self):
        capture = self.capture
        wtime = round(1/self.fps, 3)
        self.present_frame = self.init_frame
        #capture.set(cv2.CAP_PROP_POS_FRAMES, self.present_frame)
        #self.playing = False
        self.frame_counter = 0
        self.frame_moved = False
        while not self.isInterruptionRequested():
            t = time.time()
            ##brightness = self.brightness
            ##contrast = self.contrast
            #self.present_frame = capture.get(cv2.CAP_PROP_POS_FRAMES)
            if self.vplayer_status == VPlayerStatus.STARTING:
                print("player started")
                self.starting_frame = self.present_frame
                capture.set(cv2.CAP_PROP_POS_FRAMES, self.starting_frame)
                self.vplayer_status = VPlayerStatus.STARTED                
            if self.vplayer_status == VPlayerStatus.PAUSING:
                self.present_frame = self.frame_counter
                self.vplayer_status = VPlayerStatus.PAUSED
            if self.vplayer_status == VPlayerStatus.STOPPING:
                self.stop()                
            if self.frame_counter >= self.total_frame:
                #print('play finished')
                self.stop()
            if self.vplayer_status == VPlayerStatus.STARTED:
                print('started')
                ret, temp_frame = capture.read()
                tmp_frame = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB)
                self.data_lock.lock()
                self.frame_counter = capture.get(cv2.CAP_PROP_POS_FRAMES)
                #self.present_sec = capture.get(cv2.CAP_PROP_POS_MSEC) ###
                tmp_frame = self.brightness_contrast_control(tmp_frame, self.brightness, self.contrast)
                frame = tmp_frame
                height, width, dim = frame.shape
                bytesPerLine = dim * width
                image = QtGui.QImage(frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
                self.data_lock.unlock()
                self.frameC.emit(image)    
                count_sec = wtime - (time.time() - t)
                if count_sec >= 0:
                    time.sleep(count_sec) ## or qtimer
            
            if self.frame_moved: ## moving
                ## self.present_frame <- value from mainwindow
                capture.set(cv2.CAP_PROP_POS_FRAMES, self.present_frame)
                self.frame_moved = False
            
            #    capture.set(cv2.CAP_PROP_POS_MSEC, self.starting_msec) ## maybe need to change to frame
            #    print('setvalue: ', self.starting_msec)
            #    self.frame_moved = False


    def stop(self):
        self.frame_counter = 0
        self.present_frame = 0
        self.vplayer_status = VPlayerStatus.STOPPED
        self.stopS.emit(True)

    def done(self):
        print("player stopped")
        self.requestInterruption()
        self.wait()

    ## bfris
    def brightness_contrast_control(self, frame, b=0, c=0):
        buf = frame
        if b != 0:
            b = b/100 * 255
            if b > 0:
                shadow = b
                highlight = 255
            else: 
                shadow = 0
                highlight = 255 + 255
            alpha_b = (highlight - shadow)/255
            gamma_b = shadow
            
            buf = cv2.addWeighted(frame, alpha_b,frame, 0, gamma_b)
        else:
            buf = frame.copy()
        
        if c != 0:
            c = c/100*255
            f = 131*(c + 127) / (127*(131-c))
            alpha_c = f
            gamma_c = 127*(1-f)

            buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)

        return buf

    