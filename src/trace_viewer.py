import numpy as np
from PySide2.QtWidgets import QWidget, QVBoxLayout, QGraphicsLineItem
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import QMargins, Qt
from PySide2.QtGui import QPen, QBrush
from pyqtgraph import PlotWidget
import pyqtgraph as pg


pg.setConfigOption('background', 'w')
# Trace Viewer for displaying trace
# param: brightlist - a list contains all brightness info of each ROI circle
class Traceviewer(pg.GraphicsLayoutWidget):
    def __init__(self, rois, brightlist, parent=None):
        super().__init__(parent)

        self.plot_item = self.addPlot()
        self.plot_item.hideAxis('left')

        self.gap = 0.5
        self.brightlist = brightlist
        self.rois = rois
        self.trace_size = 5

        self.init_trace()

    def init_trace(self):
        for i, data in enumerate(self.brightlist):
            curve = pg.PlotCurveItem(np.linspace(0, len(data), len(data)), data, pen=pg.mkPen(color=pg.intColor(5), width=2))
            self.plot_item.addItem(curve)
            curve.setPos(0, -i * self.gap)

            label = pg.TextItem(self.rois[i].name, color=pg.intColor(6))
            label.setParentItem(curve)
            label.setPos(0, 0.2)

        self.plot_item.autoRange()
        if len(self.rois) > self.trace_size:
            self.plot_item.setYRange(-self.trace_size * self.gap + 0.4, 0.3)
        else:
            self.plot_item.setYRange(-len(self.rois) * self.gap + 0.4, 0.3)

# class Traceviewer(QWidget):
#     def __init__(self, brightlist, parent=None):
#         super().__init__(parent)
#
#         self.viewer = QWidget(parent) # main widget
#         self.mainwin = parent
#         self.brightlist = brightlist.reverse()
#
#         # layout setting
#         self.layout = QVBoxLayout(self.viewer)
#         self.setLayout(self.layout)
#         self.layout.setContentsMargins(0, 2, 0, 0)
#         self.layout.setSpacing(15)
#
#         self.chartlist = [] # store charts
#
#         # draw traces
#         self.init_traces()
#
#         # stretch remaining blank
#         self.layout.addStretch(1)
#
#     def init_traces(self):
#         i = 1
#         for list in self.brightlist:
#             self.add_chart(list, "ROI_"+str(i))
#             i += 1
#
#     def add_chart(self, list, title=None):
#         # series setting
#         series = QtCharts.QLineSeries()
#         series.setPen(QPen(QBrush(Qt.blue), 1, Qt.SolidLine))
#         for i in range(0, len(list)):
#             series.append(i, list[i])
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
#         #axisY.setRange(0, 255)
#         #axisY.setVisible(False)
#         axisY.setTickCount(2)
#         axisY.setLabelFormat("%.2f")
#         chart.addAxis(axisY, Qt.AlignRight)
#         series.attachAxis(axisY)
#
#         axisX = QtCharts.QValueAxis()
#         axisX.setVisible(True)
#         axisX.setLabelFormat("%d")
#         chart.addAxis(axisX, Qt.AlignBottom)
#         series.attachAxis(axisX)
#
#         # chart view setting
#         #chart_view = QtCharts.QChartView(chart)
#         chart_view = Chartview(chart, self.chartlist)
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
#
#     def mousePressEvent(self, event):
#         if event.button() == Qt.LeftButton:
#             self.mousePressed = True
#             self.mousePos = event.pos()
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
#             for chart in self.chartlist:
#                 chart.chart().axisX().setRange(self.min, self.max)
#
#     def wheelEvent(self, event):
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