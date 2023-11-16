import time

import cv2
import torch
from PySide2 import QtCore
from PySide2.QtWidgets import QWidget, QVBoxLayout, QGraphicsLineItem, QGraphicsTextItem, QLabel
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import QMargins, Qt, QTimer, QThread
from PySide2.QtGui import QPen, QBrush, QPainter, QPalette, QColor

import pyqtgraph as pg

import numpy as np
import h5py
import datetime
# Trace Viewer for displaying trace
# param: brightlist - a list contains all brightness info of each ROI circle
from src.ROI import ROIType

from utils import func_cost
pg.setConfigOption('background', 'w')

class OnTraceviewer(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # self.central_widget = pg.GraphicsLayoutWidget(parent=self)

        self.plot_item = self.addPlot()

        self.plot_item.hideAxis('left')

        self.gap = 0.5
        self.num_curves = 0
        self.curves = []
        self.itemlist = []
        self.trace_data = []
        self.window_size = 400
        self.trace_size = 10

        self.plot_item.setXRange(0, self.window_size)


        # Create some example data and names
        # num_curves = 5
        # num_points = 100
        # x = np.linspace(0, 10, num_points)
        # data = [np.sin(x + i) + i for i in range(num_curves)]
        # curve_names = [f"Curve {i}" for i in range(num_curves)]
        #
        # # Set the curve colors and gaps
        # colors = [pg.intColor(i, num_curves) for i in range(num_curves)]
        # gaps = 3  # Adjust the gap as needed
        #
        # for i in range(num_curves):
        #     curve = pg.PlotCurveItem(x, data[i], pen=pg.mkPen(color=colors[i], width=2))
        #     curve.setPos(0, i * gaps)  # Adjust the y-position for each curve
        #     self.plot_item.addItem(curve)
        #
        #     # Add label for each curve
        #     label = pg.TextItem(curve_names[i], color=colors[i])
        #
        #     label.setParentItem(curve)
        #     label.setPos(0, 2 + i)
        #     # label.setTransform(pg.Transform.rotate(180))  # Rotate the label
        #     # label.setPos(-0.1, i * gaps)  # Adjust position
        #     label.setText(curve_names[i])

    def single_trace_update(self, i, avg, frame_index):
        curve = self.curves[i]
        trace = self.trace_data[i]
        trace.append(avg)
        if len(trace) > self.window_size:
            trace.pop(0)

        curve.setData(np.linspace(0, len(trace), len(trace)), trace)


    def full_trace_update(self, avgs, frame_index):
        [self.single_trace_update(i, avg, frame_index) for (i, avg) in enumerate(avgs)]
        # if frame_index > self.window_size:
        #     self.plot_item.setXRange(frame_index-self.window_size, frame_index+self.window_size)

    def add_trace(self, roi):
        curve = pg.PlotCurveItem([0], [0], pen=pg.mkPen(color=pg.intColor(5), width=2))
        self.plot_item.addItem(curve)

        label = pg.TextItem(roi.name, color=pg.intColor(6))
        label.setParentItem(curve)
        label.setPos(0, 0.2)

        self.num_curves += 1
        self.curves.append(curve)
        self.itemlist.append(roi)
        self.trace_data.append([])
        self.resetPos()
        self.plot_item.setYRange(-self.num_curves * self.gap + 0.4, 0.3)

    def remove_trace(self, roi):
        i = self.itemlist.index(roi)
        self.itemlist.remove(roi)
        curve = self.curves.pop(i)
        self.plot_item.removeItem(curve)
        self.trace_data.pop(i)
        self.num_curves -= 1

        self.resetPos()
        self.plot_item.setYRange(-self.num_curves * self.gap + 0.4, 0.3)

    def resetPos(self):
        for i, curve in enumerate(self.curves):
            curve.setPos(0, -i * self.gap)


# class OnTraceviewer(QWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#
#         self.viewer = QWidget(parent) # main widget
#         self.mainwin = parent
#         self.itemlist = []
#         self.numchart = 0 # number of chart
#
#         self.frame_count = 1 # frame pointer for current frame
#
#         self.editlock = False
#
#         # layout setting
#         self.layout = QVBoxLayout(self.viewer)
#         self.setLayout(self.layout)
#         self.layout.setContentsMargins(0, 2, 0, 0)
#         self.layout.setSpacing(15)
#
#
#         self.chartlist = [] # store charts
#         self.pause = False # pause updating series
#         self.height = self.viewer.height()
#
#         self.traces = []
#         self.window_size = 300
#         # draw traces
#         # self.init_traces()
#         # self.timer_init()
#         # parent.on_scope.frameG.connect(self.update_s)
#         # stretch remaining blank
#         # self.layout.addStretch(1)
#
#     def single_trace_update(self, chartview, trace, avg, frame_index):
#         if len(trace) > self.window_size:
#             trace.pop(0)
#         trace.append(avg)
#         chart = chartview.chart()
#         chart.series()[0].append(QtCore.QPointF(frame_index, avg))
#         chart.axisX().setMax(frame_index)
#         chart.max = frame_index
#         if frame_index > self.window_size:
#             chart.axisX().setMin(frame_index - self.window_size + 1)
#             if chart.series()[0].count() > self.window_size:
#                 chart.series()[0].removePoints(0, chart.series()[0].count() - self.window_size)
#         if avg > chart.axisY().max():
#             chart.axisY().setMax(avg)
#         pass
#
#     # @func_cost
#     def full_trace_update(self, avgs, frame_index):
#         assert len(avgs) == len(self.chartlist)
#         [self.single_trace_update(chart, trace, avg, frame_index) for (chart, trace, avg) in zip(self.chartlist, self.traces, avgs)]
#
#
#     def remove_trace(self, circle):
#         self.editlock = True
#         index = self.itemlist.index(circle)
#         chart = self.chartlist[index]
#         self.layout.removeWidget(chart)
#         self.chartlist.remove(chart)
#         self.itemlist.remove(circle)
#         self.traces.pop(index)
#         self.editlock = False
#
#     def add_trace(self, circle):
#         self.numchart += 1
#         self.add_chart(circle.name)
#         self.itemlist.append(circle)
#         self.traces.append([])
#
#     def add_chart(self, title=None):
#         # series setting
#         series = QtCharts.QLineSeries()
#         series.setPen(QPen(QBrush(Qt.blue), 2, Qt.SolidLine))
#         series.setUseOpenGL(True)
#
#         # chart setting
#         chart = QtCharts.QChart()
#         chart.addSeries(series)
#         chart.legend().setVisible(False)
#         chart.layout().setContentsMargins(0, 0, 0, 0)
#         chart.setMargins(QMargins(0, 0, 0, 0))
#         chart.setBackgroundRoundness(0)
#
#         if title:
#             chart.setTitle(title)
#
#         # axis setting
#         axisY = QtCharts.QValueAxis()
#         axisY.setRange(0, 0.1)
#         #axisY.setVisible(False)
#         axisY.setTickCount(2)
#         axisY.setLabelFormat("%f")
#         chart.addAxis(axisY, Qt.AlignRight)
#         series.attachAxis(axisY)
#
#         axisX = QtCharts.QValueAxis()
#         #axisX.setVisible(False)
#         axisX.setRange(0, 1)
#         axisX.setTickCount(5)
#         axisX.setLabelFormat("%d")
#         chart.addAxis(axisX, Qt.AlignBottom)
#         series.attachAxis(axisX)
#
#         # chart view setting
#         chart_view = QtCharts.QChartView(chart)
#         # chart_view = Chartview(chart, self.chartlist, self)
#         chart_view.setFixedWidth(408)
#         chart_view.setFixedHeight(100)
#         #chart_view.setStyleSheet("border: 0.5px solid black;")
#         self.chartlist.append(chart_view)
#         self.layout.addWidget(chart_view)


# class Chartview(QtCharts.QChartView):
#     def __init__(self, chart, chartlist, parent = None):
#         super().__init__(chart, parent)
#         self.curChart = chart
#         self.chartlist = chartlist
#         self.mousePressed = False
#         self.mousePos = None
#         self.min = chart.axisX().min()
#         self.max = chart.axisX().max()
#         self.parent = parent
#
#         # self.line = QGraphicsLineItem(self.chart)
#         # self.text = QGraphicsTextItem(self.chart)
#         # self.line.setLine(0, 0, 0, self.height())
#         # self.text.setPos((0, 0))
#         # self.text.setPlainText('frame:0')
#         # self.line.show()
#         # self.text.show()
#
#
#     def mousePressEvent(self, event):
#         if event.button() == Qt.LeftButton:
#             self.mousePressed = True
#             self.parent.pause = True
#             self.mousePos = event.pos()
#             self.parent.moveline(event.pos())
#
#
#     def mouseMoveEvent(self, event):
#         curPos = event.pos()
#         if self.mousePressed:
#             offset = curPos.x() - self.mousePos.x()
#             self.mousePos = curPos
#
#             min = self.curChart.axisX().min()
#             max = self.curChart.axisX().max()
#
#             if min - offset < self.min:
#                 offset = min - self.min
#
#             if max - offset > self.max:
#                 offset = max - self.max
#
#             for chart in self.chartlist:
#                 chart.chart().axisX().setRange(min - offset, max - offset)
#
#     def mouseReleaseEvent(self, event):
#         self.mousePressed = False
#         if event.button() == Qt.RightButton:
#             self.parent.pause = False
#             for chart in self.chartlist:
#                 chart.chart().axisX().setRange(self.min, self.max)
#
#
#     def wheelEvent(self, event):
#         self.parent.pause = True
#         curPos = event.pos()
#         curVal = self.curChart.mapToValue(curPos)
#
#         factor = 1.5 # zoom multiplier
#         central = curVal.x()
#
#         min = self.curChart.axisX().min()
#         max = self.curChart.axisX().max()
#
#         if event.delta() > 0:
#             leftoffset = 1.0 / factor * (central - min)
#             rightoffset = 1.0 / factor * (max - central)
#         else:
#             leftoffset = factor * (central - min)
#             rightoffset = factor * (max - central)
#
#         if central - leftoffset < self.min or central + rightoffset > self.max:
#             leftoffset = central - self.min
#             rightoffset = self.max - central
#
#         for chart in self.chartlist:
#             chart.chart().axisX().setRange(central - leftoffset, central + rightoffset)