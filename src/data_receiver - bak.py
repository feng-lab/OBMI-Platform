import datetime
import time

import h5py
import numpy as np
import torch
from PySide2 import QtCore
from PySide2.QtCore import QObject, QThread, QTimer, Qt

from src.ROI import ROIType
from queue import Queue

class ReceiverThread(QThread):
    def __init__(self, trace_viewer, parent):
        super(ReceiverThread, self).__init__()
        self.data_receiver = DataReceiver(trace_viewer)
        self.parent = parent
        self.timer = QTimer(self)
        # self.img_buffer = Queue(maxsize=-1)

    def run(self):
        self.data_receiver.moveToThread(self)

        self.parent.on_scope.frameG.connect(self.data_receiver.recieve_img)
        self.timer.timeout.connect(self.data_receiver.data_handler)
        self.timer.start(1)
        print('run')


class DataReceiver(QObject):

    def __init__(self, trace_viewer, parent):
        super(DataReceiver, self).__init__()
        self.parent = parent
        self.trace_viewer = trace_viewer
        self.itemlist = trace_viewer.itemlist
        self.frame_count = 1
        self.img_buffer = []
        self.filename = datetime.datetime.now().strftime('%F %T') + '.h5'

        self.save_file = h5py.File('trace_data_2.h5', 'w')  # change to self.filename
        self.save_file["version"] = 1.0
        self.save_file.close()

        self.range_list_reset()

        self.timer = QTimer()

    def start(self):
        self.parent.on_scope.frameG.connect(self.recieve_img)
        self.timer.timeout.connect(self.data_handler)
        self.timer.start(1)

    def stop(self):
        self.timer.stop()

    def range_list_reset(self):
        self.max_list = [0, 0, 0, 0, 0]
        self.window_size = 300


    def recieve_img(self, img):
        self.img_buffer.append(img)

    def data_handler(self):
        if len(self.img_buffer) == 0:
            return
        else:
            img = self.img_buffer.pop(0)
            print('read img, remaining: ', len(self.img_buffer))
            t0 = time.time()

        num = len(self.itemlist)
        data = np.empty((num, 6))
        #contours = []
        shape_data = []


        for i in range(num):
            item = self.itemlist[i]
            x = int(item.pos().x())
            y = int(item.pos().y())
            width = int(item.boundingRect().width())
            height = int(item.boundingRect().height())

            # extract gray value
            imgmat = img[y:y + height, x:x + width].flatten()
            if torch.cuda.is_available():
                imgmat = torch.tensor(imgmat)
                item_noise = torch.tensor(item.noise)
                item_mat = torch.tensor(item.mat)
            else:
                item_noise = item.noise
                item_mat = item.mat

            noise = imgmat * item_noise
            noise_exist = (item_noise != 0)
            noise_avg = int(noise.sum() / noise_exist.sum())

            res = imgmat * item_mat - noise_avg
            res[res < 0] = 0
            exist = (res != 0)
            if exist.sum() == 0:
                avg = 0
            else:
                avg = int(res.sum() / exist.sum())
                if noise_avg != 0:
                    avg = avg / noise_avg

                # if i < 5:
                #     self.trace_viewer.traces[i].append(QtCore.QPointF(self.frame_count, avg))
                #     if avg > self.max_list[i]:
                #         self.max_list[i] = avg
                #
                #     print('trace update')
                #     chart = self.trace_viewer.chartlist[i].chart()
                #     series = chart.series()[0]
                #     series.append(self.frame_count, avg)
                #     chart.axisY().setMax(self.max_list[i])
                #
                #     if self.frame_count % 300 == 0:
                #         series.clear()
                #         chart.axisX().setMax(self.frame_count + 300)
                #         self.trace_viewer.chartlist[i].max = self.frame_count + 300
                #         chart.axisX().setMin(self.frame_count)
                #         self.range_list_reset()

            # if i < 5:
            #     chart = self.trace_viewer.chartlist[i].chart()
            #     chart.series()[0].append(QtCore.QPointF(self.frame_count, avg))
            #     chart.axisX().setMax(self.frame_count)
            #     self.trace_viewer.chartlist[i].max = self.frame_count
            #     if self.frame_count > 500:
            #         chart.axisX().setMin(self.frame_count - 500)
            #         if chart.series()[0].count() > 500:
            #             chart.series()[0].removePoints(0, chart.series()[0].count() - 501)
            #     if avg > chart.axisY().max():
            #         chart.axisY().setMax(avg)

            if len(self.trace_viewer.traces[i]) > self.window_size:
                self.trace_viewer.traces[i].pop(0)
            self.trace_viewer.traces[i].append(avg)

            if i < 5:
                chart = self.trace_viewer.chartlist[i].chart()
                chart.series()[0].append(QtCore.QPointF(self.frame_count + 1, avg))
                chart.axisX().setMax(self.frame_count + 1)
                self.trace_viewer.chartlist[i].max = self.frame_count + 1
                if self.frame_count + 1 > self.window_size:
                    chart.axisX().setMin(self.frame_count - self.window_size + 2)
                    if chart.series()[0].count() > self.window_size:
                        chart.series()[0].removePoints(0, chart.series()[0].count() - self.window_size)
                if avg > chart.axisY().max():
                    chart.axisY().setMax(avg)

            c_size = item.c_size
            #contours.append(item.contours)
            #contours.extend(item.contours.tolist())
            shape_data.extend(item.contours.tolist())

            if item.type == ROIType.CIRCLE:
                type = 1
            else:
                type = 2

            data[i] = np.array([item.id, x, y, type, c_size, avg])


        t2 = time.time()
        str = f'{self.frame_count:06}'
        with h5py.File('trace_data_2.h5', 'a') as f:
            g = f.create_group(str)
            g["image"] = img
            g["data"] = data
            g["contours"] = np.array(shape_data)
            # g["contours"] = np.array(contours)
        self.frame_count += 1
        t1 = time.time()
        print(f'recieve extraction: {t2 - t0}\n'
              f'recieve saving: {t1 - t2}\n'
              f'recieve total: {t1 - t0}')
        # print('recieve time: ', t1 - t0)

