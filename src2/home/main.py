import sys
from PySide2.QtWidgets import QApplication, QDesktopWidget
from mainwindow import OldWindow #MainWindow
from PySide2.QtCore import QCoreApplication

if __name__ == "__main__":

	app = QApplication(sys.argv)
	window = OldWindow() #MainWindow()
	window.show()
	sys.exit(app.exec_())
	
