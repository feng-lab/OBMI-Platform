import torch
import numpy as np
import cv2
from compute_offset import ApplyShifts
from LoadData import load_data as ld
from correlation_torch import NormXCorr2
import time
import os
import scipy.io as io

#test signal
from PySide2.QtCore import Slot, QObject, Signal
class sig(QObject):
    signalP = Signal(int)

class NCCProject():

    def __init__(self, template_frame, path):
        self.LOAD=ld(1)
        cap=cv2.VideoCapture(path)
        ret, raw_frame=cap.read()
        raw_frame=cv2.cvtColor(raw_frame, cv2.COLOR_RGB2GRAY)
        raw_frame=torch.tensor(raw_frame, dtype=torch.float32)
        self.template=torch.tensor(template_frame, dtype=torch.float32).cuda()
        self.kernel=torch.tensor(self.LOAD.generate_kernel((8,8)), dtype=torch.float32)#kernel尺寸可能后期要根据神经元大小调整
        self.sum1, self.a_rot_complex, self.b_complex, self.Zeros, self.theta, self.template_buffer = self.LOAD.SetParameters(
            raw_frame, self.kernel, CROP=False, use_gpu=True)
        self.kernel=self.kernel.cuda()
        self.ith=0


    def NCC_framebyframe(self, frame):
        #frame = torch.tensor(frame, dtype=torch.float32).cuda()
        frame = frame.astype(np.float32)
        frame = torch.from_numpy(frame)
        frame = frame.cuda()
        preprocess_frame = self.LOAD.filter_frame(frame, self.kernel)
        normxcorr2_general_output = NormXCorr2(self.template, preprocess_frame)
        output, _ = normxcorr2_general_output.normxcorr2_general(self.sum1, self.a_rot_complex, self.b_complex,
                                                                 self.Zeros)
        Shift = ApplyShifts(output)
        new_filtered_frame, _, _ = Shift.apply_shift(preprocess_frame, self.theta)
        new_raw_frame, _ , _ = Shift.apply_shift(frame, self.theta)

        new_filtered_frame = new_filtered_frame.squeeze(0)
        self.template_buffer[:, :, self.ith] = new_filtered_frame
        self.ith+=1
        if self.ith%200==0:
            mean_temp = torch.mean(self.template_buffer, dim=2)
            self.template = (self.template + mean_temp) / 2
            self.ith=0
        new_raw_frame = new_raw_frame.squeeze(0)
        new_raw_frame=new_raw_frame.cpu().numpy()

        return new_raw_frame.astype(np.uint8), self.template

class on_NCC(): #H

    def __init__(self, template_frame, init_frame):
        self.LOAD=ld(1)
        raw_frame=init_frame
        raw_frame=cv2.cvtColor(raw_frame, cv2.COLOR_RGB2GRAY) ## raw frame - R-G
        raw_frame=torch.tensor(raw_frame, dtype=torch.float32)
        self.template=torch.tensor(template_frame, dtype=torch.float32).cuda() ### template
        self.kernel=torch.tensor(self.LOAD.generate_kernel((8,8)), dtype=torch.float32)#kernel尺寸可能后期要根据神经元大小调整
        self.sum1, self.a_rot_complex, self.b_complex, self.Zeros, self.theta, self.template_buffer = self.LOAD.SetParameters(
            raw_frame, self.kernel, CROP=False, use_gpu=True)
        self.kernel=self.kernel.cuda()
        self.ith=0
        ## template,again?


    def NCC_framebyframe(self, frame):
        #frame = torch.tensor(frame, dtype=torch.float32).cuda()
        frame = frame.astype(np.float32)
        frame = torch.from_numpy(frame)
        frame = frame.cuda()
        preprocess_frame = self.LOAD.filter_frame(frame, self.kernel)
        normxcorr2_general_output = NormXCorr2(self.template, preprocess_frame)
        output, _ = normxcorr2_general_output.normxcorr2_general(self.sum1, self.a_rot_complex, self.b_complex,
                                                                 self.Zeros)
        Shift = ApplyShifts(output)
        new_filtered_frame, _, _ = Shift.apply_shift(preprocess_frame, self.theta)
        new_raw_frame, _ , _ = Shift.apply_shift(frame, self.theta)

        new_filtered_frame = new_filtered_frame.squeeze(0)
        self.template_buffer[:, :, self.ith] = new_filtered_frame
        self.ith+=1
        if self.ith%200==0:
            mean_temp = torch.mean(self.template_buffer, dim=2)
            self.template = (self.template + mean_temp) / 2
            self.ith=0
        new_raw_frame = new_raw_frame.squeeze(0)
        new_raw_frame=new_raw_frame.cpu().numpy()

        return new_raw_frame.astype(np.uint8), self.template

    def NCC_framebyframe_out_gpu(self, frame):
        frame = frame.astype(np.float32)
        frame = torch.from_numpy(frame)
        frame = frame.cuda()
        preprocess_frame = self.LOAD.filter_frame(frame, self.kernel)
        normxcorr2_general_output = NormXCorr2(self.template, preprocess_frame)
        output, _ = normxcorr2_general_output.normxcorr2_general(self.sum1, self.a_rot_complex, self.b_complex,
                                                                 self.Zeros)
        Shift = ApplyShifts(output)
        new_filtered_frame, _, _ = Shift.apply_shift(preprocess_frame, self.theta)
        new_raw_frame, _, _ = Shift.apply_shift(frame, self.theta)

        new_filtered_frame = new_filtered_frame.squeeze(0)
        self.template_buffer[:, :, self.ith] = new_filtered_frame
        self.ith += 1
        if self.ith % 200 == 0:
            mean_temp = torch.mean(self.template_buffer, dim=2)
            self.template = (self.template + mean_temp) / 2
            self.ith = 0
        new_raw_frame = new_raw_frame.squeeze(0)

        return new_raw_frame, self.template
class Preprocess(sig):
    def __init__(self, path):
        super().__init__()
        self.path=path
        #self.signalPP = self.signalP
        
    def get_video(self):
        print(self.path)
        cap=cv2.VideoCapture(self.path)
        nums=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video=np.empty((height, width, nums))
        i=0
        while(cap.isOpened() and i<nums):
            ret, frame=cap.read()
            frame=cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            video[:,:,i]=frame
            i+=1

        return video

    def generate_template(self):
        init_video=self.get_video()
        init_video = torch.tensor(init_video, dtype=torch.float32)
        LOAD=ld(1)
        # 1 first frame
        kernel=torch.tensor(LOAD.generate_kernel((8,8)), dtype=torch.float32)
        sum1, a_rot_complex, b_complex, Zeros, theta, _ = LOAD.SetParameters(
            init_video[:,:,0], kernel, CROP=False, use_gpu=True)

        init_video = init_video.cuda()
        kernel=kernel.cuda()
        # 1  first frame
        template = init_video[:, :, 0]
        preprocess_temp = LOAD.filter_frame(template, kernel)
        for i in range(200):

            frame = init_video[:, :, i % init_video.shape[2]]

            preprocess_frame = LOAD.filter_frame(frame, kernel)
            normxcorr2_general_output = NormXCorr2(preprocess_temp, preprocess_frame)
            output, _ = normxcorr2_general_output.normxcorr2_general(sum1, a_rot_complex, b_complex,
                                                                     Zeros)
            Shift = ApplyShifts(output)
            new_filtered_frame, _, _ = Shift.apply_shift(preprocess_frame, theta)
            new_filtered_frame = new_filtered_frame.squeeze(0)
            preprocess_temp = preprocess_temp * (i + 1) / (i + 2) + new_filtered_frame / (i + 2)

        preprocess_temp=preprocess_temp.cpu().numpy()

        return preprocess_temp

    def on_generate_temp(self):
        cap = cv2.VideoCapture(self.path)
        nums = 200
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video=np.empty((height, width, nums))

        i=0
        while(cap.isOpened() and i<nums): ## frame 받아와서 진행 ## frame 넘길때마다 하나씩?
            ret, frame=cap.read()
            frame=cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            # video[:,:,i]=frame
            if i == 0:
                ## video = torch.tensor(video, dtype=torch.float32)
                init_frame = torch.tensor(frame, dtype=torch.float32)
                #video[:,:,i] = frame
                #init_frame = video[:,:,i]

                LOAD=ld(1)
                # 1 first frame
                kernel=torch.tensor(LOAD.generate_kernel((8,8)), dtype=torch.float32)
                sum1, a_rot_complex, b_complex, Zeros, theta, _ = LOAD.SetParameters(
                    init_frame, kernel, CROP=False, use_gpu=True)

                #video = video.cuda()
                init_frame = init_frame.cuda()
                kernel=kernel.cuda()
                # 1  first frame
                template = init_frame
                #template = video[:,:,i]
                preprocess_temp = LOAD.filter_frame(template, kernel)

            ## init finish / next frame
            video[:,:,i] = frame ###
            preprocess_frame = LOAD.filter_frame(torch.tensor(video[:,:,i], dtype=torch.float32).cuda(), kernel)
            normxcorr2_general_output = NormXCorr2(preprocess_temp, preprocess_frame)
            output, _ = normxcorr2_general_output.normxcorr2_general(sum1, a_rot_complex, b_complex, 
                                                                    Zeros)
            Shift = ApplyShifts(output)
            new_filtered_frame, _, _ = Shift.apply_shift(preprocess_frame, theta)
            new_filtered_frame = new_filtered_frame.squeeze(0)
            preprocess_temp = preprocess_temp * (i + 1) / (i + 2) + new_filtered_frame / (i + 2)
            
            #self.signalPP.emit(i)
            self.signalP.emit(i)
            i+=1

        preprocess_temp=preprocess_temp.cpu().numpy()
        cap.release()
        return preprocess_temp

    def focus_generate_temp(self, cap):
        nums = 200
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video = np.empty((height, width, nums))

        i = 0
        while (cap.isOpened() and i < nums):
            ret, frame = cap.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            # video[:,:,i]=frame
            if i == 0:
                ## video = torch.tensor(video, dtype=torch.float32)
                init_frame = torch.tensor(frame, dtype=torch.float32)
                # video[:,:,i] = frame
                # init_frame = video[:,:,i]

                LOAD = ld(1)
                # 1 first frame
                kernel = torch.tensor(LOAD.generate_kernel((8, 8)), dtype=torch.float32)
                sum1, a_rot_complex, b_complex, Zeros, theta, _ = LOAD.SetParameters(
                    init_frame, kernel, CROP=False, use_gpu=True)

                # video = video.cuda()
                init_frame = init_frame.cuda()
                kernel = kernel.cuda()
                # 1  first frame
                template = init_frame
                # template = video[:,:,i]
                preprocess_temp = LOAD.filter_frame(template, kernel)

            ## init finish / next frame
            video[:, :, i] = frame  ###
            preprocess_frame = LOAD.filter_frame(torch.tensor(video[:, :, i], dtype=torch.float32).cuda(), kernel)
            normxcorr2_general_output = NormXCorr2(preprocess_temp, preprocess_frame)
            output, _ = normxcorr2_general_output.normxcorr2_general(sum1, a_rot_complex, b_complex,
                                                                     Zeros)
            Shift = ApplyShifts(output)
            new_filtered_frame, _, _ = Shift.apply_shift(preprocess_frame, theta)
            new_filtered_frame = new_filtered_frame.squeeze(0)
            preprocess_temp = preprocess_temp * (i + 1) / (i + 2) + new_filtered_frame / (i + 2)

            i += 1

        preprocess_temp = preprocess_temp.cpu().numpy()
        return preprocess_temp


# dir="E:/CaImage/1_22_2021/H18"  #文件夹名称
# filelist=[]
# for i in os.listdir(dir):  #遍历整个文件夹
#     path = os.path.join(dir, i)
#
#     if os.path.isfile(path):  #判断是否为一个文件，排除文件夹
#         if os.path.splitext(path)[1]==".avi":  #判断文件扩展名是否为“.avi”
#             filelist.append(i)
#
# filelist.sort(key=lambda x: int(x.split('msCam')[1].split('.avi')[0]))
# for i in filelist:
#     print(dir+'/'+i)
#
# path=dir+'/'+filelist[0]
# Pre=Preprocess(path)
# template=Pre.generate_template()
#
# for name in filelist:
#     filename = dir + '/' + name
#     print(filename)
#     cap = cv2.VideoCapture(filename)
#     NCCInstance=NCCProject(template, filename)
#     fps = cap.get(cv2.CAP_PROP_FPS)
#
#     size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
#     fNUMS = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#
#     C_next = np.empty((size[1], size[0], fNUMS))
#     i = 0
#     while (cap.isOpened()):
#         ret, frame = cap.read()
#         if ret == True:
#             frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
#             fixed_frame, template=NCCInstance.NCC_framebyframe(frame_gray)
#             cv2.imshow('frame', fixed_frame)
#             cv2.waitKey(50)
#             C_next[:, :, i] = fixed_frame
#             i+=1
#
#
#         else:
#             break
#     cv2.destroyAllWindows()
#     save_path = filename + '_' + 'MC'
#     io.savemat(save_path, {'MCvideo': C_next})


# cap=cv2.VideoCapture(path)
#
# NCCInstance=NCCProject(template, path)
#
# while(cap.isOpened()):
#     ret, frame=cap.read()
#     if ret==True:
#         frame=cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
#         fixed_frame=NCCInstance.NCC_framebyframe(frame)
#         cv2.imshow('frame',fixed_frame)
#         cv2.waitKey(50)
#
#
# cv2.destroyAllWindows()