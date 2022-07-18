from registration_h import NCCProject, Preprocess, on_NCC
import cv2
import time

from PySide2.QtCore import Slot, Signal, QObject

class MCCs(QObject):
    signalPath = Signal(str)
    signalPrc = Signal(int)
    signalLen = Signal(int)

    signalPPe = Signal(int)

class MCC(MCCs):
    
    def __init__(self, path, parent:QObject):##
        super().__init__(parent=parent)
        self.open_video_path = path
        self.startX = time.time()
        self.c_onmc = 0
        self.on_ncc = None

        @Slot(int)
        def propp(n):
            self.signalPPe.emit(n)
        #self.on_pre=Preprocess(cam_num)
        self.on_pre=Preprocess(path)
        #self.on_pre.signalPP.connect(propp) ##emit 사전필요?
        self.on_pre.signalP.connect(propp)

    def g_temp(self, cam_num):
        S = time.time()
        ## 일단은.. ##init signal
        pretemp = self.on_pre.on_generate_temp() 
        print('online > g_temp time: ', time.time() - S)
        return pretemp

    def on_mc(self, on_temp, frame):

        if self.c_onmc == 0: ## future bgs / temp
            self.on_ncc = on_NCC(on_temp, frame)  ## cycleXX

        ## player frame
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        fixed_frame, template = self.on_ncc.NCC_framebyframe(frame)
        img = cv2.cvtColor(fixed_frame, cv2.COLOR_GRAY2BGR)

        ##image out
        return img, template




    def mc(self):
        path = self.open_video_path
        save_path = self.open_video_path.split('.')[0] + '_mcc.avi'   ## result .avi

        ## 위치수정
        video = cv2.VideoCapture(path)
        nums = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

        ## process
        self.signalLen.emit(nums)
        i=0
        self.signalPrc.emit(i)

        t= time.time()
        pre=Preprocess(path)
        self.signalPrc.emit(nums/20)
        pretemp = pre.generate_template()
        self.signalPrc.emit(nums/15) ##

        ncc = NCCProject(pretemp, path)
        self.signalPrc.emit(nums/10) ##

        tmpt = time.time() - t
        print('preparing time: ', tmpt)

        writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'DIVX'), 20, (752,480))
        ## np.empty([752,480,nums])
        t = time.time()

        ## time: 210.88 preparing, 1444.49 until saving, 1233.61
#        for i in range(nums):
#            ret, frame = video.read()
#            ## ret bool /ox?
#            t2 = time.time()
#            ft = t2 - t
#            fps = 'fps: ' + str(round(1/ft,2)) 
#            t = t2#
#            print(fps)
#
#            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
#            fixed_frame,_ = ncc.NCC_framebyframe(frame)
#            img = cv2.cvtColor(fixed_frame, cv2.COLOR_GRAY2BGR)
#            writer.write(img)
#            self.signalPrc.emit(i)


        # 0.8frame/s
        while video.isOpened():
            if i == nums:
                print('inumsequal')
                break
            
            ret, frame = video.read()
            t2 = time.time()
            ft = t2 - t
            fps = 'fps: ' + str(round(1/ft, 2))
            t = t2
            print(fps)

            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                fixed_frame, _template = ncc.NCC_framebyframe(frame)
                img = cv2.cvtColor(fixed_frame, cv2.COLOR_GRAY2BGR)
                writer.write(img)
                self.signalPrc.emit(i)
            i+=1
        #while video.isOpened():
        #    ret, frame = video.read()
        #    t2 = time.time()
        #    ft = t2 - t
        #    fps = 'fps: ' + str(round(1/ft,2)) 
        #    t = t2#

        #    if ret:
        #        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        #        fixed_frame, _template = ncc.NCC_framebyframe(frame)
        #        img = cv2.cvtColor(fixed_frame, cv2.COLOR_GRAY2BGR)
        #        writer.write(img)

        writer.release()
        video.release()
        print('until saving: ', time.time() - self.startX, 'tmplate: ',tmpt)
        self.signalPath.emit(save_path) 