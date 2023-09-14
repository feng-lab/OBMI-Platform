# This Python file uses the following encoding: utf-8
import sys
sys.path.append('.')
sys.path.append('..')
from PySide2.QtWidgets import QApplication, QDesktopWidget
from mainwindow_ep3_m2_linux_0406 import MainWindow ##, MainWindow2 ##ep2 ## ~ep3 0316

from PySide2.QtCore import QCoreApplication, Qt

if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)

    ## QCoreApplication.setLibraryPaths(['/HATA/hdocuments/program/qt/5.15.0/Src/qtmultimedia'])

    window = MainWindow()
    window.show()

    #gui = MainWindow2()
    #gui.show()

    sys.exit(app.exec_())
    #app.exec_()

###
# pyside2
# opencv-python
# pandas
# comtypes


## tab movement - check status/save status function ?
## tab feature 정리 / 역할 정의 


#### chart - realtime 관련 update 필요
#### usb 관련 연계하여 작업, button으로 신호대체 고려
### 나머지 부분은 cpp 참고하여 변경.

## 일단은 fin_record_status에 따라 
## 양측다 재 활성화. 비활성화시 양측다 실시

## recording시 둘 다 turn on 상태여야 함으로 되어있음. 


# 현재 레코딩 정책:
# addWidget***
# 값들 여러가지 -  data 만들기. table


# --- td ---
# setEnable() -true -false / setDisable 0715
# drop frame, insert
# thread problem

# record - save, format
# save-aquisition tab change value - check 
# qchart

# thread -> multiprocessing

# === d ===
# led problem
# gain


#### requirements
## pyside2
## opencv-python
## pandas
## comtypes
