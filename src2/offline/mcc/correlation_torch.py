import torch
import numpy as np
import time


class NormXCorr2():

    def __init__(self, input_T, input_A, requiredNumberOfOverlapPixels=0):
        self.T=input_T
        self.A=input_A
        self.requiredNumberOfOverlapPixels=requiredNumberOfOverlapPixels

    def local_sum(self, A, m, n):
        if(m==A.shape[0] and n==A.shape[1]):

            s=torch.cumsum(A, dim=0)
            w=s.shape[0]
            h=s.shape[1]
            temp=s[-1,:].repeat([m-1,1])-s[0:w-1,:]
            c=torch.cat((s, temp), 0)
            s=torch.cumsum(c, dim=1)
            del c

            w1=s.shape[0]
            h1=s.shape[1]
            temp1=s[:, -1].reshape(-1, 1).repeat([1,n-1])-s[:, 0:h1-1]
            local_sum_A=torch.cat((s,temp1),1)

        else:
            raise ValueError("The frame and the template cannot have different size.")
        return local_sum_A

    def FactorizeNumber(self, n):
        for ifac in [2,3,5]:
            while n%ifac==0:
                n=n/ifac

        return n

    def FindCloesValidDimension(self, n):
        newNumber=n
        result=0
        newNumber=newNumber-1
        while result!=1:
            newNumber=newNumber+1
            result=self.FactorizeNumber(newNumber)

        return newNumber

    def checkIfFlat(self, T):
        temp=torch.flatten(T)
        std=torch.std(temp)
        if std==0:
            raise ValueError("The values of Template cannot be the same.")

    def checkSizesTandA(self, T, A):
        num=T.shape[0]*T.shape[1]
        if num<2:
            raise ValueError("Template must contain at least 2 elements")

    def time_fft2(self, outsize):
        R=outsize[0]
        S=outsize[1]
        R=torch.tensor(R, dtype=torch.float32)
        S=torch.tensor(S, dtype=torch.float32)
        K_fft=3.3e-7
        Tr=K_fft*R*torch.log(R)
        if S==R:
            Ts=Tr
        else:
            Ts=K_fft*S*torch.log(S)

        time=S*Tr+R*Ts
        return time

    def time_conv2(self, obssize, refsize):
        K=2.7e-8
        time=K*torch.prod(obssize)*torch.prod(refsize)
        return time

    def complex_mul(self, real1, img1, real2, img2):
        real_new = real1 * real2 - img1 * img2
        img_new = img1 * real2 + real1 * img2
        return real_new, img_new

    def freqxcorr(self, a, b, outsize1, outsize2, a_rot_complex, b_complex):
        optimalSize1=self.FindCloesValidDimension(outsize1)
        optimalSize2=self.FindCloesValidDimension(outsize2)
        w1=a.shape[0]
        h1=a.shape[1]
        a_rot=torch.rot90(a, k=2)
        #a_rot_complex=torch.zeros([optimalSize1, optimalSize2, 2])
        a_rot_complex[0:w1, 0:h1, 0]=a_rot
        w2=b.shape[0]
        h2=b.shape[1]
        #b_complex=torch.zeros([optimalSize1, optimalSize2, 2])
        b_complex[0:w2, 0:h2, 0]=b
        # pytorch version < 1.7.0:
        # Fa=torch.fft(a_rot_complex,2)
        # Fb=torch.fft(b_complex,2)
        # Fa=torch.fft.fft(a_rot_complex,2)
        # Fb=torch.fft.fft(b_complex,2)
        # mul_real, mul_img=self.complex_mul(Fa[:,:,0],Fa[:,:,1],Fb[:,:,0],Fb[:,:,1])
        # Fa[:,:,0]=mul_real
        # Fa[:,:,1]=mul_img
        # temp = torch.ifft(Fa, 2)
        # xcorr_ab=temp[:,:,0]

        # pytorch version >= 1.7.0:
        a_rot_complex = torch.complex(a_rot_complex[:, :, 0], a_rot_complex[:, :, 1])
        b_complex = torch.complex(b_complex[:, :, 0], b_complex[:, :, 1])
        Fa = torch.fft.fft2(a_rot_complex)
        Fb = torch.fft.fft2(b_complex)
        mul_real, mul_img = self.complex_mul(Fa.real, Fa.imag, Fb.real, Fb.imag)
        Fa.real = mul_real
        Fa.img = mul_img
        temp = torch.fft.ifft2(Fa)
        xcorr_ab = temp.real
        xcorr_ab=xcorr_ab[0:outsize1, 0:outsize2]
        return xcorr_ab

    def xcorr2_fast(self, T, A, a_rot_complex, b_complex):

        # T_size=torch.tensor(T.shape)
        # A_size=torch.tensor(A.shape)
        # outsize=A_size+T_size-1

        outsize1=T.shape[0]+A.shape[0]-1
        outsize2=T.shape[1]+A.shape[1]-1
        # conv_time=self.time_conv2(T_size, A_size)
        # fft_time=3*self.time_fft2(outsize)

        #conv2d(need to supplement)

        cross_corr=self.freqxcorr(T, A, outsize1, outsize2, a_rot_complex, b_complex)
        return cross_corr

    def normxcorr2_general(self, sum1, a_rot_complex, b_complex, Zeros):


        sizeA=self.A.shape

        sizeT=self.T.shape
        numberOfOverlapPixels=self.local_sum(sum1, sizeT[0], sizeT[1])



        local_sum_A=self.local_sum(self.A, sizeT[0], sizeT[1])


        local_sum_A2=self.local_sum(torch.mul(self.A, self.A), sizeT[0], sizeT[1])



        diff_local_sums_A=(local_sum_A2 - (local_sum_A**2) / numberOfOverlapPixels)
        del local_sum_A2
        diff_local_sums_A[diff_local_sums_A < 0]=0
        denom_A=diff_local_sums_A
        del diff_local_sums_A

        rotatedT=torch.rot90(self.T, k=2)
        local_sum_T=self.local_sum(rotatedT, sizeA[0], sizeA[1])
        local_sum_T2=self.local_sum(rotatedT*rotatedT, sizeA[0], sizeA[1])
        del rotatedT

        diff_local_sums_T=(local_sum_T2-(local_sum_T**2) / numberOfOverlapPixels)
        del local_sum_T2
        diff_local_sums_T[diff_local_sums_T<0]=0
        denom_T=diff_local_sums_T
        del diff_local_sums_T

        denom=torch.sqrt(denom_T * denom_A)
        del denom_T
        del denom_A

        xcorr_TA=self.xcorr2_fast(self.T, self.A, a_rot_complex, b_complex)
        # xcorr_TA=torch.tensor(xcorr_TA, dtype=torch.float32)
        numerator=xcorr_TA-local_sum_A*local_sum_T/numberOfOverlapPixels

        del xcorr_TA
        del local_sum_A
        del local_sum_T


        C_shape=numerator.shape
        #C=torch.zeros(C_shape)
        denom_flatten=denom.flatten()
        flatten_max=torch.max(torch.abs(denom_flatten))
        tol=1000*(torch.finfo(flatten_max.dtype).eps)
        #denom_np=denom_flatten.numpy()
        #tol=1000* np.spacing(max(np.abs(denom_np)))

        c = numerator / denom

        B = torch.where(denom > tol, c, Zeros)


        del numerator
        del denom

        if self.requiredNumberOfOverlapPixels > torch.max(numberOfOverlapPixels.flatten()):
            raise ValueError


        B[numberOfOverlapPixels < self.requiredNumberOfOverlapPixels] = 0




        return B, numberOfOverlapPixels





