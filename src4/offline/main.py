import sys
from PySide2.QtWidgets import QApplication, QDesktopWidget
from mainwindow import MainWindow
from PySide2.QtCore import QCoreApplication, Qt

if __name__ == "__main__":
	QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
	app = QApplication(sys.argv)
	window = MainWindow(indep=True)
	window.show()
	sys.exit(app.exec_())
	
