import sys
from PySide2.QtWidgets import QApplication, QDesktopWidget
from mainwindow import MainWindow ## MainWindow ##
from PySide2.QtCore import QCoreApplication

if __name__ == "__main__":

	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec_())
	
