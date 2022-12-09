import sys
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QDesktopWidget
from __mainwindow import MainWindow #MainWindow
import threading
import pyqtgraph as pg

if __name__ == "__main__":

	app = QApplication(sys.argv)
	window = MainWindow() #MainWindow()
	window.show()


	sys.exit(app.exec_())


	


