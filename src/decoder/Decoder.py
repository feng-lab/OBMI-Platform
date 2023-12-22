import traceback

import numpy as np
import os
import sys
import argparse
import math
import _pickle
import numpy as np
import random

import sklearn
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score,recall_score, f1_score, roc_auc_score,precision_score
import joblib

class OBMIDecoder():
    def __init__(self):
        # model_path = './decoder/best_svm.pkl'
        model_path = 'D:\data\obmi\\231214\model\model tq\\best_svm_1214_38.pkl'
        self.model = joblib.load(model_path)
        # 归一化常量，根据当天采集的数据集而定
        # self.data_min = -0.03512258532225913
        # self.data_max = 0.13549502268053126

        # self.data_min = -0.024158042929754545
        # self.data_max = 0.07747500551928602


        # 39 all
        # self.data_min = -0.04754848099313753
        # self.data_max = 0.6147035422720355

        # 39
        # self.data_min = -0.029390582304221695
        # self.data_max = 0.31663806488518415

        self.data_min = -0.01737869807302489
        self.data_max = 0.09952513139910092

        self.T = 0.9

    def inference(self, data):
        try:
            input_sample = np.reshape(data, (1, data.shape[0] * 30 ))   # 数据扁平化

            # input_sample = scaler.transform(input_sample) #标准化

            input_sample = (input_sample - self.data_min) / (self.data_max - self.data_min)

            # p_labels = self.model.predict(input_sample)
            p_labels = self.model.predict_proba(input_sample)[:, 1]
            p_labels = np.where(p_labels > self.T, 1, 0)
        except:
            print(traceback.format_exc())
            p_labels = -1
        # print('get label:', p_labels)

        return p_labels