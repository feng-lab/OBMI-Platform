import time

import cv2
import torch
from PySide2 import QtCore
from PySide2.QtWidgets import QWidget, QVBoxLayout, QGraphicsLineItem, QGraphicsTextItem, QLabel
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import QMargins, Qt, QTimer, QThread
from PySide2.QtGui import QPen, QBrush, QPainter, QPalette, QColor

import numpy as np
import h5py
import datetime
# Trace Viewer for displaying trace
# param: brightlist - a list contains all brightness info of each ROI circle
from src.ROI import ROIType

from utils import func_cost


class OnTraceviewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.viewer = QWidget(parent) # main widget
        self.mainwin = parent
        self.itemlist = []
        self.numchart = 0 # number of chart

        self.frame_count = 1 # frame pointer for current frame

        self.editlock = False

        # layout setting
        self.layout = QVBoxLayout(self.viewer)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 2, 0, 0)
        self.layout.setSpacing(15)


        self.chartlist = [] # store charts
        self.pause = False # pause updating series
        self.height = self.viewer.height()

        self.traces = []
        self.window_size = 300
        # draw traces
        # self.init_traces()
        # self.timer_init()
        # parent.on_scope.frameG.connect(self.update_s)
        # stretch remaining blank
        # self.layout.addStretch(1)


    def single_trace_update(self, chartview, trace, avg, frame_index):
        if len(trace) > self.window_size:
            trace.pop(0)
        trace.append(avg)
        chart = chartview.chart()
        chart.series()[0].append(QtCore.QPointF(frame_index, avg))
        chart.axisX().setMax(frame_index)
        chart.max = frame_index
        if frame_index > self.window_size:
            chart.axisX().setMin(frame_index - self.window_size + 1)
            if chart.series()[0].count() > self.window_size:
                chart.series()[0].removePoints(0, chart.series()[0].count() - self.window_size)
        if avg > chart.axisY().max():
            chart.axisY().setMax(avg)
        pass

    # @func_cost
    def full_trace_update(self, avgs, frame_index):
        assert len(avgs) == len(self.chartlist)
        [self.single_trace_update(chart, trace, avg, frame_index) for (chart, trace, avg) in zip(self.chartlist, self.traces, avgs)]



    # def timer_init(self):
    #     # 使用QTimer，2秒触发一次，更新数据
    #     self.timer = QTimer(self)
    #     self.timer.timeout.connect(self.updates)
    #     self.timer.start(200)

    # def recieve_img(self, img):
    #     t0 = time.time()
    #
    #     num = len(self.itemlist)
    #     data = np.empty((num, 6))
    #     contours = []
    #
    #     for i in range(num):
    #         item = self.itemlist[i]
    #         x = int(item.pos().x())
    #         y = int(item.pos().y())
    #         width = int(item.boundingRect().width())
    #         height = int(item.boundingRect().height())
    #
    #         # extract gray value
    #         imgmat = img[y:y+height, x:x+width].flatten()
    #         if torch.cuda.is_available():
    #             imgmat = torch.tensor(imgmat)
    #             item_noise = torch.tensor(item.noise)
    #             item_mat = torch.tensor(item.mat)
    #         else:
    #             item_noise = item.noise
    #             item_mat = item.mat
    #
    #         noise = imgmat * item_noise
    #         noise_exist = (item_noise != 0)
    #         noise_avg = int(noise.sum() / noise_exist.sum())
    #
    #         res = imgmat * item_mat - noise_avg
    #         res[res < 0] = 0
    #         exist = (res != 0)
    #         if exist.sum() == 0:
    #             avg = 0
    #         else:
    #             avg = int(res.sum() / exist.sum())
    #             if noise_avg != 0:
    #                 avg = avg / noise_avg
    #
    #         #data[i] = np.array([item.id, x+width/2, y+height/2, width, avg])
    #
    #         c_size = item.c_size
    #         contours.extend(item.contours.tolist())
    #
    #         if item.type == ROIType.CIRCLE:
    #             type = 1
    #         else:
    #             type = 2
    #
    #         data[i] = np.array([item.id, x, y, type, c_size, avg])
    #
    #         # if i < 5:
    #         #     chart = self.chartlist[i].chart()
    #         #     chart.series()[0].append(QtCore.QPointF(self.frame_count+1, avg))
    #         #     if not self.pause:
    #         #         chart.axisX().setMax(self.frame_count + 1)
    #         #         self.chartlist[i].max = self.frame_count + 1
    #         #         if self.frame_count + 1 > 500:
    #         #             chart.axisX().setMin(self.frame_count + 1 - 499)
    #         #             if chart.series()[0].count() > 500:
    #         #                 chart.series()[0].removePoints(0, chart.series()[0].count() - 500)
    #         #         if avg > chart.axisY().max():
    #         #             chart.axisY().setMax(avg)
    #
    #     t2 = time.time()
    #     str = f'{self.frame_count:06}'
    #     with h5py.File('trace_data_2.h5', 'a') as f:
    #         g = f.create_group(str)
    #         g["image"] = img
    #         g["data"] = data
    #         g["contours"] = np.array(contours)
    #     self.frame_count += 1
    #     t1 = time.time()
    #     print(f'recieve start: {t0}\n'
    #           f'recieve extraction: {t2-t0}\n'
    #           f'recieve saving: {t1-t2}\n'
    #           f'recieve total: {t1-t0}\n'
    #           f'recieve end: {t1}')
    #     #print('recieve time: ', t1 - t0)
    #
    #
    # def updates(self):
    #     if self.editlock:
    #         return
    #
    #     # switch buffer
    #     index = self.buffer_index
    #     if index == 0:
    #         self.buffer_index = 1
    #         buffer = self.buffer[0]
    #     else:
    #         self.buffer_index = 0
    #         buffer = self.buffer[1]
    #
    #     t0 = time.time()
    #     bufferlength = len(buffer)
    #     print('buffer len: ', bufferlength)
    #     for i in range(len(self.itemlist)):
    #         item = self.itemlist[i]
    #         x = int(item.pos().x())
    #         y = int(item.pos().y())
    #         width = int(item.rect().width())
    #         height = int(item.rect().height())
    #         avgs = []
    #
    #         for j in range(bufferlength):
    #             imgmat = buffer[j][y:y+height, x:x+width]
    #             noise = imgmat * item.noise
    #             noise_exist = (item.noise != 0)
    #             noise_avg = int(noise.sum() / noise_exist.sum())
    #
    #             res = imgmat * item.mat - noise_avg
    #             res[res < 0] = 0
    #             exist = (res != 0)
    #             if exist.sum() == 0:
    #                 avg = 0
    #             else:
    #                 avg = int(res.sum() / exist.sum())
    #             avgs.append(QtCore.QPointF(self.frame_count + j, avg))
    #
    #         chart = self.chartlist[i].chart()
    #         chart.series()[0].append(avgs)
    #         if not self.pause:
    #             chart.axisX().setMax(self.frame_count + bufferlength)
    #             self.chartlist[i].max = self.frame_count + bufferlength
    #             if self.frame_count + bufferlength > 500:
    #                 chart.axisX().setMin(self.frame_count + bufferlength - 499)
    #                 if chart.series()[0].count() > 500:
    #                     chart.series()[0].removePoints(0, chart.series()[0].count() - 500)
    #
    #
    #     self.frame_count += bufferlength
    #     print('fc: ', self.frame_count)
    #     # for img in buffer:
    #     #     self.update_chart(img)
    #     self.buffer[index] = []
    #     t1 = time.time()
    #     print('updates time: ', t1-t0)

    def remove_trace(self, circle):
        self.editlock = True
        index = self.itemlist.index(circle)
        chart = self.chartlist[index]
        self.layout.removeWidget(chart)
        self.chartlist.remove(chart)
        self.itemlist.remove(circle)
        self.traces.pop(index)
        self.editlock = False

    def add_trace(self, circle):
        self.numchart += 1
        self.add_chart(circle.name)
        self.itemlist.append(circle)
        self.traces.append([])

    # series update
    # def update_s(self, img):
    #     t0 = time.time()
    #     for i in range(0, self.numchart):
    #         total = 0
    #         for pos in self.rangelist[i]:
    #             total += img[pos[1]][pos[0]]
    #         avg = total / len(self.rangelist[i])
    #         chart = self.chartlist[i].chart()
    #         chart.series()[0].append(self.frame_count, int(avg))
    #         if not self.pause:
    #             chart.axisX().setMax(self.frame_count+1)
    #             self.chartlist[i].max = self.frame_count + 1
    #             if self.frame_count > 500:
    #                 chart.axisX().setMin(self.frame_count - 499)
    #     self.frame_count += 1
    #     t1 = time.time()
    #     print("update_s process time: ", t1 - t0)
    #     print(f'update_s frame {self.frame_count} done at {t1}')
    #
    # def update_chart(self, img):
    #     for i in range(len(self.itemlist)):
    #         rect = self.itemlist[i].rect()
    #         x = int(rect.x())
    #         y = int(rect.y())
    #         width = int(rect.width())
    #         height = int(rect.height())
    #         imgmat = img[y:y+height, x:x+width]
    #         res = imgmat*self.itemlist[i].mat
    #         exist = (self.itemlist[i].mat != 0)
    #         avg = res.sum()/exist.sum()
    #         chart = self.chartlist[i].chart()
    #         chart.series()[0].append(self.frame_count, int(avg))
    #         if not self.pause:
    #             chart.axisX().setMax(self.frame_count + 1)
    #             self.chartlist[i].max = self.frame_count + 1
    #             if self.frame_count > 500:
    #                 chart.axisX().setMin(self.frame_count - 499)
    #                 chart.series()[0].remove(0)
    #
    #     self.frame_count += 1


    def add_chart(self, title=None):
        # series setting
        series = QtCharts.QLineSeries()
        series.setPen(QPen(QBrush(Qt.blue), 2, Qt.SolidLine))
        series.setUseOpenGL(True)

        # chart setting
        chart = QtCharts.QChart()
        chart.addSeries(series)
        chart.legend().setVisible(False)
        chart.layout().setContentsMargins(0, 0, 0, 0)
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.setBackgroundRoundness(0)

        if title:
            chart.setTitle(title)

        # axis setting
        axisY = QtCharts.QValueAxis()
        axisY.setRange(0, 0.1)
        #axisY.setVisible(False)
        axisY.setTickCount(2)
        axisY.setLabelFormat("%f")
        chart.addAxis(axisY, Qt.AlignRight)
        series.attachAxis(axisY)

        axisX = QtCharts.QValueAxis()
        #axisX.setVisible(False)
        axisX.setRange(0, 1)
        axisX.setTickCount(5)
        axisX.setLabelFormat("%d")
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        # chart view setting
        chart_view = QtCharts.QChartView(chart)
        # chart_view = Chartview(chart, self.chartlist, self)
        chart_view.setFixedWidth(408)
        chart_view.setFixedHeight(100)
        #chart_view.setStyleSheet("border: 0.5px solid black;")
        self.chartlist.append(chart_view)
        self.layout.addWidget(chart_view)


class Chartview(QtCharts.QChartView):
    def __init__(self, chart, chartlist, parent = None):
        super().__init__(chart, parent)
        self.curChart = chart
        self.chartlist = chartlist
        self.mousePressed = False
        self.mousePos = None
        self.min = chart.axisX().min()
        self.max = chart.axisX().max()
        self.parent = parent

        # self.line = QGraphicsLineItem(self.chart)
        # self.text = QGraphicsTextItem(self.chart)
        # self.line.setLine(0, 0, 0, self.height())
        # self.text.setPos((0, 0))
        # self.text.setPlainText('frame:0')
        # self.line.show()
        # self.text.show()


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mousePressed = True
            self.parent.pause = True
            self.mousePos = event.pos()
            self.parent.moveline(event.pos())


    def mouseMoveEvent(self, event):
        curPos = event.pos()
        if self.mousePressed:
            offset = curPos.x() - self.mousePos.x()
            self.mousePos = curPos

            min = self.curChart.axisX().min()
            max = self.curChart.axisX().max()

            if min - offset < self.min:
                offset = min - self.min

            if max - offset > self.max:
                offset = max - self.max

            for chart in self.chartlist:
                chart.chart().axisX().setRange(min - offset, max - offset)

    def mouseReleaseEvent(self, event):
        self.mousePressed = False
        if event.button() == Qt.RightButton:
            self.parent.pause = False
            for chart in self.chartlist:
                chart.chart().axisX().setRange(self.min, self.max)


    def wheelEvent(self, event):
        self.parent.pause = True
        curPos = event.pos()
        curVal = self.curChart.mapToValue(curPos)

        factor = 1.5 # zoom multiplier
        central = curVal.x()

        min = self.curChart.axisX().min()
        max = self.curChart.axisX().max()

        if event.delta() > 0:
            leftoffset = 1.0 / factor * (central - min)
            rightoffset = 1.0 / factor * (max - central)
        else:
            leftoffset = factor * (central - min)
            rightoffset = factor * (max - central)

        if central - leftoffset < self.min or central + rightoffset > self.max:
            leftoffset = central - self.min
            rightoffset = self.max - central

        for chart in self.chartlist:
            chart.chart().axisX().setRange(central - leftoffset, central + rightoffset)