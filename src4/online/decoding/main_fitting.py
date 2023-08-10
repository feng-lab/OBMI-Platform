#!/home/mingkang/anaconda3/envs/calcium/bin/python

# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import time

import torch
import numpy as np
import cv2
import matplotlib.pyplot as plt
import scipy
import resnet
#import densenet
from ReadData import MyDatasetsFitting
from torch.utils.data import DataLoader
from torch import nn
import os
from scipy.io import loadmat
#import TCN3D
#from CalDecoder import CNNTCN
from CalDecoder import CNNLSTM


def getFileList_P(dir_name):

    file_list = []
    plabel = []
    for i in os.listdir(dir_name):
        path = os.path.join(dir_name, i)
        if os.path.isfile(path):
            if os.path.splitext(path)[1] == ".mat":
                file_list.append(i)

    file_list.sort(key = lambda x : int(x.split('sample')[1].split('.mat')[0]))
    for i in range(len(file_list)):
        file_list[i]=dir_name+file_list[i]
        plabel.append(1)
    return file_list, plabel


def getFileList_N(dir_name):
    file_list = []
    nlabel = []
    for i in os.listdir(dir_name):
        path = os.path.join(dir_name, i)
        if os.path.isfile(path):
            if os.path.splitext(path)[1] == ".mat":
                file_list.append(i)

    file_list.sort(key=lambda x: int(x.split('sample')[1].split('.mat')[0]))

    # n_list=[]
    # for i in range(len(file_list)):
    #     if i%7==0:
    #         n_list.append(file_list[i])

    for i in range(len(file_list)):
        file_list[i] = dir_name + file_list[i]
        nlabel.append(0)

    return file_list, nlabel

def makeList(plist, nlist):

    return plist+nlist



# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    dir_name_p = '/src/decoder\pos\\'
    dir_name_n = '/src/decoder\\neg\\'
    p_list, plabel = getFileList_P(dir_name_p)
    n_list, nlabel = getFileList_N(dir_name_n)

    p_list_train = p_list[0:15]
    n_list_train = n_list[0:15]

    p_list_test = p_list[15:]
    n_list_test = n_list[15:]

    all_list_train = makeList(p_list_train, n_list_train)
    all_list_test = makeList(p_list_test, n_list_test)


    BATCH_SIZE = 8

    press_path = '/src/decoder\\all_press_filter10.mat'
    press_path_negative = '/src/decoder\\all_press_negative_filter10.mat'
    matdata = loadmat(press_path)
    matdata_negative = loadmat(press_path_negative)
    all_press = matdata['all_press']
    all_press_negative = matdata_negative['all_press']
    all_press = np.array([all_press], dtype=np.float32)
    all_press_negative = np.array([all_press_negative], dtype=np.float32)
    all_press = (all_press-1600)/500
    all_press_negative = (all_press_negative-1600)/500






    press_label = torch.from_numpy(all_press)
    press_label_negative = torch.from_numpy(all_press_negative)
    press_label = press_label.squeeze(0)
    press_label_negative = press_label_negative.squeeze(0)
    press_label_train = press_label[0:15, :]
    press_label_train_negative = press_label_negative[0:15, :]
    press_label_test = press_label[15:30, :]
    press_label_test_negative = press_label_negative[15:30, :]

    all_press_label_train = torch.cat((press_label_train, press_label_train_negative), dim=0)
    all_press_label_test = torch.cat((press_label_test, press_label_test_negative), dim=0)

    print(all_press_label_train.shape)
    print(all_press_label_test.shape)

    train_loader = DataLoader(MyDatasetsFitting(all_list_train, all_press_label_train), batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(MyDatasetsFitting(all_list_test, all_press_label_test), batch_size=BATCH_SIZE, shuffle=True)

    #model = TCN3D.TemporalConvNet3D(1, [32, 64, 64, 32], 20, 241, 377, [3, 3, 3])
    model = CNNLSTM(sample_duration=20, sample_height=241, sample_width=377)
    #model = densenet.DenseNet(sample_height=241, sample_width=377, sample_duration=20)
    model = nn.DataParallel(model)
    model = model.cuda()

    learning_rate = 0.0003
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(params=model.parameters(), lr=learning_rate)

    # scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.95)


    TOTAL_EPOCHS = 50

    train_loss_list = []
    valid_loss_list = []

    for epoch in range(TOTAL_EPOCHS):
        train_loss_sum = 0
        valid_loss_sum = 0

        if epoch == TOTAL_EPOCHS-1:
            final_outlist = []
            final_outlabel = []

        correct = 0  # 记录正确的个数，每个epoch训练完成之后打印accuracy
        for i, (images, labels) in enumerate(train_loader):
            images = images.float().cuda()
            #labels = torch.tensor(labels, dtype=torch.long)
            labels = labels.cuda()
            optimizer.zero_grad()  # 清零
            outputs = model(images)
            print(outputs)


            # 计算损失函数
            loss = criterion(outputs, labels)
            #print('output:', outputs)
            #print('label', labels)
            loss.backward()
            optimizer.step()


            print("Training Set:")
            print("epoch: {}, iter:{} ,loss: {}".format(epoch, i, loss.item()))
            train_loss_sum += loss.item()

        train_loss_list.append(train_loss_sum/(i+1))
        # scheduler.step()

        # 每个epoch计算测试集accuracy

        with torch.no_grad():
            for i, (images, labels) in enumerate(val_loader):
                t0 = time.time()
                images = images.float().cuda()
                labels = labels.cuda()
                optimizer.zero_grad()
                y_hat = model(images)

                print(y_hat.shape)
                print(labels.shape)
                loss_t = criterion(y_hat, labels).item()  # batch average loss
                valid_loss_sum += loss_t
                if epoch == TOTAL_EPOCHS-1:
                    y_hat_fl = y_hat.flatten()
                    labels_fl = labels.flatten()
                    size1 = y_hat_fl.shape[0]
                    #print(y_hat_fl.shape)
                    for j in range(size1):
                        final_outlist.append(y_hat_fl[j].cpu().numpy())
                        final_outlabel.append(labels_fl[j].cpu().numpy())

                print("Valid Set:")
                print("epoch: {}, iter:{} ,loss: {}".format(epoch, i, loss_t))
                t1 = time.time()
                print('decoding time:', (t1-t0)/20)

            valid_loss_list.append(valid_loss_sum/(i+1))

    test_random_sample1 = torch.rand([1, 1, 20, 241, 377])
    test_random_sample1 = test_random_sample1.cuda()
    test_output1 = model(test_random_sample1)
    test_output1 = test_output1.cpu()
    test_output1 = test_output1.squeeze()
    test_output1 = test_output1.detach().numpy()

    test_random_sample2 = torch.rand([1, 1, 20, 241, 377])
    test_random_sample2 = test_random_sample2.cuda()
    test_output2 = model(test_random_sample2)
    test_output2 = test_output2.cpu()
    test_output2 = test_output2.squeeze()
    test_output2 = test_output2.detach().numpy()
    # plt.figure(1)

    np_final_outlist = np.array(final_outlist)
    np_final_outlabel = np.array(final_outlabel)

    cor = np.corrcoef(np_final_outlist, np_final_outlabel)
    print("相关系数：", cor)

    p1 = plt.plot(final_outlist,  label='Output')
    p2 = plt.plot(final_outlabel, label='Label')
    plt.xlabel("Epoch")
    plt.ylabel("Press")
    plt.legend()
    plt.figure(2)
    p3 = plt.plot(train_loss_list, label='Trainset')
    p4 = plt.plot(valid_loss_list, label='Validset')
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.figure(3)
    plt.plot(final_outlist)
    plt.figure(4)
    plt.plot(final_outlabel)
    plt.show()

    #plt.savefig("SimulatedAllNeuronFitting.png")

    #os.environ["CUDA_VISIBLE_DEVICES"] = "1"
    # dir_name_p = '/home/mingkang/calciumproject/positive_sample/'
    # dir_name_n = '/home/mingkang/calciumproject/negative_sample/'
    # p_list, plabel = getFileList_P(dir_name_p)
    # n_list, nlabel = getFileList_N(dir_name_n)
    # all_list, all_label = makeListandLabel(p_list, plabel, n_list, nlabel)
    # print('start')
    # model = resnet.resnet18(sample_height=480, sample_width=752, sample_duration=25)
    # print('..')
    # #model = model.cuda()
    # print('done')
    # k_fold(5, model, all_list, all_label)
    # model = resnet.resnet34(sample_height=480, sample_width=752, sample_duration=25)
    # data=torch.rand([1,1,5,10,10])
    # print('..')
    # data=data.cuda()
    # print('done')
    # x=model(data)
    # print(x)
    # dataset = MyDatasets(all_list, all_label)
    # dataloader = DataLoader(dataset, batch_size=1, shuffle=True)
    #
    # for i, (images, labels) in enumerate(dataloader):
    #     images = images.float()
    #     labels = torch.squeeze(labels.type(torch.LongTensor))
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
