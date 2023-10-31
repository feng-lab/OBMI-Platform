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
        model_path = 'C:\\Users\ZJLAB\Documents\WeChat Files\wxid_ciusgv6gvwq222\FileStorage\File\\2023-10\\best_svm_1012.pkl'
        self.model = joblib.load(model_path)
        # 归一化常量，根据当天采集的数据集而定
        self.data_min = -0.03512258532225913
        self.data_max = 0.13549502268053126

    def inference(self, data):
        try:
            input_sample = np.reshape(data, (1, 10 * 30 ))   # 数据扁平化

            # input_sample = scaler.transform(input_sample) #标准化

            input_sample = (input_sample - self.data_min) / (self.data_max - self.data_min)

            p_labels = self.model.predict(input_sample)
        except:
            print(traceback.format_exc())
            p_labels = -1
        # print('get label:', p_labels)

        return p_labels