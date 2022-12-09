# python -m home.main
import sys
from PySide2.QtWidgets import QApplication, QDesktopWidget
from PySide2.QtCore import QCoreApplication, Qt
from home.mainwindow import MainWindow
#from mainwindow import MainWindow

if __name__ == "__main__":
	QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
	app = QApplication(sys.argv)
	window = MainWindow(indep=False)
	#window = OldWindow()
	window.show()
	sys.exit(app.exec_())
	
