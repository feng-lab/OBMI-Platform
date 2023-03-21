import torch
import numpy as np
from scipy.io import loadmat
import os
import torch.nn as nn
from torch.utils.data import Dataset



class MyDatasets(Dataset):

    def __init__(self, all_list, all_label):
        self.all_list = all_list
        self.all_label = all_label

    def __getitem__(self, idx):
        data_path = self.all_list[idx]
        label = self.all_label[idx]
        matdata = loadmat(data_path)
        data = torch.from_numpy(matdata['frame_buffer'])
        # vec = data.flatten()
        # max_num = torch.max(vec)
        data = data / 150
        data = data.transpose(0, 2)
        data = data.transpose(1, 2)

        data = data.unsqueeze(dim=0)

        return data, label

    def __len__(self):
        return len(self.all_label)

class MyDatasetsFitting(Dataset):

    def __init__(self, all_list, press_label):
        self.all_list = all_list
        self.press_label = press_label

    def __getitem__(self, idx):
        data_path = self.all_list[idx]
        label = self.press_label[idx, :]
        matdata = loadmat(data_path)
        data = torch.from_numpy(matdata['frame_buffer'])
        vec = data.flatten()
        max_num = torch.max(vec)
        data = data/max_num
        data = data.transpose(0, 2)
        data = data.transpose(1, 2)
        data = data.unsqueeze(dim=0)

        return data, label

    def __len__(self):
        return len(self.all_list)





# dir_n='/home/mingkang/calciumproject/negative_sample/'
# dir_p='/home/mingkang/calciumproject/positive_sample/'
# n_list, nlabel=getFileList_N(dir_n)
# p_list, plabel=getFileList_P(dir_p)
# data = loadmat(n_list[0])
# a=data['frame_buffer']
# b=torch.from_numpy(a)
# print(type(b))