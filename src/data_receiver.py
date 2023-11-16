import datetime
import time
from multiprocessing import Process, Queue

import h5py
import numpy as np
import torch
from PySide2 import QtCore
from PySide2.QtCore import QObject, QThread, QTimer, Qt

from src.ROI import ROIType
from src.decoder.Decoder import OBMIDecoder



def extraction(item, img):
    x = int(item['x'])
    y = int(item['y'])
    outlines = item['contours'].copy().reshape((-1, 2))  # 相对坐标

    outlines[:, 0] += x
    outlines[:, 1] += y

    x_min = int(np.min(outlines[:, 0]))
    x_max = int(np.max(outlines[:, 0]))
    y_min = int(np.min(outlines[:, 1]))
    y_max = int(np.max(outlines[:, 1]))
    center_x = x_min + (x_max - x_min) // 2
    center_y = y_min + (y_max - y_min) // 2
    r_cell = (x_max - x_min) // 2
    dist = 5

    xx, yy = np.meshgrid(np.arange(x_min, x_max + 1), np.arange(y_min, y_max + 1))
    distances = np.sqrt((xx - center_x) ** 2 + (yy - center_y) ** 2)
    mask_cell = distances < (x_max - x_min) / 2

    masked_frame = img[y_min:y_max + 1, x_min:x_max + 1] * mask_cell
    F_cell = np.sum(masked_frame)
    cnt_cell = np.sum(mask_cell)
    F_cell = F_cell / cnt_cell

    x_min = x_min - dist
    x_max = x_max + dist
    y_min = y_min - dist
    y_max = y_max + dist

    xx, yy = np.meshgrid(np.arange(x_min, x_max + 1), np.arange(y_min, y_max + 1))
    distances = np.sqrt((xx - center_x) ** 2 + (yy - center_y) ** 2)
    mask_all = np.logical_and(distances < (x_max - x_min) / 2, distances > r_cell)

    masked_frame = img[y_min:y_max + 1, x_min:x_max + 1] * mask_all
    F_all = np.sum(masked_frame)
    cnt_all = np.sum(mask_all)
    F_b = F_all / cnt_all

    res = (F_cell - F_b) / F_b
    return res
def extract_process(input_stream:Queue, output_stream:Queue, itemlist):
    while True:
        if input_stream.qsize() > 0:
            img = input_stream.get()
            avg = [extraction(item, img) for item in itemlist]
            output_stream.put(avg)
            time.sleep(0.001)
        else:
            time.sleep(0.01)

class ReceiverThread(QThread):
    def __init__(self, trace_viewer, frame_signal):
        super(ReceiverThread, self).__init__()
        self.trace_viewer = trace_viewer
        self.frame_signal = frame_signal
        self.itemlist = trace_viewer.itemlist
        self.frame_count = 1

        self.filename = datetime.datetime.now().strftime('%F %T') + '.h5'

        self.save_file = h5py.File('trace_data_2.h5', 'w')  # change to self.filename
        self.save_file["version"] = 1.0
        self.save_file.close()

        self.range_list_reset()
        self.interval = 0.03

        self.img_buffer = Queue(maxsize=-1)
        self.out_stream = Queue(maxsize=-1)

        self.timer = QTimer()
        self.timer.timeout.connect(self.traceupdate)

    def start_process(self):
        self.frame_signal.connect(self.recieve_img)

        itemlist = [item.get_contour_dict() for item in self.itemlist]
        self.p = Process(target=extract_process, args=(self.img_buffer, self.out_stream, itemlist,))
        self.p.start()
    def traceupdate(self):
        if self.out_stream.empty():
            return

        avgs = self.out_stream.get()
        if self.img_buffer.qsize() > 1:
            print("img buffer, remaining:", self.img_buffer.qsize())
        if self.out_stream.qsize() > 0:
            print('read img, remaining:', self.out_stream.qsize())

        self.trace_viewer.full_trace_update(avgs, self.frame_count)
        self.frame_count += 1

    def run(self):
        self.frame_signal.connect(self.recieve_img)

        itemlist = [item.get_contour_dict() for item in self.itemlist]
        self.p = Process(target=extract_process, args=(self.img_buffer, self.out_stream, itemlist,))
        self.p.start()

        self.timer.start(20)
        # while not self.isInterruptionRequested():
        #     if self.out_stream.empty():
        #         self.msleep(20)
        #         continue
        #     avgs = self.out_stream.get()
        #     if self.img_buffer.qsize() > 1:
        #         print("img buffer, remaining:", self.img_buffer.qsize())
        #     if self.out_stream.qsize() > 0:
        #         print('read img, remaining:', self.out_stream.qsize())
        #
        #     self.trace_viewer.full_trace_update(avgs, self.frame_count)
        #     self.frame_count += 1
        #     self.msleep(1)

    def recieve_img(self, img):
        self.img_buffer.put(img)

    def range_list_reset(self):
        self.max_list = [0, 0, 0, 0, 0]
        self.window_size = 300


class TraceProcess(QObject):
    def __init__(self, in_queue, itemlist):
        super(TraceProcess, self).__init__()
        self.in_queue = in_queue
        self.out_queue = Queue(maxsize=-1)
        self.itemlist = itemlist

    def start(self):
        itemlist = [item.get_contour_dict() for item in self.itemlist]
        p = Process(target=extract_process, args=(self.in_queue, self.out_queue, itemlist,))
        p.start()

class DataReceiver(QObject):
    decoding_sig = QtCore.Signal(bool)

    def __init__(self, trace_viewer, frame_signal, network_controller, decoding_text):
        super(DataReceiver, self).__init__()
        self.frame_signal = frame_signal
        self.network_controller = network_controller
        self.trace_viewer = trace_viewer
        self.decoding_text = decoding_text
        self.decoding_timer = 0
        self.itemlist = trace_viewer.itemlist
        self.frame_count = 1
        self.img_buffer = []
        self.filename = datetime.datetime.now().strftime('%F %T') + '.h5'

        self.save_file = h5py.File('trace_data_2.h5', 'w')  # change to self.filename
        self.save_file["version"] = 1.0
        self.save_file.close()

        self.range_list_reset()

        self.timer = QTimer()

        self.traces = None
        self.decoding = False
        self.decoder = None

        self.fake = False
        self.j = 0

    def start(self):
        self.frame_signal.connect(self.recieve_img)
        self.timer.timeout.connect(self.data_handler)
        self.timer.start(1)

    def stop(self):
        self.timer.stop()

    def range_list_reset(self):
        self.max_list = [0, 0, 0, 0, 0]
        self.window_size = 300


    def recieve_img(self, img):
        self.img_buffer.append(img)

    def decoder_init(self):
        self.decoder = OBMIDecoder()
        num = len(self.itemlist)
        self.traces = np.empty((num,))
        self.decoding = True

    def extraction(self, item, img):
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

        return avg

    def extraction_v2(self, item, img):
        x = int(item.pos().x())
        y = int(item.pos().y())
        outlines = item.contours.copy().reshape((-1, 2))  # 相对坐标

        outlines[:, 0] += x
        outlines[:, 1] += y

        x_min = int(np.min(outlines[:, 0]))
        x_max = int(np.max(outlines[:, 0]))
        y_min = int(np.min(outlines[:, 1]))
        y_max = int(np.max(outlines[:, 1]))
        center_x = x_min + (x_max - x_min) // 2
        center_y = y_min + (y_max - y_min) // 2
        r_cell = (x_max - x_min) // 2
        dist = 5

        xx, yy = np.meshgrid(np.arange(x_min, x_max + 1), np.arange(y_min, y_max + 1))
        distances = np.sqrt((xx - center_x) ** 2 + (yy - center_y) ** 2)
        mask_cell = distances < (x_max - x_min) / 2

        masked_frame = img[y_min:y_max + 1, x_min:x_max + 1] * mask_cell
        F_cell = np.sum(masked_frame)
        cnt_cell = np.sum(mask_cell)
        F_cell = F_cell / cnt_cell

        x_min = x_min - dist
        x_max = x_max + dist
        y_min = y_min - dist
        y_max = y_max + dist

        xx, yy = np.meshgrid(np.arange(x_min, x_max + 1), np.arange(y_min, y_max + 1))
        distances = np.sqrt((xx - center_x) ** 2 + (yy - center_y) ** 2)
        mask_all = np.logical_and(distances < (x_max - x_min) / 2, distances > r_cell)

        masked_frame = img[y_min:y_max + 1, x_min:x_max + 1] * mask_all
        F_all = np.sum(masked_frame)
        cnt_all = np.sum(mask_all)
        F_b = F_all / cnt_all

        res = (F_cell - F_b) / F_b
        return res

    def fake_avg(self):
        return 0.9
    def data_handler(self):
        if len(self.img_buffer) == 0:
            return
        else:
            img = self.img_buffer.pop(0)
            if len(self.img_buffer) > 0:
                print('read img, remaining: ', len(self.img_buffer))
            t0 = time.time()

        num = len(self.itemlist)
        data = np.empty((num, 6))
        shape_data = []

        for i in range(num):
            item = self.itemlist[i]
            x = int(item.pos().x())
            y = int(item.pos().y())
            avg = self.extraction_v2(item, img)

            if self.fake:
                if self.frame_count > self.j * 400 + 250 and self.frame_count < self.j * 400 +270:
                    avg = self.fake_avg()

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
            shape_data.extend(item.contours.tolist())

            if item.type == ROIType.CIRCLE:
                type = 1
            else:
                type = 2

            data[i] = np.array([item.id, x, y, type, c_size, avg])

        if self.fake:
            if self.frame_count > self.j * 400 + 250 and self.frame_count < self.j * 400 +270:
                self.j += 1

        if self.decoding:
            if self.decoding_text.isVisible() and time.time() - self.decoding_timer > 1:
                self.decoding_sig.emit(False)
            # print(data[:, 5])
            self.traces = np.vstack((self.traces, data[:, 5]))
            # print(self.traces.shape)
            if self.traces.shape[0] == 30:
                label = self.decoder.inference(self.traces.T)
                if label == 1:
                    self.network_controller.feed()
                    self.decoding_sig.emit(True)
                    self.decoding_timer = time.time()
                self.traces = self.traces[15:, :]
                print(self.traces.shape)

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
        # print(f'recieve extraction: {t2 - t0}\n'
        #       f'recieve saving: {t1 - t2}\n'
        #       f'recieve total: {t1 - t0}')
        # print('recieve time: ', t1 - t0)



