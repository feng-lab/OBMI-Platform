from PySide2.QtWidgets import QWidget, QVBoxLayout, QGraphicsLineItem, QGraphicsTextItem, QLabel
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import QMargins, Qt
from PySide2.QtGui import QPen, QBrush, QPainter, QPalette, QColor

# Trace Viewer for displaying trace
# param: brightlist - a list contains all brightness info of each ROI circle
class Traceviewer(QWidget):
    def __init__(self, brightlist, parent=None):
        super().__init__(parent)

        self.viewer = QWidget(parent) # main widget
        self.mainwin = parent
        self.brightlist = brightlist

        # layout setting
        self.layout = QVBoxLayout(self.viewer)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 2, 0, 0)
        self.layout.setSpacing(15)

        self.chartlist = [] # store charts

        self.height = self.viewer.height()
        # draw traces
        self.init_traces()

        # stretch remaining blank
        self.layout.addStretch(1)

        # self.linex = 2

    # def paintEvent(self, event):
    #     qp = QPainter()
    #     qp.setPen(Qt.red)
    #     qp.begin(self)
    #     qp.drawLine(self.linex, 0, self.linex, self.height)
    #     qp.end()

    def moveline(self, pos):
        self.linex = pos.x()
        self.update()

    def init_traces(self):
        i = 1
        for list in self.brightlist:
            self.add_chart(list, "ROI_"+str(i))
            i += 1

    def add_chart(self, list, title=None):
        # series setting
        series = QtCharts.QLineSeries()
        series.setPen(QPen(QBrush(Qt.blue), 1, Qt.SolidLine))
        for i in range(0, len(list)):
            series.append(i, list[i])

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
        #axisY.setRange(0, 255)
        #axisY.setVisible(False)
        axisY.setTickCount(2)
        axisY.setLabelFormat("%d")
        chart.addAxis(axisY, Qt.AlignRight)
        series.attachAxis(axisY)

        axisX = QtCharts.QValueAxis()
        #axisX.setVisible(False)
        axisX.setTickCount(5)
        axisX.setLabelFormat("%d")
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        # chart view setting
        #chart_view = QtCharts.QChartView(chart)
        chart_view = Chartview(chart, self.chartlist, self)
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
            for chart in self.chartlist:
                chart.chart().axisX().setRange(self.min, self.max)

    def wheelEvent(self, event):
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