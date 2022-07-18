import sys
from PySide2.QtWidgets import QApplication, QDesktopWidget
from mainwindow import OldWindow #MainWindow
from PySide2.QtCore import QCoreApplication, Qt

if __name__ == "__main__":
	QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
	app = QApplication(sys.argv)
	window = OldWindow() #MainWindow()
	window.show()
	sys.exit(app.exec_())
	
