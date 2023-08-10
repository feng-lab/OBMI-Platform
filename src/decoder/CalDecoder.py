import torch
import torch.nn as nn
import math
#from TCN import TemporalConvNet
from torch.nn.utils import weight_norm

class RDCNN(nn.Module):

    def __init__(self, sample_duration, sample_height, sample_width):
        super(RDCNN, self).__init__()

        self.maxpool = nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2), padding=(0, 1, 1))

        self.conv1 = nn.Conv3d(
            1,
            4,
            kernel_size=(1, 3, 3),
            stride=(1, 2, 2),
            padding=(0, 1, 1),
            bias=False)
        self.bn1 = nn.BatchNorm3d(4)
        self.relu1 = nn.ReLU(inplace=True)
        self.net1 = nn.Sequential(self.conv1, self.bn1, self.relu1)

        self.conv2 = nn.Conv3d(
            4,
            8,
            kernel_size=(1, 3, 3),
            stride=(1, 2, 2),
            padding=(0, 1, 1),
            bias=False)
        self.bn2 = nn.BatchNorm3d(8)
        self.relu2 = nn.ReLU(inplace=True)
        self.net2 = nn.Sequential(self.conv2, self.bn2, self.relu2)

        self.conv3 = nn.Conv3d(
            8,
            16,
            kernel_size=(1, 3, 3),
            stride=(1, 2, 2),
            padding=(0, 1, 1),
            bias=False)
        self.bn3 = nn.BatchNorm3d(16)
        self.relu3 = nn.ReLU(inplace=True)
        self.net3 = nn.Sequential(self.conv3, self.bn3, self.relu3)

        self.conv4 = nn.Conv3d(
            16,
            32,
            kernel_size=(1, 3, 3),
            stride=(1, 2, 2),
            padding=(0, 1, 1),
            bias=False)
        self.bn4 = nn.BatchNorm3d(32)
        self.relu4 = nn.ReLU(inplace=True)
        self.net4 = nn.Sequential(self.conv4, self.bn4, self.relu4)

        self.conv5 = nn.Conv3d(
            32,
            64,
            kernel_size=(1, 3, 3),
            stride=(1, 2, 2),
            padding=(0, 1, 1),
            bias=False)
        self.bn5 = nn.BatchNorm3d(64)
        self.relu5 = nn.ReLU(inplace=True)
        self.net5 = nn.Sequential(self.conv5, self.bn5, self.relu5)

        self.conv6 = nn.Conv3d(
            64,
            128,
            kernel_size=(1, 3, 3),
            stride=(1, 2, 2),
            padding=(0, 1, 1),
            bias=False)
        self.bn6 = nn.BatchNorm3d(128)
        self.relu6 = nn.ReLU(inplace=True)
        self.net6 = nn.Sequential(self.conv6, self.bn6, self.relu6)

        #last_duration = int(math.ceil(sample_duration / 128))
        last_height = int(math.ceil(sample_height / 128))
        last_width = int(math.ceil(sample_width / 128))
        self.avgpool = nn.AvgPool3d(
            (1, last_height, last_width), stride=1)


        for m in self.modules():
            if isinstance(m, nn.Conv3d):
                m.weight = nn.init.kaiming_normal_(m.weight, mode='fan_out')
            elif isinstance(m, nn.BatchNorm3d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def forward(self, x):
        x = self.maxpool(x)
        x = self.net1(x)
        x = self.net2(x)
        x = self.net3(x)
        x = self.net4(x)
        x = self.net5(x)
        x = self.net6(x)
        x = self.avgpool(x)

        return x

# class CNNTCN(nn.Module):
#
#     def __init__(self, sample_duration, sample_height, sample_width, tcn_inputs_channels=128, tcn_hidden_channels=[64, 32, 16, 8], kernel_size=2, drop_out=0.1):
#         super(CNNTCN, self).__init__()
#
#         layers1 = [RDCNN(sample_duration, sample_height, sample_width)]
#         layers2 = [TemporalConvNet(num_inputs = tcn_inputs_channels, num_channels = tcn_hidden_channels,
#                                    kernel_size = kernel_size, dropout = drop_out)]
#
#
#         self.CNN = nn.Sequential(*layers1)
#
#
#         self.TCN = nn.Sequential(*layers2)
#
#         self.FCN1 = weight_norm(nn.Conv1d(in_channels=tcn_hidden_channels[-1], out_channels=4, kernel_size=1, stride=1, padding=0))
#         self.relu1 = nn.ReLU()
#         self.ds1 = nn.Sequential(self.FCN1, self.relu1)
#
#         self.FCN2 = weight_norm(
#             nn.Conv1d(in_channels=4, out_channels=1, kernel_size=1, stride=1, padding=0))
#         self.relu2 = nn.ReLU()
#         self.ds2 = nn.Sequential(self.FCN2, self.relu2)
#
#         # self.FCN3 = weight_norm(
#         #     nn.Conv1d(in_channels=2, out_channels=1, kernel_size=1, stride=1, padding=0))
#         # self.relu3 = nn.ReLU()
#         # self.ds3 = nn.Sequential(self.FCN3, self.relu3)
#
#     def init_weights(self):
#         """
#         参数初始化
#
#         :return:
#         """
#         self.FCN1.weight.data.normal_(0, 0.1)
#         self.FCN2.weight.data.normal_(0, 0.1)
#         # self.FCN3.weight.data.normal_(0, 0.01)
#
#     def forward(self, x):
#         x = self.CNN(x)
#         x = x.squeeze(3).squeeze(3)
#         x = self.TCN(x)
#         x = x.reshape(x.size(0), x.size(1) * x.size(2))
#         x = self.ds1(x)
#         x = self.FCN2(x)
#         # x = self.ds3(x)
#         x = x.squeeze(1)
#
#         return x

class CNNLSTM(nn.Module):

    def __init__(self, sample_duration, sample_height, sample_width,):
        super(CNNLSTM, self).__init__()

        layers1 = [RDCNN(sample_duration, sample_height, sample_width)]
        layers2 = [nn.LSTM(input_size=128, hidden_size=64, num_layers=2, bidirectional=False)]

        self.CNN = nn.Sequential(*layers1)
        self.LSTM = nn.Sequential(*layers2)


        self.fc1 = nn.Linear(in_features=64 * 20, out_features=1 * 20)

        self.FCN1 = weight_norm(
            nn.Conv1d(in_channels=128, out_channels=32, kernel_size=1, stride=1, padding=0))
        self.relu1 = nn.ReLU()
        self.ds1 = nn.Sequential(self.FCN1, self.relu1)

        self.FCN2 = weight_norm(
            nn.Conv1d(in_channels=32, out_channels=4, kernel_size=1, stride=1, padding=0))
        self.relu2 = nn.ReLU()
        self.ds2 = nn.Sequential(self.FCN2, self.relu2)

        self.FCN3 = weight_norm(
            nn.Conv1d(in_channels=4, out_channels=1, kernel_size=1, stride=1, padding=0))
        # self.relu3 = nn.ReLU()
        # self.ds3 = nn.Sequential(self.FCN3, self.relu3)


    def init_weights(self):
        """
        参数初始化

        :return:
        """
        self.FCN1.weight.data.normal_(0, 0.01)
        self.FCN2.weight.data.normal_(0, 0.01)
        self.FCN3.weight.data.normal_(0, 0.01)

    def forward(self, x):
        x = self.CNN(x)
        x = x.squeeze(3).squeeze(3)
        x = x.permute(2, 0, 1)
        x, _ = self.LSTM(x)
        x = x.permute(1, 2, 0)
        #print(x.shape)
        x = x.reshape(x.size(0), x.size(1)*x.size(2))
        #print(x.shape)
        x = self.fc1(x)
        # x = self.relu1(x)
        # x = self.fc2(x)
        # x = self.relu2(x)
        # x = self.fc3(x)


        #
        # x = self.ds1(x)
        # x = self.ds2(x)
        # x = self.FCN3(x)
        # x = x.squeeze(1)

        return x
