from enum import Enum, auto ## enum
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
    frameCaptured = QtCore.Signal(QtGui.QImage)
    print("frameCaptured:", frameCaptured)
    fpsChanged = QtCore.Signal(float)
    print("fpsChanged:", fpsChanged)
    videoSaved = QtCore.Signal(str) 
    print("videoSaved:", videoSaved)

    def __init__(self, camera: int, camera_type: str, camera_size, lock: QtCore.QMutex, parent: QtCore.QObject, 
                        user_path: str, file_type: str, pj_name: str, os_type: int, init_fps=30.0, drop_f=None):
        super().__init__(parent=parent) 

        self.camera_ID = camera
        self.camera_idf = [cv2.CAP_DSHOW, cv2.CAP_V4L][os_type]
        self.camera_type = camera_type # 'B', 'S'
        self.camera_size = camera_size
        self.data_lock = lock
        self.user_path = user_path # + cam_type, self.base_path
        
        self.video_path = '' ## get video path from ... os || home tab

        self.project_dir = pj_name
        self.save_format = file_type
        
        self.video_saving_status = VideoSavingStatus.STOPPED
        self.save_one_screen_shot = False
        
        self.exposure_status = 50 ##
        self.gain_status = 16 ##
        self.led_status = 0

        self.exposure_control_value = self.exposure_status
        self.gain_control_value = self.gain_status
        self.led_control_value = self.led_status

        #self.tfps = 0
        
        self.fps = 20.0 ## 0.0 40
        self.fps_calculating = False ### False 상태
        self.fps_control_value = init_fps ##control ##30.0
        self.status_fps = 0.0 ##stastus

        self.drop_frame_image = drop_f

        self.fakeCapture = True

    def run(self):
            cap = cv2.VideoCapture(self.camera_ID, self.camera_idf)
            if self.fakeCapture:
                if self.camera_ID == 1:
                    cap = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\\behavior.avi")
                else:
                    cap = cv2.VideoCapture("C:\\Users\ZJLAB\caiman_data\example_movies\\msCam1.avi")
            self.camera_setting(cap=cap, c=self.camera_type)

            self.frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if self.camera_type == 'S':
                if self.camera_size is not None:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.camera_size[0])
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_size[1])
            
            #self.exposure = int(cap.get(cv2.CAP_PROP_EXPOSURE)) ##
            self.exposure_status = int(cap.get(cv2.CAP_PROP_BRIGHTNESS))
            #self.s_gain 
            ## self.gain_status = int(cap.get(cv2.CAP_PROP_GAIN))
        
        ## initialize 
            ## LED value
            ## self.hue_value = cap.get(cv2.CAP_PROP_HUE)
            self.led_status = cap.get(cv2.CAP_PROP_HUE)
            print('led_status: ', self.led_status)
            self.led_value = 0 ###
            
            self.count_frames = 0

            self.fps = cap.get(cv2.CAP_PROP_FPS)
            print('fps: ', self.fps)
            prev_time = 0
            droppedframes = 0
            while not self.isInterruptionRequested(): ## 기능나누기|같이쓰기. scope behavier
                ## self.fser = True
                ## fpser.setInterval(10)
                ## fpser.start()
                ptime = time.time()
                ret, tmp_frame = cap.read()
                #status = cap.grab()
                #if status == False:
                    ## something buffer, queryperformancecounter
                    ## https://stackoverflow.com/questions/38461335/python-2-x-queryperformancecounter-on-windows
                #    continue
                #status = cap.retrieve()



                if not ret:
                    if self.fakeCapture:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    print('------- ret break -------')
                    droppedframes += 10

                    #break
                else:
                    if self.video_saving_status == VideoSavingStatus.STARTING:
                        self.start_saving_video(tmp_frame)
                    if self.video_saving_status == VideoSavingStatus.STARTED:
                        self.video_writer.write(tmp_frame)
                        self.count_frames = self.count_frames + 1
                    if self.video_saving_status == VideoSavingStatus.STOPPING:
                        self.stop_saving_video()
                    if self.save_one_screen_shot:
                        self.save_screen_shot(tmp_frame)
                        self.save_one_screen_shot = False

                ## Exposure control
                if self.exposure_status != self.exposure_control_value:
                    coutV = self.change_exposure(cap, self.exposure_control_value)
                    print('exposure_control_value: ', coutV) #check
                    #self.exposure_control_value = cap.get(cv2.CAP_PROP_BRIGHTNESS) #check
                ##    print('exposure_controlled_value: ', self.exposure_control_value) #check
                    self.exposure_status = coutV

                ## Gain control
                if self.gain_status != self.gain_control_value:
                    coutV = self.change_gain(cap, self.gain_control_value)
                    print('gain_control_value: ', coutV) #check
                    self.gain_status = coutV
                ##    print('gain_controled_value: ', self.gain_control_value) #check

                ## LED control
                if self.led_status != self.led_control_value:
                    coutV = self.change_led(cap, self.led_control_value)
                    print('led_control_value: ', coutV) #check
                    ## self.led_control_value = cap.get(cv2.CAP_PROP_HUE)
                    self.led_status = coutV


                    ## self.ftime = time.time() - ttime
                    ## tfps = round(1/self.ftime,3)
                    ## print(f'{self.camera_ID}: {tfps}')

                if self.camera_type == 'S' and self.fps != self.fps_control_value:
                ##if self.fps != self.fps_control_value:
                    coutV = self.fps_switch(cap, self.fps_control_value) ## set fps
                    print('fps:', coutV)
                    self.fps = coutV

                        ## self.get_prop(cap) #####

                        #cap.set(cv2.CAP_PROP_FPS, self.sfps)
                        #print('fps changed: {self.fps}')


                if droppedframes > 0:
                    tmp_frame = self.drop_frame_image

                # print('tmp_frame: ', tmp_frame)

                tmp_frame = cv2.cvtColor(tmp_frame, cv2.COLOR_BGR2RGB)
                self.data_lock.lock()
                self.frame = tmp_frame
                height, width, dim = self.frame.shape
                bytesPerLine = dim * width
                image = QtGui.QImage(self.frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888) ##24bit rgb

                self.data_lock.unlock()
                self.frameCaptured.emit(image)


                ## if self.fps_calculating:  ####
                ##    self.calculate_FPS(cap)


                ## self.fps = cap.get(cv2.CAP_PROP_FPS)
                ## if self.fps != :
                ##     self.fps = lfps
                ##    cap.set(cv2.CAP_PROP_FPS)

                ## (1/self.sfps)

                ## while(self.fser):
                    ##pass

                delay = float(f'{(1/self.fps) - (time.time() - ptime) -0.005 :.2f}')
                if delay > 0:
                    time.sleep(delay)
                    #self.sleep(1000*delay)

                ## para or h ordr

                # if self.sfps != round(fps):

                ## cfps
                #self.cal_FPS(ttime - ptime)

                pres_time = time.time()
                fps = round(1/( 1000 if pres_time == prev_time else pres_time - prev_time),3)
                print(fps)
                prev_time = pres_time

                if droppedframes >= 10:
                    print('---reset---')
                    cap.release()
                    cap = cv2.VideoCapture(self.camera_ID, self.camera_idf)
                    droppedframes = 0
                    #self.fpsChanged.emit(droppedframes)
                    #continue
                    fps = droppedframes

                self.fpsChanged.emit(fps)


                ## if self.fps_control:
                ## #    cap.get(cv2.CAP_PROP_FPS)
                ##    cap.set(cv2.CAP_PROP_FPS, )


                # print('fps: ', fps)
                if fps <= 1 or self.fps/2 > fps: ## camera sep?
                    droppedframes += 1
                else:
                    droppedframes = 0

                if self.fakeCapture:
                    droppedframes = 0

            cap.release()

    def camera_setting(self, cap, c):
        if c == 'S':
            cap.set(cv2.CAP_PROP_SATURATION, 0x03) ##
            self.fps_cons_dict = {  20:0x14, 
                                    30:0x15, 
                                    60:0x16, 
                                    15:0x13, 
                                    10:0x12, 
                                    5:0x11  }
        elif c == 'B':
            pass

    def stop(self): ###
        print("Capture Thread Stopped")
        self.requestInterruption()
        self.wait()


    def fps_switch(self, cap:cv2.VideoCapture, n:int):
        fps_cons = self.fps_cons_dict.get(n, 0x14)
        cap.set(cv2.CAP_PROP_SATURATION, fps_cons)
        ##cap.set(cv2.CAP_PROP_FPS, fps_cons)
        print(f'changed fps value: {n}')
        return n

    def set_fps(self):
            self.fser=False
            print("kick")

    def cal_FPS(self, dur):
        fps = round(1/dur,3)
        self.fpsChanged.emit(fps)

    def calculate_FPS(self, cap: cv2.VideoCapture): ## cap 할 때..
        count_to_read = 10
        timer = QtCore.QElapsedTimer() ##QtCore.QTimer
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
        self.saved_video_name = now.strftime("%Y-%m-%d+%H-%M-%S") ## %H:%M:%S") ## 멈춤 실패시 방지책 마련

        if self.user_path == False:
            user_movie_path = QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.MoviesLocation)[0] ##
            movie_dir = QtCore.QDir(user_movie_path) ##
        else: movie_dir = QtCore.QDir(self.user_path)#video_path) ##

        ## if there is no definition of project folder name 
        ## use local dates
        if not self.project_dir:
            t = time.localtime()
            self.project_dir = f'{t.tm_year}_{t.tm_mon}_{t.tm_mday}'

        movie_dir.mkpath(self.project_dir)
        movie_dir = movie_dir.absoluteFilePath(self.project_dir) ##  +data 이용하기
        print("movie_dir: ", movie_dir)
        
        cover = f'{movie_dir}/{self.saved_video_name}_cover{self.camera_ID}.jpg'
        cv2.imwrite(cover, first_frame)

        #self.fps = self.sfps
        # print(self.frame_width, self.frame_heigh

        if self.save_format == '.wmv':
            self.video_file = f'{movie_dir}/{self.saved_video_name}_{self.camera_ID}.wmv'
            self.video_writer = cv2.VideoWriter(
                self.video_file,
                cv2.VideoWriter_fourcc('W', 'M', 'V', '2'), ## check
                self.fps if self.fps > 0 else 30,
                (self.frame_width, self.frame_height),
                True)
            self.video_saving_status = VideoSavingStatus.STARTED
    
        elif self.save_format == '.mp4': ## mp4로 수정 필요 ## check 필요 ## 특허주의
            ## OpenCV: FFMPEG: tag 0x44495658/'XVID' is not supported with codec id 12 and format 'mp4 / MP4 (MPEG-4 Part 14)'
            ## OpenCV: FFMPEG: fallback to use tag 0x7634706d/'mp4v'
            self.video_file = f'{movie_dir}/{self.saved_video_name}_{self.camera_ID}.mp4'
            self.video_writer = cv2.VideoWriter(
                self.video_file,
                ## cv2.VideoWriter_fourcc('M', 'P', '4', 'V'),  ## GNU gpl XVID to MP4V
                ## cv2.VideoWriter_fourcc(*'mpeg'),
                cv2.VideoWriter_fourcc('M','J','P','G'),
                self.fps if self.fps > 0 else 30,
                (self.frame_width, self.frame_height),
                True)
            self.video_saving_status = VideoSavingStatus.STARTED

        elif self.save_format == '.tiff': ## check 필요
            ## OpenCV: FFMPEG: tag 0x66666974/'tiff' is not supported with codec id 96 and format 'image2 / image2 sequence'
            ## [image2 @ 0x7f2cf02f1f00] Could not get frame filename number 2 from pattern '/home/e08/Videos/rbmi/2020-09-15+16:23:35.tiff'. Use '-frames:v 1' for a single image, 
            ## or '-update' option, or use a pattern such as %03d within the filename.
            self.video_file = f'{movie_dir}/{self.saved_video_name}_{self.camera_ID}.tiff'
            self.video_writer = cv2.VideoWriter(
                self.video_file,
                cv2.VideoWriter_fourcc('t', 'i', 'f', 'f'), ##
                self.fps if self.fps > 0 else 30,
                (self.frame_width, self.frame_height),
                True)
            self.video_saving_status = VideoSavingStatus.STARTED

        else: ## self.save_format == '.avi':
            self.video_file = f'{movie_dir}/{self.saved_video_name}_{self.camera_ID}.avi'
            self.video_writer = cv2.VideoWriter(
                self.video_file,
                cv2.VideoWriter_fourcc('I', '4', '2', '0'), #('R', 'G', 'B', 'A'), #('D', 'I', 'B', ' '),  #('M', 'J', 'P', 'G'),
                self.fps if self.fps > 0 else 30,
                (self.frame_width, self.frame_height),
                True)
            self.video_saving_status = VideoSavingStatus.STARTED


    def stop_saving_video(self):
        self.video_saving_status = VideoSavingStatus.STOPPED
        #self.videoSaved.emit(self.video_file) #self.saved_video_name) ## 에러조심
        self.video_writer.release()
        del self.video_writer
        self.video_writer = None


## x
    def save_screen_shot(self, frame):
        now = datetime.datetime.now()
        self.saved_video_name = now.strftime("%Y-%m-%d+%H-%M-%S") ##%H:%M:%S
        if self.user_path == False:
            user_movie_path = QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.MoviesLocation)[0]
            movie_dir = QtCore.QDir(user_movie_path)
        else: movie_dir = QtCore.QDir(self.video_path)
        movie_dir.mkpath('rbmi') ##
        movie_dir = movie_dir.absoluteFilePath('rbmi') ##

        cover = f'{movie_dir}/{self.saved_video_name}_screenshot.jpg'
        cv2.imwrite(cover, frame)


    ##
    def change_exposure(self, cap: cv2.VideoCapture, exp_value):
        cap.set(cv2.CAP_PROP_BRIGHTNESS,exp_value) ## exposure
        #exp_value = exp_value/255*100
        #cap.set(cv2.CAP_PROP_EXPOSURE,exp_value)

        # print(cap.get(cv2.CAP_PROP_BRIGHTNESS))
        #print("change", cap.get(cv2.CAP_PROP_EXPOSURE))
        #print("self exposure status2: ",self.exposure_status)
        #print("self exposure2: ", self.exposure)
        #print("exp value", exp_value)

        # -1 status?
        # not changed
        return exp_value

    def change_gain(self, cap:cv2.VideoCapture, ga_value):
        if ga_value>=32 and (ga_value%2)==1:
            ga_value+=1
        cap.set(cv2.CAP_PROP_GAIN, ga_value)
        return ga_value

    def change_led(self, cap:cv2.VideoCapture, l_value):
        outV = np.uint16(l_value*(0x0FFF)/100)|(0x3000)
        cap.set(cv2.CAP_PROP_HUE,(outV>>4)&0x00FF)
        print("changed led value: ", outV)
        return l_value
        
        #print(outV)
        
        
        #outV = np.uint16(v*(0x0FFF)/1000))|(0x3000)    

    def get_prop(self, cap:cv2.VideoCapture):
        print('brightness: ', cap.get(cv2.CAP_PROP_BRIGHTNESS))
        print('gain: ', cap.get(cv2.CAP_PROP_GAIN))
        print('contrast: ', cap.get(cv2.CAP_PROP_CONTRAST))
        print('FPS: ', cap.get(cv2.CAP_PROP_FPS))
        print('saturation: ', cap.get(cv2.CAP_PROP_SATURATION))
        print('hue: ', cap.get(cv2.CAP_PROP_HUE))
        print('exposure: ', cap.get(cv2.CAP_PROP_EXPOSURE))
        

    