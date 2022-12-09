from PySide2.QtWidgets import QMainWindow,QApplication, QGraphicsView, QVBoxLayout, QWidget
from PySide2.QtUiTools import QUiLoader
import pyqtgraph as pg

from time import sleep
# import iconlist
import array
import serial
import threading
import numpy as np
import time

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setupUi()
		self.LeverPressure.openPort_Button.clicked.connect(self.openSerialPort)
		self.LeverPressure.pushButton_StartTest.clicked.connect(self.startGraphing)

	def Serial(self):
		i = 0
		while (True):
			n = self.mSerial.inWaiting()
			if (n):
				if self.data != " ":
					dat = int.from_bytes(self.mSerial.readline(1), byteorder='little')  # change format
					n = 0
					print("receive : ", self.data)
					print("dat", dat)
					if dat == 17:
						dat1 = int.from_bytes(self.mSerial.readline(1), byteorder='little')
						dat2 = int.from_bytes(self.mSerial.readline(1), byteorder='little')
						if i < 1000:
							self.data[i] = dat1 * 255 + dat2
							i = i + 1

						else:
							self.data[:-1] = self.data[1:]
							self.data[i - 1] = dat1 * 255 + dat2
					else:
						continue

	def plotData(self):
		# self.curve.setData(self.data)
		# self.curve = self.pw.plot()  # Draw a grap
		self.curve.setData(self.data)

	def startGraphing(self):
		i = 0
		historyLength = 1000  # The length of the abscissa
		a = 0
		self.data = np.zeros(historyLength).__array__('d')  # Set the length of the array

		self.pw = pg.PlotWidget()
		self.LeverPressure.verticalLayout.addWidget(self.pw)

		self.curve = self.pw.plot()  # Draw a grap
		self.curve.setData(self.data)

		th1 = threading.Thread(target=self.Serial)
		th1.start()
		timer = pg.QtCore.QTimer()
		# timer.timeout.connect(self.plotData)  # Refresh data display regularly
		timer.timeout.connect(self.plotData)  # Refresh data display regularly
		timer.start(50)  # How many 'ms' to call once


###################### Open port
	def openSerialPort(self):
		portx = str(self.LeverPressure.comboBox_com.currentText())
		bps = self.LeverPressure.comboBox_baud.currentText()
		print(portx, bps)
		#self.mSerial = serial.Serial(portx, bps)
		self.mSerial = serial.Serial()
		self.mSerial.open()

		if self.mSerial.isOpen():
			print("open success")
			self.mSerial.write("hello".encode())
			self.mSerial.flushInput()
		else:
			print("open failed")
			serial.close()


	def setupUi(self):
		self.LeverPressure = QUiLoader().load('widget_leverpressure.ui')
		self.setCentralWidget(self.LeverPressure)


