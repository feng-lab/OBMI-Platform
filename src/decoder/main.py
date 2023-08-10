#!/home/mingkang/anaconda3/envs/calcium/bin/python

# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import torch
import matplotlib.pyplot as plt
import resnet
from ReadData import MyDatasets
from torch.utils.data import DataLoader
from torch import nn
import os


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

def makeListandLabel(plist, pabel, nlist, nlabel):

    return plist+nlist, pabel+nlabel

def get_kfold_data(k, i, all_list, all_label):
    # 返回第 i+1 折 (i = 0 -> k-1) 交叉验证时所需要的训练和验证数据，X_train为训练集，X_valid为验证集
    fold_size = len(all_list) // k  # 每份的个数:数据总条数/折数（组数）

    val_start = i * fold_size
    if i != k - 1:
        val_end = (i + 1) * fold_size
        # X_valid, y_valid = X[val_start:val_end], y[val_start:val_end]
        # X_train = torch.cat((X[0:val_start], X[val_end:]), dim=0)
        # y_train = torch.cat((y[0:val_start], y[val_end:]), dim=0)
        list_valid, label_valid = all_list[val_start: val_end], all_label[val_start: val_end]
        list_train = all_list[0: val_start] + all_list[val_end:]
        label_train = all_label[0: val_start] + all_label[val_end:]
    else:  # 若是最后一折交叉验证
        # X_valid, y_valid = X[val_start:], y[val_start:]  # 若不能整除，将多的case放在最后一折里
        # X_train = X[0:val_start]
        # y_train = y[0:val_start]
        list_valid, label_valid = all_list[val_start:], all_label[val_start:]
        list_train = all_list[0: val_start]
        label_train = all_label[0: val_start]

    return list_train, label_train, list_valid, label_valid



# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    dir_name_p = 'D:\project\OBMI-Platform\src\decoding\pos\\'
    dir_name_n = 'D:\project\OBMI-Platform\src\decoding\\neg\\'
    p_list, plabel = getFileList_P(dir_name_p)
    n_list, nlabel = getFileList_N(dir_name_n)

    p_list_train = p_list[0:-25]
    n_list_train = n_list[0:-25]

    p_list_test = p_list[-25:]
    n_list_test = n_list[-25:]

    plabel_train = plabel[0:-25]
    nlabel_train = nlabel[0:-25]

    plabel_test = plabel[-25:]
    nlabel_test = nlabel[-25:]

    all_list_train, all_label_train = makeListandLabel(p_list_train, plabel_train, n_list_train, nlabel_train)
    all_list_test, all_label_test = makeListandLabel(p_list_test, plabel_test, n_list_test, nlabel_test)

    BATCH_SIZE = 8

    train_loader = DataLoader(MyDatasets(all_list_train, all_label_train), batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(MyDatasets(all_list_test, all_label_test), batch_size=BATCH_SIZE, shuffle=True)

    model = resnet.resnet10(sample_height=241, sample_width=377, sample_duration=20)
    #model = densenet.DenseNet(sample_height=241, sample_width=377, sample_duration=20)
    model = nn.DataParallel(model)
    model = model.cuda()

    learning_rate = 0.000001
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(params=model.parameters(), lr=learning_rate)

    scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.9)
    losses = []
    val_losses = []
    train_acc = []
    val_acc = []
    TOTAL_EPOCHS = 50

    for epoch in range(TOTAL_EPOCHS):

        correct = 0  # 记录正确的个数，每个epoch训练完成之后打印accuracy
        for i, (images, labels) in enumerate(train_loader):
            images = images.float().cuda()
            labels = torch.tensor(labels, dtype=torch.long)
            labels = labels.cuda()
            optimizer.zero_grad()  # 清零
            outputs = model(images)


            # 计算损失函数
            loss = criterion(outputs, labels)
            #print('output:', outputs)
            #print('label', labels)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
            # 计算正确率
            y_hat = model(images)
            pred = y_hat.max(1, keepdim=True)[1]
            correct += pred.eq(labels.view_as(pred)).sum().item()

            if (i + 1) % BATCH_SIZE == 0:
                # 每10个batches打印一次loss
                print('Epoch : %d/%d, Iter : %d/%d,  Loss: %.4f' % (epoch + 1, TOTAL_EPOCHS,
                                                                    i + 1, len(all_list_train) // BATCH_SIZE,
                                                                    loss.item()))
        accuracy = 100. * correct / len(all_list_train)
        print('Epoch: {}, Loss: {:.5f}, Training set accuracy: {}/{} ({:.3f}%)'.format(
            epoch + 1, loss.item(), correct, len(all_list_train), accuracy))
        train_acc.append(accuracy)

        # 每个epoch计算测试集accuracy
        val_loss = 0
        correct = 0
        with torch.no_grad():
            for i, (images, labels) in enumerate(val_loader):
                images = images.float().cuda()
                labels = torch.tensor(labels, dtype=torch.long).cuda()
                optimizer.zero_grad()
                y_hat = model(images)

                y_hat = y_hat
                loss = criterion(y_hat, labels).item()  # batch average loss
                val_loss += loss * len(labels)  # sum up batch loss
                pred = y_hat.max(1, keepdim=True)[1]  # get the index of the max log-probability
                correct += pred.eq(labels.view_as(pred)).sum().item()

        val_losses.append(val_loss / len(all_list_test))
        accuracy = 100. * correct / len(all_list_test)
        print('Test set: Average loss: {:.4f}, Accuracy: {}/{} ({:.3f}%)\n'.format(
            val_loss, correct, len(all_list_test), accuracy))
        val_acc.append(accuracy)


    p1 = plt.plot(val_acc)
    p2 = plt.plot(train_acc)
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.show()
    plt.savefig("BackgroundRemoveData.png")

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
