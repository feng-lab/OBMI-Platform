import cv2
import torch
import os
import numpy as np
from scipy.io import loadmat
import time
from scipy import ndimage
from torch.nn import functional as F

class load_data():
    def __init__(self, path):
        self.path=path

    def read_file(self):
        cap=cv2.VideoCapture(self.path)
        fps=cap.get(cv2.CAP_PROP_FPS)

        size=(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        fNUMS=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        C=np.empty((size[1], size[0], fNUMS))
        i=0

        while(cap.isOpened()):
            ret, frame=cap.read()
            if ret==True:

                frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                C[:, :, i] = frame_gray
                i=i+1
            else:
                break

        return C, fps, size

    def read_filestream(self):

        filelist = []
        for i in os.listdir(self.path):  # 遍历整个文件夹
            path = os.path.join(self.path, i)

            if os.path.isfile(path):  # 判断是否为一个文件，排除文件夹
                if os.path.splitext(path)[1] == ".avi":  # 判断文件扩展名是否为“.avi”
                    filelist.append(i)

        filelist.sort(key=lambda x: int(x.split('msCam')[1].split('.avi')[0]))

        first_file=self.path + '/' + filelist[0]
        print(first_file)
        cap = cv2.VideoCapture(first_file)
        fps = cap.get(cv2.CAP_PROP_FPS)

        size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        fNUMS = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        C = np.empty((size[1], size[0], fNUMS))
        i = 0
        while (cap.isOpened()):
            ret, frame = cap.read()
            if ret == True:
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                C[:, :, i] = frame_gray

            else:
                break
        del filelist[0]

        if len(filelist):
            for name in filelist:

                filename = self.path + '/' + name
                print(filename)
                cap = cv2.VideoCapture(filename)
                fps = cap.get(cv2.CAP_PROP_FPS)

                size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
                fNUMS = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                C_next = np.empty((size[1], size[0], fNUMS))
                i = 0
                while (cap.isOpened()):
                    ret, frame = cap.read()
                    if ret == True:
                        frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                        C_next[:, :, i] = frame_gray

                    else:
                        break
                C = np.concatenate((C, C_next), axis=2)

        return C, fps, size

    def filter(self, raw_data, kernel):

        #filter_video=np.empty(raw_data.shape)
        # psf=loadmat("psf.mat")
        # kernel = np.array(psf.get('psf'))
        for i in range(raw_data.shape[2]):
            #filter_video[:,:,i]=cv2.filter2D(raw_data[:,:,i], -1, kernel=kernel)
            raw_data[:, :, i] = cv2.filter2D(raw_data[:, :, i], -1, kernel=kernel)

        # enhanced_video = np.empty(raw_data.shape)
        #
        # for i in range(raw_data.shape[2]):
        #     enhanced_video[:, :, i] = self.Sharpen(raw_data[:, :, i])# remove background

        return raw_data



    def cut_frame(self, frame, crop_size):

        size1=frame.shape[0]
        size2=frame.shape[1]
        mid_height = size1/ 2
        mid_width = size2/ 2

        cropped_frame=frame[int(mid_height-crop_size/2):int(mid_height+crop_size/2), int(mid_width-crop_size/2):int(mid_width+crop_size/2)]
        return cropped_frame

    def filter_frame(self, crop_frame, kernel):
        filter_ouput=F.conv2d(crop_frame.unsqueeze(0).unsqueeze(0), kernel.unsqueeze(0).unsqueeze(0))

        return filter_ouput.squeeze(0).squeeze(0)

    # def Sharpen(self, img):
    #     img_smooth = ndimage.gaussian_filter(img, 3)
    #     low_pass_img = ndimage.gaussian_filter(img, 50)
    #     high_pass_img = img_smooth - low_pass_img
    #
    #     return high_pass_img

    def FactorizeNumber(self, n):
        for ifac in [2,3,5]:
            while n%ifac==0:
                n=n/ifac

        return n

    def generate_kernel(self, gSig_filt):
        ksize = tuple([(3 * i) // 2 * 2 + 1 for i in gSig_filt])
        ker = cv2.getGaussianKernel(ksize[0], gSig_filt[0])
        ker2D = ker.dot(ker.T)
        nz = np.nonzero(ker2D >= ker2D[:, 0].max())
        zz = np.nonzero(ker2D < ker2D[:, 0].max())
        ker2D[nz] -= ker2D[nz].mean()
        ker2D[zz] = 0

        return ker2D

    def FindCloesValidDimension(self, n):
        newNumber=n
        result=0
        newNumber=newNumber-1
        while result!=1:
            newNumber=newNumber+1
            result=self.FactorizeNumber(newNumber)

        return newNumber


    def Trans_GPU(self, high_filter=True, Crop=True):
        #not used
        C, fps, size=self.read_file()
        if high_filter==True:
            C=self.filter(C)
        else:
            pass

        if Crop==True:
            C=self.crop(C)

        C=torch.tensor(C, dtype=torch.float32)
        #C=C.cuda()

        return C, C.shape[0], C.shape[1], C.shape[2], fps, size

    def SetParameters(self, frame, kernel, CROP, use_gpu):
        #Set some parameters and intermediate variables used for calculate NCC on GPU.

        if CROP==False:
            frame = self.filter_frame(frame, kernel)

        sizeC=frame.shape

        sum1=torch.ones(sizeC, dtype=torch.float32)
        #sum1=sum1.cuda()
        outsize1 = frame.shape[0] + frame.shape[0] - 1
        outsize2 = frame.shape[1] + frame.shape[1] - 1
        optimalSize1 = self.FindCloesValidDimension(outsize1)
        optimalSize2 = self.FindCloesValidDimension(outsize2)
        a_rot_complex = torch.zeros([optimalSize1, optimalSize2, 2])
        b_complex = torch.zeros([optimalSize1, optimalSize2, 2])
        #a_rot_complex=a_rot_complex.cuda()
        #b_complex=b_complex.cuda()

        Zeros=torch.zeros([outsize1, outsize2], dtype=torch.float32)
        #Zeros=Zeros.cuda()

        theta = torch.tensor([
            [1, 0, 0],
            [0, 1, 0]
        ], dtype=torch.float32)
        #theta=theta.cuda()

        template_buffer=torch.zeros([sizeC[0], sizeC[1], 200], dtype=torch.float32)
        #template_buffer=template_buffer.cuda()
        if use_gpu==True:
            sum1 = sum1.cuda()
            a_rot_complex=a_rot_complex.cuda()
            b_complex=b_complex.cuda()
            Zeros = Zeros.cuda()
            theta = theta.cuda()
            template_buffer = template_buffer.cuda()

        return sum1, a_rot_complex, b_complex, Zeros, theta, template_buffer





