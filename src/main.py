# This Python file uses the following encoding: utf-8
import sys
sys.path.append('.')
sys.path.append('..')

from PySide2.QtWidgets import QApplication
from mainwindow_ep3_m2_linux_0406 import MainWindow

from PySide2.QtCore import QCoreApplication, Qt

if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

