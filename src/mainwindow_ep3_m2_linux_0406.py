import h5py
import numpy
import scipy
import torch
from PySide2.QtWidgets import (QMainWindow, QSlider, QFileDialog, QTableWidget, QTableWidgetItem,
                               QWidget, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLayout,
                               QHBoxLayout, QLabel)
from PySide2 import QtCore, QtGui
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import QObject, Signal, Slot, QThread

from PySide2.QtUiTools import QUiLoader  ### +++++++++++++++++++++++++++++++++++++

from PySide2.QtWidgets import QApplication, QDesktopWidget  #
from PySide2.QtCore import QFile  #

##for ui
from PySide2 import QtWidgets

## for media
### from PySide2.QtMultimedia import QMediaPlayer
### from PySide2.QtMultimediaWidgets import QVideoWidget
####   from PySide2.QtMultimedia.QMediaPlayer

import os
from PySide2.QtCore import QUrl, Qt, QSize

## from ui_mainwindow3 import Ui_MainWindow ## - 1


## from ui_mainwindow6 import Ui_MainWindow ############----------------------------++++
# from ui_mainwindow7 import Ui_MainWindow ############----------------------------++++ 0316


from capture_thread import VideoSavingStatus, CaptureThread
import cv2, random
import platform
from datetime import datetime

# from test_chart2 import make_graph
import time
import numpy as np

### lever -- chart------------
import pandas as pd

### vplayer
from pygrabber.dshow_graph import FilterGraph
from ROI import ROI, ROIType, readImagejROI

from src.data_receiver import DataReceiver, ReceiverThread
from src.network_controller import NetworkController
from vplayer import VPlayer, VPlayerStatus

## camera number
## from __future__ import print_function
## from pygrabber.dshow_graph import FilterGraph ### and get_devlist()


## status and log
from PySide2.QtWidgets import QMessageBox, QDialog
from PySide2.QtUiTools import QUiLoader

## motion correction
from mccc import MCC

from online_player import OPlayer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()  ## //
        import threading
        print("main thread:", threading.get_ident())
        self.timermode = False
        self.cameraID = 0
        # - self.ui = Ui_MainWindow() ## ###+++++++++

        self.setupUi()  ############################ +------
        ## self.gh = make_graph()
        # - self.ui.setupUi(self) ## ----------------

        ## window coordinate
        rect = self.frameGeometry()  # .center
        centerPoint = QDesktopWidget().availableGeometry().center()
        rect.moveCenter(centerPoint)
        self.move(rect.topLeft())
        ## print('rect', rect)

        ## xx self.ui.mapToGlobal(QtCore.QPoint(0, 0))

        self.capturer = None  #
        self.capturer2 = None

        self.roi_clicked = None
        self.data_lock = QtCore.QMutex()  # thread-vari.

        self.MC = None
        self.decoder = None

        self.rt = False
        self.network_controller = None

        ## Behavior Camera Connection
        self.ui.connectBehaviorCameraButton.clicked.connect(self.connect_behavior_camera_button_clicked)
        self.ui.recordButton.clicked.connect(self.recording_start_stop)
        #### self.ui.screenShotButton.clicked.connect(self.save_screen_shot)

        ## Scope Camera Connection
        self.ui.connectScopeCameraButton.clicked.connect(self.connect_scope_camera_button_clicked)

        ## slider movement - (class/

        self.ui.exposureSliderBCam.valueChanged.connect(
            self.move_slider1)  # self.ui.exposureValueBCam, self.ui.exposureSliderBCam.value
        self.ui.exposureValueBCam.returnPressed.connect(
            self.slider_box1)  ## if get value  #self.ui.exposureValueBCam, self.ui.exposureSliderBCam
        # self.ui.exposureValueBCam.valueChanged.connect(self.move_slider)
        # self.ui.exposureSliderBCam.mouseMoveEvent(self.move_slider)
        ## self.ui.exposureSliderBCam.value()
        # valueChanged/ mouseMoveEvent/ sliderMoved / line-edit : (returnPressed | textChanged)

        ## exposure
        ##self.capturer.exposure_status =

        ## slider - need function

        ## visualization slider | brightness & Constrast
        self.ui.visualBrightnessSlider.valueChanged.connect(self.move_slider2)
        self.ui.visualBrightnessValue.returnPressed.connect(self.slider_box2)

        self.ui.visualContrastSlider.valueChanged.connect(self.move_slider3)
        self.ui.visualContrastValue.returnPressed.connect(self.slider_box3)

        ## overlay slider
        self.ui.overlaySlider.valueChanged.connect(self.move_slider4)
        self.ui.overlayValue.returnPressed.connect(self.slider_box4)

        ## scope LED slider
        self.ui.scopeLEDslider.valueChanged.connect(self.move_slider5)
        self.ui.scopeLEDvalue.returnPressed.connect(self.slider_box5)

        ## scope Gain slider
        self.ui.scopeGainSlider.valueChanged.connect(self.move_slider6)
        self.ui.scopeGainValue.returnPressed.connect(self.slider_box6)

        # todo: check point
        ## scope FR slider
        self.ui.scopeFocusSlider.valueChanged.connect(self.move_slider7)
        self.ui.scopeFocusValue.returnPressed.connect(self.slider_box7)
        # self.fvalue = [5, 10, 15, 20, 30, 60]
        # self.ui.scopeFRslider.valueChanged.connect(self.move_slider7)
        # self.ui.scopeFRvalue.returnPressed.connect(self.slider_box7)
        #
        # ## scope exposure slider
        # self.ui.scopeExposureSlider.valueChanged.connect(self.move_slider8)
        # self.ui.scopeExposureValue.returnPressed.connect(self.slider_box8)


        ## scope Exposuretime Slider
        #### self.ui.scopeETslider.valueChanged.connect(self.move_slider9)
        #### self.ui.scopeETvalue.returnPressed.connect(self.slider_box9)

        self.ui.FRcomboBox.currentIndexChanged.connect(self.fpsBox)

        ##------------project name----------- home tab ---------

        n_date = datetime.now()
        self.project_name = n_date.strftime("%Y-%m-%d")
        ## print(self.project_name)

        self.ui.lineEdit.setText(self.project_name)

        ##------------file window------------ home tab ---------
        self.ui.homeBrowseButton.clicked.connect(self.selectD)  ## browse button (76)
        self.save_path = ""
        self.user_path = False

        # self.ui.homeSaveButton.clicked.connect(self.push_dir) ## send button (75)
        ## self.ui.lineEdit.textChanged.connect(self.project_name = self.self)

        ##------------new project---------------
        self.ui.pushButton.clicked.connect(self.button_new)

        ##------------project load---------------
        self.ui.pushButton_8.clicked.connect(self.button_load)

        ##------------project save---------------
        self.ui.homeSaveButton.clicked.connect(self.button_save)
        self.ui.pushButton_9.clicked.connect(self.button_save)

        ##------------recent file----------------
        self.ui.pushButton_10.clicked.connect(self.button_recentfile)

        ##------------project option-------------
        self.ui.pushButton_11.clicked.connect(self.button_option)

        self.format_list = ["wmv", "avi", "mp4", "tiff"]
        self.save_format = ""

        ##------------file save---------
        self.ui.comboBox.currentIndexChanged.connect(self.format_change)  ##

        ##------------hide--------------------
        ## leverpressure
        self.ui.pushButton_22.clicked.connect(self.leverP_vi)
        self.leverpVS = True
        ## behaviorcamera
        self.ui.pushButton_21.clicked.connect(self.behavP_vi)
        self.behavPVS = True
        ## scopecamera
        self.ui.pushButton_20.clicked.connect(self.scopeP_vi)
        self.scopeVS = True

        ## ----lever pressure 2
        self.ui.pushButton_17.clicked.connect(self.leverP_rec)
        self.leverP_recVS = True

        ## -- window size width
        self.temp_width = 0
        self.pl_width = 0

        self.pl_width2 = 0

        ### --- recording ------ and UI (temporary)

        ## edit ui - player1
        ## self.ui.pushButton_55.setText('OK')
        ## self.ui.pushButton_56.setText('Next')
        ## self.ui.pushButton_49.setText('play')
        self.ui.pushButton_58.setText('stop')

        ## player1
        self.player = None
        self.fin_record_status = False

        self.s_fps = 0.0
        self.s_fps_up = False
        self.e_timer = None
        self.s_total = 0
        self.s_totalframe = 0
        self.present_time = 0

        ## player2
        self.player2 = None
        self.fin_record_status2 = False  ##- next function

        self.s_total2 = 0
        self.s_totalframe2 = 0
        self.present_time2 = 0

        ## self.ui.statusbar.showMessage('ready')
        ## self.statusbar().showMessage('ready')

        # manual ROI
        self.filter = None
        self.on_filter = None
        self.ontrace_viewer = None

        ## self.ui.horizontalSlider_3.sliderReleased.connect(self.slider_value_changed)
        # self.ui.horizontalSlider_3.valueChanged.connect(self.slider_value_changed)
        ##        self.frame_count = 0
        ## time domain으로 --
        ## self.p_timer = QtCore.QTimer()
        ##self.p_timer.timeout.connect(self.count_player)

        ## valuse label sync

        ## self.ui.horizontalSlider_3.valueChanged.connected()## VPlayerStatus.MOVING-STARTING -- just value set, even, )
        # self.ui.pushButton_49.clicked.connect(self.play_button_clicked)## VPlayerStatus.-- start to pause / pause to start)
        # self.ui.pushButton_58.clicked.connect(self.stop_button_clicked)## VPlayerStatus.-- stop>start, slider move)
        # self.ui.pushButton_55.clicked.connect(self.play_finished)
        # ## self.ui.pushButton_58.clicked.connect(self.player_)
        # self.ui.pushButton_56.clicked.connect(self.after_player)

        ## self.player_view = self.ui.graphicsView_5 --
        self.player_scene = QGraphicsScene()
        self.ui.graphicsView_5.setScene(self.player_scene)  ##-
        self.player_view = None
        self.player_view = QGraphicsView(self.player_scene, parent=self.ui.graphicsView_5)  ##ui.widget_46)
        self.ui.graphicsView_5.setStyleSheet("background-color: rgb(0,0,0);")  # *# ##-

        self.player_view_item_i = QGraphicsPixmapItem()
        self.player_scene.addItem(self.player_view_item_i)

        ## offline processing tab --------------------------------------------------------------

        self.ui.connectBehaviorCameraButton_2.clicked.connect(self.load_video)  ### UI - need to change the name
        self.open_video_path = ''

        self.ui.LoadRoi.clicked.connect(self.load_roi)
        self.ui.LoadRoi_2.clicked.connect(self.load_on_roi)
        
        ## second player scene

        ## self.ui.scope_camera_view_item_2 = QtWidgets.QWidget(self.ui.widget_46) ##+ edit ui
        ## self.ui.scope_camera_view_item_2.setMinimumSize(QtCore.QSize(917,585))
        ## self.ui.horizontalLayout_2.addWidget(self.ui.scope_camera_view_item_2)

        self.player_scene2 = QGraphicsScene()
        self.ui.scope_camera_view_item_2.setScene(self.player_scene2)  ##-
        self.player_view2 = None

        self.ui.scope_camera_view_item_2.setStyleSheet("background-color: rgb(0,0,0);")
        self.player_view_item_i2 = QGraphicsPixmapItem()
        self.player_scene2.addItem(self.player_view_item_i2)

        self.ui.pushButton_2.clicked.connect(self.play_button_clicked2)
        self.ui.speed1x.clicked.connect(self.speed_1x)
        self.ui.speed2x.clicked.connect(self.speed_2x)
        self.ui.speed3x.clicked.connect(self.speed_3x)
        self.ui.speed5x.clicked.connect(self.speed_5x)

        ## player2 slider
        self.ui.horizontalSlider_10.sliderPressed.connect(self.player2slider_pressed)
        self.ui.horizontalSlider_10.valueChanged.connect(self.player2slider_valueChanged)
        self.ui.horizontalSlider_10.sliderReleased.connect(self.player2slider_released)

        ## grid layout ~

        self.ui.pushButton_30.clicked.connect(self.player2_onoff)
        self.p2oo_st = True

        ##      ## online processing tab -----------------------------------------------------------------

        # scope connect
        self.ui.connectScopeCameraButton_2.clicked.connect(self.online_scope)  ## saved 영상으로 일단 대체

        ## scope LED slider
        self.ui.scopeLEDslider_2.valueChanged.connect(self.move_LEDslider2)
        self.ui.scopeLEDvalue_2.returnPressed.connect(self.LEDslider2_box)

        ## scope Gain slider
        self.ui.scopeGainSlider_2.valueChanged.connect(self.move_Gslider2)
        self.ui.scopeGainValue_2.returnPressed.connect(self.Gslider2_box)

        ## scope FR box
        self.ui.FRcomboBox_2.currentIndexChanged.connect(self.fpsBox_2)

        ## scope focus slider
        self.ui.scopeFocusSlider_2.valueChanged.connect(self.move_Fslider2)
        self.ui.scopeFocusValue_2.returnPressed.connect(self.Fslider2_box)

        # check box check
        # self.ui.checkBox_7

        # pre-processing
        self.ui.connectBehaviorCameraButton_7.clicked.connect(self.pre_process)

        # auto ROI
        self.ui.connectBehaviorCameraButton_8.clicked.connect(self.on_auto_roi)

        # real-time process
        self.ui.connectBehaviorCameraButton_9.clicked.connect(self.rt_process)

        self.on_scope = None

        self.on_data_lock = QtCore.QMutex()

        ## on player
        self.onplayer_scene = QGraphicsScene()
        self.ui.scope_camera_view_item_3.setScene(self.onplayer_scene)
        #self.onplayer_view = QGraphicsView(self.onplayer_scene, parent=self.ui.scope_camera_view_item_3)
        self.ui.scope_camera_view_item_3.setStyleSheet("background-color: rgb(0,0,0);")
        self.onplayer_view_item = QGraphicsPixmapItem()
        self.onplayer_scene.addItem(self.onplayer_view_item)
        self.on_template = None

        # on player buttons
        self.ui.pushButton_129.clicked.connect(self.onplayer_pause)
        self.ui.pushButton_131.clicked.connect(self.onplayer_rt)

        # on_player slider
        self.slider_lock = False
        self.ui.horizontalSlider_7.sliderPressed.connect(self.onplayer_slider_pressed)
        self.ui.horizontalSlider_7.valueChanged.connect(self.onplayer_slider_valueChanged)
        self.ui.horizontalSlider_7.sliderReleased.connect(self.onplayer_slider_released)

        self.ui.horizontalSlider_6.sliderPressed.connect(self.onplayer_slider_pressed)
        self.ui.horizontalSlider_6.valueChanged.connect(self.onplayer_slider_valueChanged)
        self.ui.horizontalSlider_6.sliderReleased.connect(self.onplayer_slider_released)

        self.ui.DecodingButton.clicked.connect(self.decoding)
        self.ui.DecodingText.setVisible(False)
        self.ui.DecodingStatusText.setVisible(False)
        ## -------------------------------------------------------------------------------------------

        # x#
        # self.l_chart = QWidget(self.ui.widget_21)

        # x#  chart_scene = QGraphicsScene()
        # x#
        # x#  #self.chart_view = QGraphicsView(self.chart0, parent=self.ui.widget_21) ## number changed
        # x#  l_chart = QGraphicsView(chart_scene, parent=self.ui.widget_21)
        # x#
        # x#  chart0 = QtCharts.QChart()
        # x#  chart_scene.addItem(chart0)
        # x#
        # x#  #self.ui.widget_21
        # x# ## l_chart=QtCharts.QChartView(chart0)
        # x#  l_chart.setGeometry(QtCore.QRect(10,25,600,85))
        # x#  series = QtCharts.QLineSeries(name='lever pressure')
        # x#  mapper = QtCharts.QVXYModelMapper(xColumn=0, yColumn=2)  #################  ?? *******#V#
        # x#  # mapper.setModel(self.table.model())
        # x#  mapper.setSeries(series)
        # l_chart.addSeries(mapper.series())

        # l_chart.setFixedSize(620,100)

        # QtCharts.QChartView(self.l_chart)
        # l_chart = QtCharts.QChart()
        # l

        # self.ui.widget_21.add

        ##------------ lever pressure - trace praph (self.ui.widget_21 ) ------------
        # print("chart test0")
        # chart1 = QtCharts.QChart()

        # self.chart_v1 = QtCharts.QChartView(chart1)

        # self.chart_v1.setFixedSize(620,100)
        # qsplitter

        # self.chart_v1.setFixedSize(620,100)

        # x#  series = QtCharts.QLineSeries(name='lever pressure')
        # x#  mapper = QtCharts.QVXYModelMapper(xColumn=0, yColumn=2)
        # x#  #mapper.setModel(self)
        # x#  mapper.setSeries(series)

        # x#  self.table = QTableWidget(0,2)

        # x#  chart0.addSeries(mapper.series()) ### sf ui1 0

        # x#  self.axis_X = QtCharts.QDateTimeAxis()
        # x#  self.axis_X.setFormat("ss mm HH")
        # x#  self.axis_Y = QtCharts.QValueAxis()

        # x#  chart0.setAxisX(self.axis_X, series)  ### sf ui1 0
        # x#  chart0.setAxisY(self.axis_Y, series)  ### sf ui1 0
        # x#  self.axis_Y.setRange(0,0)
        # x#  self.axis_Y.setLabelFormat('%.0f')

        # x#  chart0.setTitle('trace graph') ### sf ui1 0

        # x#  self.populate()
        # self.axis_X.setRange()

        # self.axis_X =

        # self.ui.widget_21 = QtCharts.QChart()
        ### self.chartLever = QtCharts.QChart()
        ### QtCharts.QChartView(self.chartLever[self.parent=widget_21])
        # self.chart.setAnimationOptions(QtCHarts.QCHart.AllAnimations)
        # self.add_series("Magnitude (Column 1)",[0,1])

        ## lever pressure __3  --------------- temp chart
        # self.gp = make_graph()

        ###       self.l_graph_scene = QGraphicsScene()
        ###       self.ui.graphicsView = QGraphicsView(self.l_graph_scene, parent=self.ui.widget_10)
        ###       self.ui.graphicsView.setGeometry(QtCore.QRect(10, 27, 1460, 101))
        ###
        ###       x = np.linspace(0,10,100)
        ###       y = np.cos(x)
        ###
        ###       plt.ion()
        ###
        ###       l_figure, ax = plt.subplots(figsize=(16,0.8))
        ###       matplotlib.interactive(True)
        ###       plt.close(fig=l_figure)
        ###
        ###       line1, = ax.plot(x,y)
        ###
        ###       #l_fig = plt.Figure()
        ###       canvas = FigureCanvas(l_figure)
        ###
        ###
        ###       #canvas.setGeometry(10,27,1460,101)
        ###
        ###       #layout_l = QLayout(self.ui.widget_10)
        ###       #layout_l.addWidget(canvas)
        ###       self.l_graph_scene.addWidget(canvas)
        ###
        ###
        ###       for p in range(100):
        ###           updated_y = np.cos(x-0.05*p)
        ###
        ###           line1.set_xdata(x)
        ###           line1.set_ydata(updated_y)
        ###           canvas.draw()
        ###           canvas.flush_events()
        ###           time.sleep(0.01)

        ## motion correction --------------------------------------*****--------------------------

        self.ui.connectBehaviorCameraButton_4.clicked.connect(self.motion_corr)

        ## lever pressure_ 4 graph -------------------------------- **** ------------------------------------------------------
        p_path = os.getcwd()
        self.file_csv = p_path + '/test.csv'
        self.im_data(self.file_csv)
        ## -----------------------------------------
        self.test_chart = QtCharts.QChart()
        self.test_chart.setAnimationOptions(QtCharts.QChart.AllAnimations)  ## realtime-re
        ## 중복조심 name
        ##    self.test_model = self.loadChartData(self.chart_df) ## self 필요 check
        self.add_series("lever-data", [0, 1])
        ## creating QChartView
        self.chart_view = QtCharts.QChartView(self.test_chart)
        self.chart_view.setRenderHint(QtGui.QPainter.Antialiasing)  ## clear line
        self.main_layout = QHBoxLayout(self.ui.widget_10)  #######################3)
        # widgetsize#    size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # widgetsize#    self.chart_view.setSizePolicy(size)
        self.main_layout.addWidget(self.chart_view)
        self.setLayout(self.main_layout)  #####################

        ### default cam widget disable--------------------------
        self.ui.widget_8.setEnabled(False)  ## behavior
        self.ui.widget_9.setEnabled(False)  ## scope

        self.ui.widget_2.setEnabled(False)  ## record

        ## default camera
        self.Snum = None
        self.Bnum = None
        self.cam_nlist = None

        ## notice -------------------------
        self.mnotice = QMessageBox()
        self.mnotice.setWindowTitle("notice")
        self.mnotice.setWindowIcon(QtGui.QPixmap("info.png"))
        self.mnotice.setIcon(QMessageBox.Information)
        self.mnotice.setText("!")

        self.ui.statusbar.showMessage('welcome')

        ### loging test -- system information

        self.dev_list = []
        ##     self.get_devlist()
        self.mini_num = None
        self.cam_num = None
        self.get_cam_n()

        ###
        ## usb list

        #   import win32com.client
        #   wmi = win32com.client.GetObject("winmgmts:")
        #   for usb in wmi.InstancesOf("Win32_USBHub"):
        #       print(usb.DeviceID, usb.Name, usb.Description, usb.SystemName, usb.status)

        ## drive list
        ##     import win32file

        ##     def locate_usb():
        ##         drive_list = []
        ##         drivebits = win32file.GetLogicalDrives()
        ##         for d in range(1, 26):
        ##             mask = 1 << d
        ##             if drivebits & mask:
        ##                 # here if the drive is at least there
        ##                 drname = '%c:\\' % chr(ord('A') + d)
        ##                 t = win32file.GetDriveType(drname)
        ##                 ## if t == win32file.DRIVE_REMOVABLE:
        ##                 drive_list.append(drname)
        ##         return drive_list
        ##     print(locate_usb())
        ## ---

        self.user_os = platform.system()
        sys_info_data = ("system OS: " + self.user_os + "\n") * 10 + (f'device: {self.dev_list}')  ## H add function 처리
        self.sys_info = QLabel(sys_info_data)
        self.ui.scrollArea.setWidget(self.sys_info)

        ## if 'win' or 'Win' in self.user_os:
        ## os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'windowsmediafoundation'
        ### os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'directshow'

        ## linux --> camera index
        self.cam_nlist = self.cam_ix()
        self.ui.scrollArea_2.setWidget(QLabel("camera list: " + str(self.cam_nlist)))

        ## one miniscope, other cam
        self.ui.catch_camlist.clicked.connect(self.cam_refresh)

        ## cam number
        self.Bnum = None
        self.Scam = None
        regExp = QtCore.QRegExp("[0-9]*")
        self.ui.BnumBox.setValidator(QtGui.QRegExpValidator(regExp, self))
        self.ui.SnumBox.setValidator(QtGui.QRegExpValidator(regExp, self))
        self.ui.set_cnum_button.clicked.connect(self.set_cam_number)
        ## self.cam_nlist = None

        ## scope camera box

        ##
        # self.scope_camera_view_item = QtWidgets.QGraphicsView(self.widget_5)
        # self.scope_camera_view_item.setMinimumSize(QtCore.QSize(1020, 640))
        # self.scope_camera_view_item.setObjectName("scope_camera_view_item")
        # self.gridLayout_5.addWidget(self.scope_camera_view_item, 1, 1, 1, 2)

        # self.scope_camera_view = self.ui.scope_camera_view_item

        ##
        # self.ui.scope_camera_scene = QGraphicsScene()
        # self.ui.scope_camera_view_item = QGraphicsView(self.ui.scope_camera_scene, parent=self.ui.widget_5)
        # self.ui.scope_camera_view_item.setMinimumSize(QtCore.QSize(1020, 640))
        # self.ui.scope_camera_view_item.setStyleSheet("background-color: rgb(0, 0, 0);")
        # self.ui.scope_camera_view_item.setObjectName("scope_camera_view_item")
        # self.ui.scope_camera_view_item_i = QGraphicsPixmapItem()
        # self.ui.scope_camera_scene.addItem(self.ui.scope_camera_view_item_i)
        # self.ui.gridLayout_5.addWidget(self.ui.scope_camera_view_item, 1, 1, 1, 2)

        ##

        ## self.scope_camera_view = self.ui.scope_camera_view_item
        ##self.scope_camera_view = self.ui.graphicsView_5
        self.scope_camera_scene = QGraphicsScene()

        self.scope_camera_view = QGraphicsView(self.scope_camera_scene,
                                               parent=self.ui.widget_71)  ## w5->widget_71-> graphicsView_5
        # +# self.scope_camera_view = QGraphicsView(self.scope_camera_scene)#, parent=self.ui.graphicsView_5) ## w5->widget_71->

        # self.behavior_camera_view.setMinimumSize(QtCore.QSize(1020, 640))
        self.scope_camera_view.setStyleSheet("background-color: rgb(0, 0, 0);")
        # self.behavior_camera_view.setObjectName("scope_camera_view")
        self.scope_camera_view_item_i = QGraphicsPixmapItem()
        self.scope_camera_scene.addItem(self.scope_camera_view_item_i)

        ##### ui 처리
        self.gridLayout_f71 = QtWidgets.QGridLayout(self.ui.scope_camera_view_item)
        self.gridLayout_f71.addWidget(self.scope_camera_view)
        self.ui.widget_71.hide()

        self.ui.tabWidget.setCurrentIndex(0)


        #auto focus
        self.ui.AutoFocus.clicked.connect(self.autoFocus)
        self.ui.AutoFocus_2.clicked.connect(self.autoFocus)

        self.behavior_camera_view = self.ui.behavior_camera_view_item
        self.behavior_camera_scene = QGraphicsScene()
        self.behavior_camera_view = QGraphicsView(self.behavior_camera_scene, parent=self.ui.widget_4)
        # self.behavior_camera_view.setMinimumSize(QtCore.QSize(1020, 640))
        self.behavior_camera_view.setStyleSheet("background-color: rgb(0, 0, 0);")
        # self.behavior_camera_view.setObjectName("scope_camera_view")
        self.behavior_camera_view_item_i = QGraphicsPixmapItem()
        self.behavior_camera_scene.addItem(self.behavior_camera_view_item_i)
        self.ui.gridLayout_6.addWidget(self.behavior_camera_view, 1, 1, 1, 2)

        ## loading box
        t_lay_parent = QtWidgets.QVBoxLayout()
        self.ld_widget = QWidget(self.ui.widget_103)
        # self.ui.widget_103.setLayout(t_lay_parent)
        self.ld_widget.setLayout(t_lay_parent)
        self.ld_widget.setGeometry(218, 20, 895, 556)
        #        t_lay_parent=ld_widget.QVBoxLayout()

        self.m_play_state = False

        self.m_label_gif = QLabel()
        t_lay_parent.addWidget(self.m_label_gif)
        # self.ui.scope_camera_view_item_2.addWidget(self.m_label_gif)

        self.m_movie_gif = QtGui.QMovie("ldld.gif")
        self.m_label_gif.setMovie(self.m_movie_gif)
        self.m_label_gif.setScaledContents(True)
        self.m_label_gif.hide()
        self.ld_widget.hide()

        ## ROI list

        from roi_table import Table
        self.roi_table = Table(0, self)
        # self.ui.tab_16.layout = QtWidgets.QVBoxLayout(self)
        roilist_layout = QtWidgets.QVBoxLayout()
        roilist_layout.addWidget(self.roi_table)
        self.ui.tab_16.setLayout(roilist_layout)

        self.onroi_table = Table(1, self)
        onroilist_layout = QtWidgets.QVBoxLayout()
        onroilist_layout.addWidget(self.onroi_table)
        self.ui.tab_12.setLayout(onroilist_layout)

        ## ROI function
        print('item_before: ', self.player_scene2.items())
        self.check_ROI_add = False
        self.ui.pushButton_75.clicked.connect(self.addRoi)
        self.ui.pushButton_77.clicked.connect(self.deleteRoi)

        boundingRect = self.player_scene2.itemsBoundingRect()  ##여기서 하면, frame 좌표로 생성
        self.player_scene2.setSceneRect(0, 0, boundingRect.right(), boundingRect.bottom())

        self.check_onROI_add = False
        self.ui.pushButton_122.clicked.connect(self.addOnRoi)
        self.ui.pushButton_124.clicked.connect(self.deleteOnRoi)

        ## AUTO ROI function
        self.ui.connectBehaviorCameraButton_5.clicked.connect(self.auto_roi)
        # self.ui.connectBehaviorCameraButton_5.clicked.connect(self.caimanpipe)
        # self.ui.connectBehaviorCameraButton_5.clicked.connect(self.hncc_roi)

        ## neuron extraction
        self.ui.connectBehaviorCameraButton_10.clicked.connect(self.neuronExtraction)
        self.ui.connectBehaviorCameraButton_11.clicked.connect(self.save_trace)
        self.trace_viewer = None

        itemlist = self.player_scene2.items()
        print('item_after: ', itemlist)

        self.init_onchart()

    ## functions ------------------------------------------------------------------------------------------------------------------------
    #########################################################################
    #                                                                       #
    #                                                                       #
    #                           Home Tab Functions                          #
    #                                                                       #
    #                                                                       #
    #########################################################################

    # ------------------------------------------------------------------------
    #
    #                             system buttons
    #
    # ------------------------------------------------------------------------

    def button_new(self):
        self.ui.lineEdit.setText(datetime.now().strftime("%Y-%m-%d"))
        self.ui.lineEdit_26.setText("")
        self.ui.comboBox_4.setCurrentIndex(0)
        self.ui.spinBox_5.setValue(0)
        self.ui.spinBox_6.setValue(0)
        self.ui.checkBox_12.setCheckState(QtCore.Qt.Unchecked)

    # h5py版本更新，改变读取方式
    def button_load(self):
        path = str(QFileDialog.getOpenFileName(self, "select project file", './', 'Project File (*.obmiproject)')[0])
        if path == "":
            return

        print(f'load project file: {path}')
        with h5py.File(path, 'r') as f:
            version = f['info']['version'][()]
            # check version number
            if version == 1.0:
                g = f['offline']
                # read offline video data
                if len(g.keys()) > 0:
                    self.player2 = VPlayer(v_path='', lock=self.data_lock, parent=self)
                    self.player2.frame_list = g['video'][:]
                    self.player2.total_frame = g['total_frame'][()]
                    self.player2.fps = g['fps'][()]
                    self.player2.load_mode = True
                    self.player2.start()
                    self.player2.frameC.connect(self.update_player_frame2)

                    time.sleep(0.1)

                    self.s_totalframe2 = self.player2.total_frame
                    self.s_total2 = int(self.s_totalframe2 / self.player2.fps)

                    self.update_v_duration2(self.s_total2, self.s_totalframe2)

                    # read offline roi data
                    if len(g.keys()) > 3:
                        data = g['roi_data'][:]
                        contours = g['roi_contours'][:]
                        idx = 0
                        for roi_data in data:
                            roi_id, x, y, type, c_size = roi_data
                            contour = contours[idx:idx+int(c_size)]
                            idx += int(c_size)
                            contour = [QtCore.QPointF(contour[i], contour[i+1]) for i in range(len(contour)-1) if i % 2 == 0]
                            roi = self.addRoiPolygon(x, y, contour)
                            roi.setId(roi_id)
                            if type == 1:
                                roi.type = ROIType.CIRCLE
                                roi.size = roi.boundingRect().width()

                g = f['online']
                # read online roi data
                if len(g.keys()) > 1:
                    self.on_scope = None
                    data = g['roi_data'][:]
                    contours = g['roi_contours'][:]
                    idx = 0
                    for roi_data in data:
                        roi_id, x, y, type, c_size = roi_data
                        contour = contours[idx:idx + int(c_size)]
                        idx += int(c_size)
                        contour = [QtCore.QPointF(contour[i], contour[i + 1]) for i in range(len(contour) - 1) if
                                   i % 2 == 0]
                        roi = self.addOnRoiPolygon(x, y, contour)
                        roi.setId(roi_id)
                        if type == 1:
                            roi.type = ROIType.CIRCLE
                            roi.size = roi.boundingRect().width()

    def button_save(self):
        path = self.ui.lineEdit_26.text()
        if path == "":
            path_msg = QMessageBox(QMessageBox.Warning, 'Warning', 'No path found')
            path_msg.exec_()
            return
        name = self.ui.lineEdit.text()
        if name == "":
            name_msg = QMessageBox(QMessageBox.Warning, 'Warning', 'Enter project name')
            name_msg.exec_()
            return

        fileurl = path + '/' + name + '.obmiproject'
        print(fileurl)

        with h5py.File(fileurl, 'w') as f:
            g = f.create_group('info')
            g['version'] = 1.0

            g = f.create_group('offline')
            if self.player2 is not None:
                fl = self.player2.frame_list
                g['fps'] = self.player2.fps
                g['total_frame'] = self.player2.total_frame
                g['video'] = numpy.asarray(fl)

                if self.roi_table is not None:
                    size = self.roi_table.size()
                    if size > 0:
                        shape_data = []
                        data = np.empty((size, 5))
                        roi_list = self.roi_table.itemlist
                        for i in range(len(roi_list)):
                            roi = roi_list[i]
                            x = int(roi.pos().x())
                            y = int(roi.pos().y())
                            if roi.type == ROIType.CIRCLE:
                                type = 1
                            else:
                                type = 2
                            data[i] = np.array([roi.id, x, y, type, roi.c_size])
                            shape_data.extend(roi.contours.tolist())
                        g['roi_data'] = data
                        g['roi_contours'] = np.array(shape_data)

            g = f.create_group('online')
            if self.onroi_table is not None:
                size = self.onroi_table.size()
                if size > 0:
                    shape_data = []
                    data = np.empty((size, 5))
                    roi_list = self.onroi_table.itemlist
                    for i in range(len(roi_list)):
                        roi = roi_list[i]
                        x = int(roi.pos().x())
                        y = int(roi.pos().y())
                        if roi.type == ROIType.CIRCLE:
                            type = 1
                        else:
                            type = 2
                        data[i] = np.array([roi.id, x, y, type, roi.c_size])
                        shape_data.extend(roi.contours.tolist())
                    g['roi_data'] = data
                    g['roi_contours'] = np.array(shape_data)
        print('save success!')

    def button_recentfile(self):
        pass

    def button_option(self):
        pass

    #########################################################################
    #                                                                       #
    #                                                                       #
    #                     Acquisition Tab Functions                         #
    #                                                                       #
    #                                                                       #
    #########################################################################

    # ------------------------------------------------------------------------
    #
    #                             system buttons
    #
    # ------------------------------------------------------------------------

    # record button
    @Slot()
    def recording_start_stop(self):

        ## 현재시간 저장
        ###    self.rec_timer()
        ## 타이머 동작
        ## behavior 영상저장
        ## scope 영상저장
        ## pressure data 저장

        text = self.ui.recordButton.text()
        if text == "Record" and self.capturer2 is not None:
            self.capturer2.video_saving_status = VideoSavingStatus.STARTING
            if self.capturer is not None:
                self.capturer.video_saving_status = VideoSavingStatus.STARTING
                self.rec_timer(True)
            self.ui.recordButton.setText("Stop Recording")
            ## self.elapsed_t(QObject.QTime.currentTime()) timer 표기용
        elif text == "Stop Recording" and self.capturer2 is not None:
            self.capturer2.video_saving_status = VideoSavingStatus.STOPPING
            if self.capturer2 is not None:
                self.capturer.video_saving_status = VideoSavingStatus.STOPPING
                self.rec_timer(False)
            self.ui.recordButton.setText("Record")

            self.show_player()
            self.stop_connection()  ##

    # behavior camera connection
    @Slot()
    def connect_behavior_camera_button_clicked(self):
        text = self.ui.connectBehaviorCameraButton.text()
        if text == 'Behavior\n''Connect' and self.capturer is None:

            ## camera_ID = self.cam_num #1
            camera_ID = self.Bnum
            scopei = False
            if camera_ID == self.mini_num:
                scopei = True

            self.capturer = CaptureThread(camera=camera_ID, video_path=self.save_path, lock=self.data_lock, parent=self,
                                          user_path=self.user_path, f_type=self.save_format, pj_name=self.project_name,
                                          scopei=scopei)  ##받는 ##par-처리
            self.capturer.frameCaptured.connect(self.update_behavior_camera_frame)  ## frame 연결
            self.capturer.fpsChanged.connect(self.update_behavior_camera_FPS)  ##
            self.capturer.start()

            ## about fps
            ## self.ui.scope_fps.setText(f'fps: {self.FPS}')
            ## fps signal 계속 받기

            #  self.exposure_control(int(self.ui.exposureSliderBCam.value))
            # self.capturer.
            ### nd2 set policy / (!>interruption 고려)
            self.ui.connectBehaviorCameraButton.setText('Behavior\n''Disconnect')
            self.ui.signBehaviorCamera.setStyleSheet("background-color: rgb(0, 255, 0);")  ## > func or not
            self.ui.behaviorcamStatusLabel.setText('Connected')
            ###
            ### (nd check function)
            ###        if check_function():
            ###                setEnabled(True)
            ###           else
            ###                setEnabled(False)
            ###
            self.ui.widget_2.setEnabled(True)

        elif text == 'Behavior\n''Disconnect' and self.capturer is not None:

            self.capturer.frameCaptured.disconnect(self.update_behavior_camera_frame)  ##
            self.capturer.fpsChanged.disconnect(self.update_behavior_camera_FPS)
            self.capturer.stop()
            self.capturer = None

            self.ui.connectBehaviorCameraButton.setText('Behavior\n''Connect')  ## set text ##
            self.ui.signBehaviorCamera.setStyleSheet("background-color: rgb(85, 85, 127);")  ## > func or not
            self.ui.behaviorcamStatusLabel.setText('Disconnected')

            self.disable_cam('B')
            self.ui.widget_2.setEnabled(False)
            ## self.disable_cam('S') ## temp

    # scope camera connection
    @Slot()
    def connect_scope_camera_button_clicked(self):
        print("sign-sign")
        text = self.ui.connectScopeCameraButton.text()
        if text == 'Scope\n''Connect' and self.capturer2 is None:  ## check - capturer

            ## camera_ID = self.mini_num #0
            camera_ID = self.Snum  ##

            print("Camera_no.1")
            scopei = False
            if camera_ID == self.mini_num:
                scopei = True

            self.capturer2 = CaptureThread(camera=camera_ID, video_path=self.save_path, lock=self.data_lock,
                                           parent=self, user_path=self.user_path, f_type=self.save_format,
                                           pj_name=self.project_name, scopei=scopei)  ## VP- ##par-처리
            self.capturer2.frameCaptured.connect(self.update_scope_camera_frame)
            self.capturer2.fpsChanged.connect(self.update_scope_camera_FPS)
            self.capturer2.start()

            ## record finished
            self.capturer2.videoSaved.connect(self.record_finished)

            self.ui.connectScopeCameraButton.setText('Scope\n''Disconnect')
            self.ui.signScopeCamera.setStyleSheet("background-color: rgb(0, 255, 0);")
            self.ui.scopecamStatusLabel.setText('Connected')

            self.ui.widget_2.setEnabled(True)  ##

            if self.player is not None:
                self.play_finished()

            if self.fin_record_status:
                self.ui.widget_71.hide()
                self.scope_camera_view.show()

            self.capturer2.fps_calculating = True  ###

            ## print("cap2: ", self.capturer2.get(cv2.CAP_PROP_BRIGHTNESS))


        elif text == 'Scope\n''Disconnect' and self.capturer2 is not None:

            self.capturer2.frameCaptured.disconnect(self.update_scope_camera_frame)
            self.capturer2.fpsChanged.disconnect(self.update_scope_camera_FPS)
            self.capturer2.stop()
            self.capturer2 = None

            self.ui.connectScopeCameraButton.setText('Scope\n''Connect')
            self.ui.signScopeCamera.setStyleSheet("background-color: rgb(85, 85, 127);")
            self.ui.scopecamStatusLabel.setText('Disconnected')

            self.disable_cam('S')
            self.ui.widget_2.setEnabled(False)
            ## self.disable_cam('B') ## temp

    ## --------window------
    @Slot()
    def selectD(self):
        self.save_path = str(QFileDialog.getExistingDirectory(self, "select Directory"))
        self.ui.lineEdit_26.setText(self.save_path)
        self.user_path = True

    @Slot()
    def push_dir(self):  ## Home
        saving_location = self.save_path
        self.project_name = self.ui.lineEdit.text()  ## project name - rbmi 연계변경

        if self.capturer:
            self.capturer.video_path = self.save_path
            self.capturer.project_dir = self.project_name
        if self.capturer2:
            self.capturer2.video_path = self.save_path
            self.capturer2.project_dir = self.project_name

        ## default data - auto/
        ## Hwabt- cache save/

        self.save_format = self.format_list[self.ui.comboBox_3.currentIndex()]  ## number check/
        print("saveformat: ", self.save_format)
        self.ui.comboBox.setCurrentIndex(self.ui.comboBox_3.currentIndex())

        window_name = f'New Project - {self.project_name}({saving_location})'  # project

        self.ui.label_113.setGeometry(QtCore.QRect(20, 12, 500, 21))  ## temp size up
        self.ui.label_113.setText(window_name)  ## throw data

        # 82 21 500 21

        ## self.ui.scrollArea_4

        self.ui.tabWidget.setCurrentIndex(1)

    @Slot()
    def leverP_vi(self):  ## leverwindow
        if self.leverpVS:
            self.ui.widget_10.hide()
            self.leverpVS = False
        else:
            self.ui.widget_10.show()
            self.leverpVS = True

    @Slot()
    def behavP_vi(self):  ##behavwindow
        if self.behavPVS:
            self.ui.widget_4.hide()
            self.behavPVS = False
        else:
            self.ui.widget_4.show()
            self.behavPVS = True

    @Slot()
    def scopeP_vi(self):
        if self.scopeVS:
            self.scope_camera_view.hide()  ## -ui
            self.scopeVS = False
        else:
            self.scope_camera_view.show()  ## -ui
            self.scopeVS = True

    ### lever press record
    @Slot()
    def leverP_rec(self):

        if self.leverP_recVS:
            self.ui.graphicsView.hide()
            self.leverP_recVS = False
        else:
            self.ui.graphicsView.show()
            self.leverP_recVS = True

    ### format change
    @Slot()
    def format_change(self):
        if self.capturer:
            self.capturer.save_format = self.ui.comboBox.currentText()
        if self.capturer2:
            self.capturer2.save_format = self.ui.comboBox.currentText()

    @Slot()
    def autoFocus(self):
        # 弹窗选择prerecord_video,获取prerecord_video路径prerecord_video_path
        # C++实现： QString file_path = QFileDialog::getOpenFileName(this, "Open Temp file", "../")
        if self.mini_num is None:
            self.get_devlist()
            if self.get_cam_n() is None:
                return

        fp = QFileDialog.getOpenFileName(self, "select media file", './', 'Media File (*.avi;*.mp4)')[0]
        if fp is None:
            return

        dialog = QUiLoader().load('230925_Focus_Dialog.ui')
        if dialog.exec() == QDialog.Accepted:
            if self.capturer2:
                self.connect_scope_camera_button_clicked()

            if self.on_scope:
                self.online_scope()

            from registration_h import Preprocess
            prerecorded_video = Preprocess(fp)
            templateFrame = prerecorded_video.generate_template()  # 调用生成模版接口，得到templateFrame
            ncc = -1
            init_focus = int(dialog.focus.text())
            init_range = int(dialog.range.text())
            bestFocus = 0  # 记录最大NCC值和最大NCC值下的焦距

            cap = cv2.VideoCapture(self.mini_num + cv2.CAP_DSHOW)
            from cameraController import MiniscopeController
            controller = MiniscopeController('./configs/miniscopes.json')
            controller.init_args(cap)

            for i in range(init_focus - init_range, init_focus + init_range + 1):
                print("generating focus:", i)
                controller.change_focus(cap, i)
                current_template = prerecorded_video.focus_generate_temp(cap)
                # print(templateFrame.shape, current_template.shape)
                result = cv2.matchTemplate(templateFrame, current_template, cv2.TM_CCOEFF_NORMED)  # 计算两帧的相关性
                # print('result:',result)
                if (result.max() > ncc):
                    ncc = result.max()
                    bestFocus = i

            cap.release()
            msgbox = QMessageBox()
            msgbox.information(self, 'Info', f'Best focus is: {bestFocus}')


    # ------------------------------------------------------------------------
    #
    #                             system functions
    #
    # ------------------------------------------------------------------------
    ## show player
    def show_player(self):
        print('saving file...')
        time.sleep(0.5)
        self.scope_camera_view.hide()
        print('opening file...')
        time.sleep(0.5)
        self.ui.widget_71.show()

        ## 접기
        ## capture = cv2.VideoCapture(self.capturer2.video_file)
        ## ret, i_frame = capture.read()

        ## self.present_status = 0

        ##   self.push_image(i_frame)##(아니면 캡쳐 jpg)(frame 연결부에 연결)

        self.player = VPlayer(v_path=self.capturer2.video_file, lock=self.data_lock, parent=self, fps=self.s_fps)
        self.player.start()

        duration = self.s_total

        print(duration)
        self.s_totalframe = self.capturer2.count_frames
        self.update_v_duration(duration * 10, self.s_totalframe)  ## self.player.total_frame)

        print('player started')
        ## self.push_img(self.present_status,capture)

    def stop_connection(self):
        ### Hwab con/
        if self.ui.connectBehaviorCameraButton.text() == 'Behavior\n''Disconnect' and self.capturer is not None:
            self.connect_behavior_camera_button_clicked()
            self.set_cam_number()  ## func 보완필요
        if self.ui.connectScopeCameraButton.text() == 'Scope\n''Disconnect' and self.capturer2 is not None:
            self.connect_scope_camera_button_clicked()
            self.set_cam_number()  ## func 보완필요

    ############ import data -- lever -------------- --------------------------------------------------------------
    def im_data(self, file_name):
        self.chart_df = pd.read_csv(file_name)

    def add_series(self, name, columns):
        self.series = QtCharts.QLineSeries()
        self.series.setName(name)

        for i in range(self.chart_df.shape[0]):  ##self.coulumn_count):
            ## t = self.input_time[i]
            t = self.chart_df['time'][i]
            x = t  ## .toMSecsSinceEpoch()
            ## y = float(self.input_value[i])
            y = float(self.chart_df['mag'][i])

            if x >= 0 and y >= 0:
                self.series.append(x, y)
        self.test_chart.addSeries(self.series)

    ### record timer
    def rec_timer(self, status: bool):
        if status:
            self.s_total = 0
            self.e_timer = QtCore.QTimer(self)
            self.e_timer.timeout.connect(self.elapsed_time)
            self.e_timer.start(10)
        else:
            self.e_timer.stop()

    def elapsed_time(self):
        self.s_total = self.s_total + 1
        total = self.s_total * 10
        ## print(total)
        time = self.hhmmss(total)
        self.ui.label_24.setText(f'Elapsed time: {time}')
        self.ui.label_25.setText(f'Record length: {self.capturer2.count_frames}')

    ### camera indexing
    def cam_ix(self):
        cam_list = []
        for i in range(len(self.dev_list)):
            cap = cv2.VideoCapture()  ## cv2.CAP_DSHOW + i) ## cap open
            cap.open(i, cv2.CAP_DSHOW)
            if cap.read()[0]:
                cam_list.append(i)
                # cap.read()[0]
            cap.release()  ### --
        return cam_list

    @Slot()
    def cam_refresh(self):
        if self.ui.widget_2.isEnabled():
            self.mnotice.setText("turn off the camera first please")  ## temporary
            self.mnotice.exec_()
        self.ui.statusbar.showMessage('camara scan started')
        a = ""
        b = ""
        ### self.mini_num = None

        print("refresh start")
        self.get_devlist()
        cam_nlist = self.cam_ix()
        print("get camnlist: ", cam_nlist)
        scope_n = self.get_cam_n()
        print("get scopen: ", scope_n)
        print("get scopen(mininum): ", self.mini_num)
        print("dev list: ", self.dev_list)

        for i in cam_nlist:
            ## devlist str
            if scope_n == i:
                a = a + str(i) + ': ' + self.dev_list[i] + '\n'
            else:
                b = b + str(i) + ': ' + self.dev_list[i] + '\n'

        #           except:
        #               print("--- device and camera matching error ---")

        self.ui.scope_num.setText(a)
        self.ui.cam_nums.setText(b)
        self.cam_nlist = cam_nlist

        if a == '' and b == '':
            self.ui.statusbar.showMessage('--no camera detected--')

    def get_devlist(self):
        self.dev_list = []  ### temp
        graph = FilterGraph()
        try:
            self.dev_list = graph.get_input_devices()
        except ValueError:
            print("-- No device found --")  ## cn sys_info_data
            self.ui.statusbar.showMessage('-- No device found --', 7000)
            self.mnotice.setText("no device found ")  ##
            self.mnotice.exec_()

    def get_cam_n(self):
        if 'MINISCOPE' in self.dev_list:
            self.mini_num = self.dev_list.index('MINISCOPE')

        ###list = [i for i, v in enumerate(list) if value == num]
        ##if len(self.mini_num) > 1:

        ###    print("-- multiple miniscope detected -- ")
        ###    ui.statusbar.showMessage("multiple miniscope detected",30000)

        ## if self.mini_num == 0:  ##
        ##    self.cam_num = 1 ##
        else:
            self.mini_num = None
            self.ui.statusbar.showMessage('-- No miniscope found --', 7000)
            print('--no miniscope found--')
        return self.mini_num

    @Slot()
    def set_cam_number(self):  ## check mini_num and cam_num ###

        self.ui.statusbar.showMessage('camera setting')  ## ch2 emit
        Bn = self.ui.BnumBox.text()
        Sn = self.ui.SnumBox.text()

        if Bn == '' and Sn == '':
            self.mnotice.setText("(temp) set camera number again please ")  ## temporary
            self.mnotice.exec_()
            return

        Bn = int(Bn)
        Sn = int(Sn)

        # if type(Bn) or type(Sn) is not :
        #    self.mnotice.setText("check your input please")
        #    self.mnotice.exec_()

        ## print(type(self.ui.BnumBox.text()))
        ## print(self.cam_nlist, type(self.cam_nlist[0])) ## int
        ## print("Bnt: ", type(Bn)) ## str
        ## print(f'b: {Bn}, s: {Sn}')

        if (Bn in self.cam_nlist) and (Sn in self.cam_nlist):  ## 각 조건
            print("what happend")
            self.Bnum = Bn
            self.Snum = Sn
            print(self.Bnum, self.Snum, self.cam_nlist)
            self.ui.widget_8.setEnabled(True)
            self.ui.widget_9.setEnabled(True)

            self.ui.statusbar.showMessage('ready')
        else:
            print(f'xx b:{Bn}, s:{Sn}, camlist: {self.cam_nlist}')
            self.mnotice.setText("check the numbers please")
            self.mnotice.exec_()
            self.ui.statusbar.showMessage('_')
            self.ui.statusbar.showMessage('check the numbers please', 10000)
        print(self.dev_list)

    def disable_cam(self, alp: str):

        if alp == "B":
            self.ui.widget_8.setEnabled(False)
            # self.ui.BnumBox.setText("")
            # self.ui.BnumBox.setPlaceholderText(str(self.Bnum))

        if alp == "S":
            self.ui.widget_9.setEnabled(False)
            # self.ui.SnumBox.setText("")
            # self.ui.SnumBox.setPlaceholderText(str(self.Snum))

    ### def cam_status_check(self):
    ###     return True | False

    ### ------ notice f ----
    @Slot(str)
    def record_finished(self, a):
        self.ui.statusbar.showMessage('record finished', 10000)
        self.mnotice.setText(f"record finished \n {a}")

    ### ------ software system ----

    def d_widget_scope(self):
        self.ui.widget_9.setEnabled(False)

    def e_widget_scope(self):
        self.ui.widget_9.setEnabled(True)


    # ------------------------------------------------------------------------
    #
    #                             update functions
    #
    # ------------------------------------------------------------------------

    # behavior camera image update
    @Slot(QtGui.QImage)  ## camera image
    def update_behavior_camera_frame(self, pixmap):
        # temp_width2 = self.behavior_camera_view.width()
        # if self.temp_width != temp_width2:
        #     self.temp_width = temp_width2
        #     print(self.temp_width)
        pixmap = pixmap.scaledToWidth(self.behavior_camera_view.width())  ## 4
        self.behavior_camera_view_item_i.setPixmap(pixmap)

    # scope camera image update
    @Slot(QtGui.QImage)
    def update_scope_camera_frame(self, pixmap):
        pixmap = pixmap.scaledToWidth(self.scope_camera_view.width())
        self.scope_camera_view_item_i.setPixmap(pixmap)  ## ui, _i

    @Slot(float)
    def update_behavior_camera_FPS(self, fps):
        self.ui.behavior_fps.setText(f'FPS: {fps}')

    @Slot(float)
    def update_scope_camera_FPS(self, fps):
        self.ui.scope_fps.setText(f'FPS: {fps}')

    def set_scope_fps(self, fps):
        fps_d = {5: 4, 7: 6, 8: 6, 9: 6, 10: 12, 11: 12}
        fps = fps / 5
        if fps in list(fps_d.keys()):
            fps = fps_d[fps]

        self.capturer2.cfps = fps * 5
        ## self.capturer2.set(cv2.CAP_PROP_FPS, fps)

    def set_behavior_fps(self, fps):
        self.capturer.cfps = fps

    # ------------------------------------------------------------------------
    #
    #                             slider functions
    #
    # ------------------------------------------------------------------------

    ## exposure control   ### seems, miniscope used brightness for exposure > need to change
    def exposure_control_b(self, val):
        val = val / 100 * 64
        self.capturer.exposure_status = val  ##self.ui.exposureSliderBCam.value() ## ab on/
        ## self.ui.label_59.setText("FPS: " + str(self.capturer.exposure_status))
        ## self.ui.label_59.setText(f"FPS: {self.ui.exposureSliderBCam.value()}")

    def exposure_control_s(self, val):
        val = val / 100 * 64
        self.capturer2.exposure_status = val

    @Slot()
    def move_slider1(self, sl_val):
        print(sl_val)
        print("moved")
        self.ui.exposureValueBCam.setPlaceholderText(str(sl_val))
        self.exposure_control_b(sl_val)

    @Slot()
    def slider_box1(self):
        set_v = int(self.ui.exposureValueBCam.text())
        self.move_slider1(set_v)
        self.ui.exposureSliderBCam.setValue(set_v)
        self.ui.exposureValueBCam.setText("")

    ## Visualization brightness
    @Slot()
    def move_slider2(self, sl_val):
        print(sl_val)
        print("moved")
        self.ui.visualBrightnessValue.setPlaceholderText(str(sl_val))

    @Slot()
    def slider_box2(self):
        set_v = int(self.ui.visualBrightnessValue.text())
        self.ui.visualBrightnessValue.setPlaceholderText(str(set_v))
        self.ui.visualBrightnessSlider.setValue(set_v)
        self.ui.visualBrightnessValue.setText("")

    ## Visualization contrast
    @Slot()
    def move_slider3(self, sl_val):
        print(sl_val)
        print("moved")
        self.ui.visualContrastValue.setPlaceholderText(str(sl_val))

    @Slot()
    def slider_box3(self):
        set_v = int(self.ui.visualContrastValue.text())
        self.ui.visualContrastValue.setPlaceholderText(str(set_v))
        self.ui.visualContrastSlider.setValue(set_v)
        self.ui.visualContrastValue.setText("")

    ## display overlay slider

    @Slot()
    def move_slider4(self, sl_val):
        print(sl_val)
        print("moved")
        self.ui.overlayValue.setPlaceholderText(str(sl_val))

    @Slot()
    def slider_box4(self):
        set_v = int(self.ui.overlayValue.text())
        self.ui.overlayValue.setPlaceholderText(str(set_v))
        self.ui.overlaySlider.setValue(set_v)
        self.ui.overlayValue.setText("")

    ## scope LED slider
    @Slot()
    def move_slider5(self, sl_val):
        print(sl_val)
        print("moved")
        self.ui.scopeLEDvalue.setPlaceholderText(str(sl_val))
        self.capturer2.led_status = sl_val

    @Slot()
    def slider_box5(self):
        set_v = int(self.ui.scopeLEDvalue.text())
        self.move_slider5(set_v)
        self.ui.scopeLEDslider.setValue(set_v)
        self.ui.scopeLEDvalue.setText("")

    ## scope Gain slider  #####
    @Slot()
    def move_slider6(self, sl_val):
        print(sl_val)
        print("moved")
        self.ui.scopeGainValue.setPlaceholderText(str(sl_val))
        self.capturer2.gain_status = sl_val

    @Slot()
    def slider_box6(self):
        set_v = int(self.ui.scopeGainValue.text())
        # self.ui.scopeGainValue.setPlaceholderText(str(set_v))
        self.move_slider6(set_v)
        self.ui.scopeGainSlider.setValue(set_v)
        self.ui.scopeGainValue.setText("")

    ## scope Focus slider
    @Slot()
    def move_slider7(self, sl_val_r):
        self.ui.scopeFocusValue.setPlaceholderText(str(sl_val_r))
        self.capturer2.focus_status = sl_val_r

    @Slot()
    def slider_box7(self):
        set_v = int(self.ui.scopeFocusValue.text())
        self.move_slider7(set_v)  # set_v
        self.ui.scopeFocusSlider.setValue(set_v)
        self.ui.scopeFocusvalue.setText("")

    @Slot()
    def fpsBox(self):
        val = int(self.ui.FRcomboBox.currentText())
        self.capturer2.cfps = val


    ####    @Slot()
    ####    def slider_box9(self):
    ####        set_v=int(self.ui.scopeETvalue.text())
    ####        self.ui.scopeETvalue.setPlaceholderText(str(set_v))
    ####        self.ui.scopeETslider.setValue(set_v)
    ####        self.ui.scopeETvalue.setText("")

    # ----------Seems no need in Acquisition Tab------------
    # @Slot()
    # def play_button_clicked(self):
    #     text = self.ui.pushButton_49.text()
    #     if self.player is not None and text == 'play':
    #         self.player.frameC.connect(self.update_player_frame)
    #         self.player.vplayer_status = VPlayerStatus.STARTING
    #         print("set starting")
    #         self.ui.pushButton_49.setText('pause')
    #     elif self.player is not None and text == 'pause':
    #         self.player.vplayer_status = VPlayerStatus.PAUSING
    #         self.player.frameC.disconnect(self.update_player_frame)
    #         print("set pausing")
    #         self.ui.pushButton_49.setText('play')
    #
    #     self.player.stateCh.connect(self.stop_button_clicked)
    #
    # ## player1
    # @Slot()
    # def stop_button_clicked(self, a):
    #     if self.player is not None:
    #         self.player.vplayer_status = VPlayerStatus.STOPPING
    #         self.ui.pushButton_49.setText('play')
    #         self.ui.horizontalSlider_3.setValue(0)
    #         print("set stopping")
    #     if a == 1:
    #         self.player.stateCh.disconnect(self.stop_button_clicked) ## _
    #
    # ## player1
    # @Slot()
    # def play_finished(self):
    #     if self.player is not None:
    #         self.player.stop()
    #         self.player = None
    #         print("OK")
    #         self.fin_record_status = True
    #
    # ## player1
    # def after_player(self):
    #     self.play_finished()
    #     self.ui.tabWidget.setCurrentIndex(2)
    #
    # ## player1
    # @Slot(QtGui.QImage)
    # def update_player_frame(self, image):
    #     pixmap = QtGui.QPixmap.fromImage(image)
    #     ## width control
    #     pl_width2 = self.player_view.width() #view?
    #     if self.pl_width != pl_width2:
    #         self.pl_width = pl_width2
    #         print('plW', self.pl_width)
    #     self.player_view_item_i.setPixmap(pixmap)
    #     self.frame_slider_update(self.player.present_frame)
    #
    # ## player1
    # def frame_slider_update(self, present_f):
    #     ## if self.player is not None:
    #
    #     self.ui.horizontalSlider_3.blockSignals(True)
    #     self.ui.horizontalSlider_3.setValue(present_f)
    #     self.ui.horizontalSlider_3.blockSignals(False)
    #     print(f'sliderposition: {present_f}')
    #     self.frame_slider_update_p(present_f)
    #
    # ## player1
    # def frame_slider_update_p(self, present_f):
    #     self.ui.label_87.setText(f'Frame: {int(present_f)}')
    #     self.present_time = present_f * self.s_total * 10 / self.s_totalframe
    #     self.ui.label_84.setText(self.hhmmss(self.present_time))
    #
    # ## player1
    # def update_v_duration(self, duration, f_duration):
    #
    #     self.ui.horizontalSlider_3.setMaximum(f_duration) ## see max
    #     print(f'set maxvalue: {f_duration}')
    #     if duration >= 0:
    #         self.ui.label_131.setText(self.hhmmss(duration))
    #
    #     ## duration update
    #     ## label_131 _last 00:00
    #
    #
    # # player1 time slider update
    # def update_v_position(self, position): #upt
    #
    #     if position >= 0:
    #         ## self. timer 생산  start restart stop elasped
    #
    #         self.ui.label_84.setText(self.hhmmss(position)) ## moving -
    #
    #     self.ui.horizontalSlider_3.blockSignals(True)
    #     self.ui.horizontalSlider_3.setValue(position)
    #     self.ui.horizontalSlider_3.blockSignals(False)
    #
    #     ## player set value
    #     ## label_84 _first 00:00
    #
    # # player1 slider value change
    # @Slot()
    # def slider_value_changed(self):
    #     if self.player is not None:
    #
    #         present_f = self.ui.horizontalSlider_3.value()
    #         self.player.present_frame = present_f  ##self
    #         self.frame_slider_update_p(present_f)
    #
    #         if self.ui.pushButton_49.text() == 'pause':
    #             ## self.ui.pushButton_49.setText('play') # autoplay
    #             self.play_button_clicked() ##with stateCh
    #         else:
    #             self.player.vplayer_status = VPlayerStatus.MOVING

    ### show player lock----------------------------------------------------------------------------------------------------

    ###    def show_player(self):
    ###
    ###        ###   QMultimedia 작업중
    ###
    ###        self.scope_camera_view.hide()
    ###
    ###        self.player = QMediaPlayer()
    ###        ## self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
    ###
    ###
    ###        print("1:", self.capturer.video_file)
    ###        print("1.5:", self.capturer2.video_file)
    ###        print("2:",self.capturer.saved_video_name)
    ###        ## print("P: ",QtCore.QPluginLoader.load())
    ###        ## print("3:",cap.video_file)
    ###        ## print('qurl:',QUrl.fromLocalFile(self.capturer2.video_file))
    ###
    ###        self.player.setMedia(QUrl.fromLocalFile(self.capturer2.video_file))
    ###        self.player.error.connect(self.erroralert)
    ###        print("player-error: ")
    ###    ## UI design part ----------
    ###    #play x1: pushButton_49
    ###    #pause
    ###    #stop slow: pushButton_58
    ###
    ###    #timelider: horizontalSlider_3
    ###    #volume: hslider - valueChanged.connect (self.player.setVolume)
    ###
    ###        self.ui.pushButton_49.pressed.connect(self.play_pause)
    ###        print("playpuase: ")
    ###        self.ui.pushButton_58.pressed.connect(self.player_stop)
    ###
    ###        ## test
    ###
    ###        self.ui.horizontalSlider_3.valueChanged.connect(self.player.setPosition)
    ###        self.player.durationChanged.connect(self.update_v_duration) ##
    ###        self.player.positionChanged.connect(self.update_v_position)
    ###
    ###        ## self.viewer = self.ui.graphicsView_5
    ###        self.viewer_lay = QHBoxLayout(self.ui.widget_71)
    ###
    ###        self.viewer.setWindowFlags(self.viewer.windowFlags() | Qt.WindowStaysOnTopHint)
    ###        self.viewer.setMinimumSize(QSize(480,360))
    ###
    ###        videoWidget = QVideoWidget()
    ###        self.viewer_lay.addWidget(videoWidget)
    ###        ###  self.viewer.setCentralWidget(videoWidget)  **
    ###        self.player.setVideoOutput(videoWidget) ## video playback
    ###
    ###    #    self.chart_view = QtCharts.QChartView(self.test_chart)
    ###    #    self.chart_view.setRenderHint(QtGui.QPainter.Antialiasing) ## clear line
    ###    #    self.main_layout = QHBoxLayout(self.ui.widget_10) #######################3)
    ###    #    self.main_layout.addWidget(self.chart_view)
    ###    #    self.setLayout(self.main_layout)
    ###      #0ing0#  player = QMediaPlayer()
    ###      #00#  print("cvname: ", self.capturer.video_file)
    ###      #00#  player.setMedia(QUrl.fromLocalFile(self.capturer.video_file))
    ###      #00#  videoWidget = QObject.QVideoWidget(self)
    ###      #00#  player.setVideoOutput(videoWidget)
    ###      #00#  videoWidget.show()
    ###
    ###
    ###        self.ui.widget_71.show()
    ###        self.fin_record_status = True

    ###
    ###
    ###    def erroralert(self):
    ###        ## 조건나누기
    ###        print(self.sys_info)
    ###        sys_info_data = self.sys_info.text()
    ###        sys_info_data = sys_info_data+ "error_code: Cam01\n"
    ###        self.sys_info = QLabel(sys_info_data)
    ###        self.ui.scrollArea.setWidget(self.sys_info) ## 업데이트로#
    ###
    ###    @Slot()
    ###    def play_pause(self):
    ###    #play x1: pushButton_49
    ###    #pause
    ###    #stop slow: pushButton_58
    ###        ## if something on off
    ###        if self.ui.pushButton_49.text() == 'x1' or 'start':
    ###            self.player.play
    ###            self.ui.pushButton_49.setText('pause')
    ###        else: # self.ui.pushButton_49.text == 'pause'
    ###            self.player.pause
    ###            self.ui.pushButton_49.setText('start')
    ###    @Slot()
    ###    def player_stop(self):
    ###        ## if self.ui.pushButton_58.text == 'slow' or 'stop':
    ###        self.player.stop
    ###        self.ui.pushButton_58.setText('stop')
    ###
    ###        ## if self.ui.pushButton_49.text != 'start':
    ###        self.ui.pushButton_49.setText('start')

    #########################################################################
    #                                                                       #
    #                                                                       #
    #                         Offline Tab Functions                         #
    #                                                                       #
    #                                                                       #
    #########################################################################

    # ------------------------------------------------------------------------
    #
    #                             load functions
    #
    # ------------------------------------------------------------------------

    @Slot()
    def load_video(self):
        self.open_video_path = str(
            QFileDialog.getOpenFileName(self, "select media file", './', 'Video (*.mp4 *.wma *.avi);;All files (*.*)')[
                0])  ## 형식*, Qurl 기본폴더
        print(f'selected file: {self.open_video_path}')
        if self.open_video_path != "":
            self.startPlayer2()  # init

    def load_roi(self):
        # read imageJ roi files to offline tab
        dir = QFileDialog.getExistingDirectory(self, "select ROI Directory")
        file_ls = os.listdir(dir)
        file_ls = sorted([file for file in file_ls if '.roi' in file])

        for roi_file in file_ls:
            d = readImagejROI(os.path.join(dir, roi_file))
            x = d['x']
            y = d['y']
            contour = d['contour']
            roi = self.addRoiPolygon(x, y, contour, name=d['name'])

        print(f'load {len(file_ls)} roi(s)')

    def load_on_roi(self):
        # read imageJ roi files to online tab
        dir = QFileDialog.getExistingDirectory(self, "select ROI Directory")
        file_ls = os.listdir(dir)
        file_ls = sorted([file for file in file_ls if '.roi' in file])

        for roi_file in file_ls:
            d = readImagejROI(os.path.join(dir, roi_file))
            x = d['x']
            y = d['y']
            contour = d['contour']
            roi = self.addOnRoiPolygon(x, y, contour, name=d['name'])

        print(f'load {len(file_ls)} roi(s)')

    # player initialization
    # TODO: potential bugs, logic optimization req
    def startPlayer2(self):
        # video2 = cv2.VideoCapture(self.open_video_path)
        # video2_fps = video2.get(cv2.CAP_PROP_FPS)
        self.player2 = VPlayer(v_path=self.open_video_path, lock=self.data_lock, parent=self)
        self.player2.start()
        self.player2.frameC.connect(self.update_player_frame2)

        time.sleep(0.5)

        self.s_totalframe2 = self.player2.total_frame
        self.s_total2 = int(self.s_totalframe2 / self.player2.fps)

        self.update_v_duration2(self.s_total2, self.s_totalframe2)

    def speed_1x(self):
        if self.player2 is None:
            return
        self.player2.playspeed(0)

    def speed_2x(self):
        if self.player2 is None:
            return
        self.player2.playspeed(1)

    def speed_3x(self):
        if self.player2 is None:
            return
        self.player2.playspeed(2)

    def speed_5x(self):
        if self.player2 is None:
            return
        self.player2.playspeed(3)

    # ------------------------------------------------------------------------
    #
    #                             update functions
    #
    # ------------------------------------------------------------------------
    ## player2
    @Slot(QtGui.QImage)
    def update_player_frame2(self, pixmap):
        ## width control
        self.player_view2 = self.ui.scope_camera_view_item_2
        pl_width = self.player_view2.width()  # view?
        if self.pl_width2 != pl_width:
            self.pl_width2 = pl_width
            print('plW', self.pl_width2)
        self.player_view_item_i2.setPixmap(pixmap)
        self.frame_slider_update2(self.player2.present_frame)
        # print(f'{time.time()-self.player2.timer}')

    # ------------------------------------------------------------------------
    #
    #                             player buttons
    #
    # ------------------------------------------------------------------------

    # play/pause button
    @Slot()
    def play_button_clicked2(self):
        text = self.ui.pushButton_2.text()
        if self.player2 is not None and text == 'play':
            # self.player2.frameC.connect(self.update_player_frame2)
            self.player2.vplayer_status = VPlayerStatus.STARTING
            print("set starting")
            self.ui.pushButton_2.setText('pause')
        elif self.player2 is not None and text == 'pause':
            self.player2.vplayer_status = VPlayerStatus.PAUSING
            # self.player2.frameC.disconnect(self.update_player_frame2)
            print("set pausing")
            self.ui.pushButton_2.setText('play')
        # self.player2.stateCh.connect(self.stop_button_clicked2)

    # L2 button
    @Slot()
    def player2_onoff(self):
        if self.p2oo_st:
            self.ui.scope_camera_view_item_2.hide()
            self.p2oo_st = False
        else:
            self.ui.scope_camera_view_item_2.show()
            self.p2oo_st = True


    # ------------------------------------------------------------------------
    #
    #                             update functions
    #
    # ------------------------------------------------------------------------

    @Slot(QtGui.QImage)
    def online_frame(self, pixmap):
        self.pixmap = pixmap
        self.onplayer_view_item.setPixmap(self.pixmap)
        # if self.on_scope.rtProcess:
        #     self.update_onplayer_slider(self.on_scope.cur_frame, self.on_scope.total_frame, self.on_scope.s_timer)

    # ------------------------------------------------------------------------
    #
    #                             player sliders
    #
    # ------------------------------------------------------------------------

    ## player2 time slider update
    def update_v_duration2(self, duration, f_duration):

        self.ui.horizontalSlider_10.setMaximum(f_duration - 1)  ## see max ##_
        print(f'set maxvalue: {f_duration}')
        if duration >= 0:
            self.ui.label_206.setText(self.player2.time_format(duration))  ## _15
            self.ui.label_211.setText(self.player2.time_format(duration))

    # player2 slider functions
    def player2slider_pressed(self):
        if self.player2 is not None:
            if self.player2.vplayer_status == VPlayerStatus.STARTING:
                self.player2.vplayer_status = VPlayerStatus.PAUSING
                self.ui.pushButton_2.setText('play')

    def player2slider_released(self):
        if self.player2 is not None:
            self.player2.frame_update()

    def player2slider_valueChanged(self, slider_value):
        if self.player2 is not None:
            if self.player2.vplayer_status == VPlayerStatus.STARTING:
                self.player2.next_frame = slider_value
            else:
                self.player2.set_frame(slider_value)
                self.player2.frame_update()

    ## slider update
    def frame_slider_update2(self, present_f):
        ## if self.player is not None:
        self.ui.horizontalSlider_10.blockSignals(True)  ##_
        self.ui.horizontalSlider_10.setValue(present_f)  ##_
        self.ui.horizontalSlider_10.blockSignals(False)  ##_
        # print(f'sliderposition: {present_f}')
        self.frame_slider_update_p2(present_f)

    ## slider texts update
    def frame_slider_update_p2(self, present_f):
        self.ui.label_209.setText(f'Frame: {int(present_f)}')  # _72
        self.ui.label_213.setText(f'Frame: {int(present_f)}')

        # time update
        present_time = self.player2.total_time * present_f / self.player2.total_frame
        timestr = "Time: " + str(round(present_time, 1)) + "/" + str(round(self.player2.total_time, 1)) + "sec"
        self.ui.label_208.setText(timestr)
        self.ui.label_214.setText(timestr)
        timestr = self.player2.time_format(int(present_time))
        self.ui.label_204.setText(timestr)
        self.ui.label_210.setText(timestr)

    # fps set
    def set_onscope_fps(self, fps):

        fps_d = {5: 4, 7: 6, 8: 6, 9: 6, 10: 12, 11: 12}
        fps = fps / 5
        if fps in list(fps_d.keys()):
            fps = fps_d[fps]

        self.on_scope.cfps = fps * 5

    # ------------------------------------------------------------------------
    #
    #                           motion correction
    #
    # ------------------------------------------------------------------------

    ## ---motion correction function
    # def test_motion_corr(self):
    #     mccdone = QMessageBox()
    #     mccdone.setWindowTitle("notice")
    #     mccdone.setWindowIcon(QtGui.QPixmap("info.png"))
    #     mccdone.setStandardButtons(QMessageBox.Apply | QMessageBox.Close)
    #     mccdone.setDefaultButton(QMessageBox.Apply)
    #     mccdone.setIcon(QMessageBox.Information)
    #     mccdone.setText("MCC process finished")
    #     mccdone.exec_()
    #     return

    def motion_corr(self):
        # loading bar signal
        # motion correction
        from mccc import MCC
        mcstart = time.time()
        self.play_finished2()
        print('playfinished2: ', time.time() - mcstart)
        self.wait = None
        self.mccbar = QtWidgets.QProgressBar()
        ## self.mccbar.setMininum(0)

        mccdone = QMessageBox()
        mccdone.setWindowTitle("notice")
        mccdone.setWindowIcon(QtGui.QPixmap("info.png"))
        mccdone.setStandardButtons(QMessageBox.Apply | QMessageBox.Close)
        mccdone.setDefaultButton(QMessageBox.Apply)
        mccdone.setIcon(QMessageBox.Information)
        mccdone.setText("!")

        @Slot(str)
        def get_path(path):
            self.wait = path
            self.ui.statusbar.showMessage('-- MCC process done --')

            mccdone.setText("MCC process finished")  ## temporary  ## button
            if mccdone.exec_() == QMessageBox.Apply:
                self.open_video_path = path

            ## player restart
            self.startPlayer2()

        @Slot(int)
        def totallen(maxn):
            ## self.total_len = nums
            self.mccbar.setMaximum(maxn)
            ##self.ui.statusbar.showMessage('-- template generated --')

        @Slot(int)
        def prclen(nums):
            ## self.prc_len = nums
            self.mccbar.setValue(nums)

        mccth = MCC(self.open_video_path, parent=self)
        print('mccth videopath: ', time.time() - mcstart)
        mccth.signalLen.connect(totallen)
        mccth.signalPath.connect(get_path)
        mccth.signalPrc.connect(prclen)

        self.ui.statusbar.addWidget(self.mccbar)
        print('addedwidget: ', time.time() - mcstart)
        mccth.mc()
        print('template generated')
        self.ui.statusbar.showMessage('-- MCC process done(2) --')

    # ------------------------------------------------------------------------
    #
    #                              ROI functions
    #
    # ------------------------------------------------------------------------

    # add ROI button clicked
    def addRoi(self):
        self.ui.pushButton_75.setStyleSheet(
            "background-color: %s" % ({True: "", False: "gray"}[self.check_ROI_add]))
        if not self.check_ROI_add:

            self.roi_clicked = self.roi_click(self.player_scene2, self.filter)
            self.roi_clicked.connect(self.addR)

            self.check_ROI_add = True


        else:
            self.check_ROI_add = False
            self.roi_clicked.disconnect()
            self.roi_clicked = None
            self.player_scene2.removeEventFilter(self.filter)

    # add ROI
    def addR(self, scenePos, size=15):  ## 시도
        # num, colr = self.roi_table.add_to_table()
        colr = self.roi_table.randcolr()
        roi_circle = self.create_circle(colr, scenePos, size)
        self.player_scene2.addItem(roi_circle)
        self.roi_table.add_to_table(roi_circle, colr)
        return roi_circle

    #
    def addRoiPolygon(self, x, y, shape, name=""):
        # shape: list of QPointF
        colr = self.roi_table.randcolr()
        roi_polygon = self.create_polygon(colr, x, y, shape)
        self.player_scene2.addItem(roi_polygon)
        self.roi_table.add_to_table(roi_polygon, colr, name)
        return roi_polygon

    def deleteRoi(self):
        rois = self.roi_table.deleteRoi()
        for roi in rois:
            self.player_scene2.removeItem(roi)

    # auto roi by algorithms
    def auto_roi(self):
        if not self.player2:
            return

        if self.ui.comboBox_4.currentText() == 'Caiman-CNMFe':
            dialog = QUiLoader().load('220324_AutoROI_Dialog.ui')
            if dialog.exec() == QDialog.Accepted:
                param_list = []

                param_list.append(int(dialog.lineEdit.text()))  # p

                if dialog.lineEdit_2.text() == 'None':  # K
                    param_list.append(None)
                else:
                    param_list.append(int(dialog.lineEdit_2.text()))

                sig = int(dialog.lineEdit_3.text())
                param_list.append((sig, sig))  # gSig

                siz = int(dialog.lineEdit_4.text())
                param_list.append((siz, siz))  # gSiz

                if dialog.lineEdit_5.text() == 'None':  # Ain
                    param_list.append(None)
                else:
                    param_list.append(int(dialog.lineEdit_5.text()))

                param_list.append(float(dialog.lineEdit_6.text()))  # merge_thr
                param_list.append(int(dialog.lineEdit_7.text()))  # rf
                param_list.append(int(dialog.lineEdit_8.text()))  # stride_cnmf
                param_list.append(int(dialog.lineEdit_9.text()))  # tsub
                param_list.append(int(dialog.lineEdit_10.text()))  # ssub

                if dialog.lineEdit_11.text() == 'None':  # low_rank_background
                    param_list.append(None)
                else:
                    param_list.append(int(dialog.lineEdit_11.text()))

                param_list.append(int(dialog.lineEdit_12.text()))  # gnb
                param_list.append(int(dialog.lineEdit_13.text()))  # nb_patch
                param_list.append(float(dialog.lineEdit_14.text()))  # min_corr
                param_list.append(int(dialog.lineEdit_15.text()))  # min_pnr
                param_list.append(int(dialog.lineEdit_16.text()))  # ssub_B
                param_list.append(float(dialog.lineEdit_17.text()))  # ring_size_factor

                self.caimanpipe(param_list)
            else:
                print('cancel')
        elif self.ui.comboBox_4.currentText() == 'HNCC':
            self.hncc_roi()

    # auto ROI algorithm from CaImAn
    # TODO: Caiman Alg. video loading optimization req
    def caimanpipe(self, param_list):
        if self.player2 is None:
            return

        from caiman_pipeline import Caiman
        cm = Caiman(self, param_list, self.open_video_path, self.player2.fps)
        cm.roi_pos.connect(self.addAutoRoi)
        cm.start_pipeline()

    # auto ROI algorithm from HNCC
    def hncc_roi(self):
        if self.player2 is None:
            return

        from hncc.hncc_roi import Hncc
        hncc_timer = time.time()
        hncc = Hncc()
        res = hncc.auto_roi()

        print('hncc roi process time: ', time.time() - hncc_timer)
        for cell in res:
            if cell[0] - (cell[2] + 4) / 2 < 0 or cell[1] - (cell[2] + 4) / 2 < 0:
                continue
            self.addR(QtCore.QPointF(cell[0], cell[1]), cell[2] + 4)

    def addAutoRoi(self, comps):
        for item in comps:
            centY, centX = item['CoM']
            coors = item['coordinates']
            coors = coors[~np.isnan(coors).any(axis=1)]
            shapeX = coors.T[0]
            shapeY = coors.T[1]
            minx = min(shapeX)
            miny = min(shapeY)
            shape = [QtCore.QPointF(x-minx, y-miny) for x,y in zip(shapeX, shapeY)]
            self.addRoiPolygon(minx, miny, shape)


    # ------------------------------------------------------------------------
    #
    #                                Extraction
    #
    # ------------------------------------------------------------------------
    # offline neuron extraction button clicked
    def neuronExtraction(self):
        if self.player2 is None:
            return

        timer = time.time()
        frame_list = self.player2.frame_list

        itemlist = self.player_scene2.items().copy()

        self.brightlist = []  # store trace value

        for i in range(len(itemlist)-1, -1, -1):
            if itemlist[i].__class__.__name__ == "ROI":
                self.brightlist.append([])
            else:
                itemlist.pop(i)

        if len(itemlist) == 0:
            return

        itemlist.reverse()

        for frame in frame_list:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            for i in range(0, len(itemlist)):
                self.brightlist[i].append(self.getBrightness_v2(frame, itemlist[i]))
                # brightlist[i].append(self.getBrightness(frame, itemlist[i]))

        self.draw_chart(self.brightlist)
        print(f'total time: {time.time() - timer}')

    # initialize and draw offline traces
    def draw_chart(self, brightlist):
        from trace_viewer import Traceviewer
        self.trace_viewer = Traceviewer(brightlist)
        trace_layout = QtWidgets.QHBoxLayout()
        trace_layout.addWidget(self.trace_viewer)
        trace_layout.setContentsMargins(0, 0, 0, 0)

        class ScrollArea(QtWidgets.QScrollArea):
            def eventFilter(self, obj, event):
                if obj == self.verticalScrollBar():
                    if event.type() == QtCore.QEvent.Wheel:
                        return True
                return False

        self.ui.scrollAreaWidgetContents_8 = ScrollArea(self.ui.scrollArea_8)
        scrollWidget = QWidget()
        scrollWidget.setLayout(trace_layout)
        self.ui.scrollAreaWidgetContents_8.setWidget(scrollWidget)
        self.ui.scrollArea_8.setWidget(self.ui.scrollAreaWidgetContents_8)

    def save_trace(self):
        if self.brightlist is None:
            return

        fp, ok = QFileDialog.getSaveFileName(self, "Save file location", "./", "Numpy Files(*.npy)")
        print(fp)
        if ok:
            np.save(fp, np.array(self.brightlist))
            print("Trace saved")
        fn = fp.rsplit('.', maxsplit=1)[0] + '_offline_roi.txt'
        with open(fn, 'w') as f:
            roilist = self.roi_table.itemlist
            for roi in roilist:
                f.write(roi.name + '\n')



    # pre-process for getting item range
    # def getItemRange(self, item):
    #     timer = time.time()
    #     topleft = item.boundingRect().topLeft()
    #     pos = item.pos()
    #     bottomright = item.boundingRect().bottomRight()
    #     rangelist = []
    #
    #     for i in range(int(topleft.x()),int(bottomright.x())):
    #         for j in range(int(topleft.y()), int(bottomright.y())):
    #             pt = QtCore.QPoint(i,j)
    #             if item.contains(pt):
    #                 rangelist.append([i+int(pos.x()),j+int(pos.y())])
    #
    #     print(f'Size: {len(rangelist)}')
    #     print(f'Item Range time: {time.time()-timer}')
    #     return rangelist

    # process for getting average brightness in one frame for a single item
    def getBrightness(self, frame, item):
        x = int(item.pos().x())
        y = int(item.pos().y())
        width = int(item.boundingRect().width())
        height = int(item.boundingRect().height())

        # extract gray value
        imgmat = frame[y:y + height, x:x + width].flatten()

        if torch.cuda.is_available():
            imgmat = torch.tensor(imgmat)
            item_noise = torch.tensor(item.noise)
            item_mat = torch.tensor(item.mat)
        else:
            item_noise = item.noise
            item_mat = item.mat

        noise = imgmat * item_noise
        noise_exist = (item_noise != 0)
        noise_avg = int(noise.sum() / noise_exist.sum())

        # res = imgmat * item.mat
        res = imgmat * item_mat - noise_avg
        res[res < 0] = 0
        exist = (res != 0)
        if exist.sum() == 0:
            avg = 0
        else:
            avg = int(res.sum() / exist.sum())
            avg = avg / noise_avg

        return avg

    def getBrightness_v2(self, frame, item):
        x = int(item.pos().x())
        y = int(item.pos().y())
        outlines = item.contours.copy().reshape((-1, 2))  # 相对坐标

        outlines[:, 0] += x
        outlines[:, 1] += y

        x_min = int(np.min(outlines[:, 0]))
        x_max = int(np.max(outlines[:, 0]))
        y_min = int(np.min(outlines[:, 1]))
        y_max = int(np.max(outlines[:, 1]))
        center_x = x_min + (x_max - x_min) // 2
        center_y = y_min + (y_max - y_min) // 2
        r_cell = (x_max - x_min) // 2
        dist = 5

        xx, yy = np.meshgrid(np.arange(x_min, x_max + 1), np.arange(y_min, y_max + 1))
        distances = np.sqrt((xx - center_x) ** 2 + (yy - center_y) ** 2)
        mask_cell = distances < (x_max - x_min) / 2

        masked_frame = frame[y_min:y_max + 1, x_min:x_max + 1] * mask_cell
        F_cell = np.sum(masked_frame)
        cnt_cell = np.sum(mask_cell)
        F_cell = F_cell / cnt_cell

        x_min = x_min - dist
        x_max = x_max + dist
        y_min = y_min - dist
        y_max = y_max + dist

        xx, yy = np.meshgrid(np.arange(x_min, x_max + 1), np.arange(y_min, y_max + 1))
        distances = np.sqrt((xx - center_x) ** 2 + (yy - center_y) ** 2)
        mask_all = np.logical_and(distances < (x_max - x_min) / 2, distances > r_cell)

        masked_frame = frame[y_min:y_max + 1, x_min:x_max + 1] * mask_all
        F_all = np.sum(masked_frame)
        cnt_all = np.sum(mask_all)
        F_b = F_all / cnt_all

        res = (F_cell - F_b) / F_b
        return res

    #########################################################################
    #                                                                       #
    #                                                                       #
    #                         Online Tab Functions                          #
    #                                                                       #
    #                                                                       #
    #########################################################################

    # ------------------------------------------------------------------------
    #
    #                            player buttons
    #
    # ------------------------------------------------------------------------

    # play/pause button
    def onplayer_pause(self):
        if self.on_scope == None or not self.on_scope.rtProcess:
            return
        text = self.ui.pushButton_129.text()
        if text == 'pause':
            self.on_scope.pause()
            self.ui.pushButton_129.setText('play')
        if text == 'play':
            self.on_scope.play()
            self.ui.pushButton_129.setText('pause')

    # jump to real time button
    def onplayer_rt(self):
        if self.on_scope == None or not self.on_scope.rtProcess:
            return
        self.on_scope.cur_frame = self.on_scope.total_frame
        button = self.ui.pushButton_129
        if button.text() == 'play':
            self.on_scope.play()
            button.setText('pause')

    # camera connect button
    def online_scope(self):
        ## video connect
        text = self.ui.connectScopeCameraButton_2.text()
        if text == 'Scope\nConnect' and self.on_scope is None:
            # camera_ID = self.open_video_path ### temp
            self.on_scope = self.connect_online_camera()
            self.on_scope.frameI.connect(self.online_frame)
            if self.MC is not None and self.on_template is not None:
                self.MC.c_onmc = 0
                self.on_scope.MC = self.MC
                self.on_scope.ged_template = self.on_template

            if self.timermode:
                self.on_scope.timer.start()
            else:
                #self.moveToThread(self.on_scope)
                self.on_scope.start()

            self.ui.connectScopeCameraButton_2.setText('Scope\nDisconnect')

        elif text == 'Scope\nDisconnect' and self.on_scope is not None:
            self.on_scope.frameI.disconnect(self.online_frame)

            if self.timermode:
                self.on_scope.timer.stop()
            else:
                self.on_scope.stop()
                #self.on_scope.quit()

            if self.rt:
                self.rt = False
            self.on_scope = None
            self.ui.connectScopeCameraButton_2.setText('Scope\nConnect')

    # ------------------------------------------------------------------------
    #
    #                           slider functions
    #
    # ------------------------------------------------------------------------

    # on_player sliders
    def onplayer_slider_pressed(self):
        if self.on_scope is not None:
            if self.on_scope.isPlaying:
                self.on_scope.pause()
                self.ui.pushButton_129.setText('play')
            self.slider_lock = True

    def onplayer_slider_released(self):
        self.slider_lock = False

    def onplayer_slider_valueChanged(self, slider_value):
        if self.on_scope is not None:
            if self.slider_lock:
                self.on_scope.cur_frame = slider_value

        ## scope LED slider

    @Slot()
    def move_LEDslider2(self, sl_val):
        print(sl_val)
        print("moved")
        self.ui.scopeLEDvalue_2.setPlaceholderText(str(sl_val))
        self.on_scope.led_status = sl_val

    @Slot()
    def LEDslider2_box(self):
        set_v = int(self.ui.scopeLEDvalue_2.text())
        self.move_LEDslider2(set_v)
        self.ui.scopeLEDslider_2.setValue(set_v)
        self.ui.scopeLEDvalue_2.setText("")

    ## scope Gain slider  #####
    @Slot()
    def move_Gslider2(self, sl_val):
        print(sl_val)
        print("moved")
        self.ui.scopeGainValue_2.setPlaceholderText(str(sl_val))
        self.on_scope.gain_status = sl_val

    @Slot()
    def Gslider2_box(self):
        set_v = int(self.ui.scopeGainValue_2.text())
        # self.ui.scopeGainValue.setPlaceholderText(str(set_v))
        self.move_Gslider2(set_v)
        self.ui.scopeGainSlider_2.setValue(set_v)
        self.ui.scopeGainValue_2.setText("")

    ## scope FR slider
    @Slot()
    def fpsBox_2(self, val):
        val = int(self.ui.FRcomboBox_2.currentText())
        self.on_scope.cfps = val

    ## scope Focus slider
    @Slot()
    def move_Fslider2(self, val):
        print(val)
        print("moved")
        self.ui.scopeFocusValue_2.setPlaceholderText(str(val))
        self.on_scope.focus_status = val

    @Slot()
    def Fslider2_box(self):
        set_v = int(self.ui.scopeFocusValue_2.text())
        # self.ui.scopeExposureValue.setPlaceholderText(str(set_v))
        self.move_Fslider2(set_v)
        self.ui.scopeFocusSlider_2.setValue(set_v)
        self.ui.scopeFocusValue_2.setText("")

    def update_onplayer_slider(self, cur_frame, total_frame, s_timer):
        self.ui.label_176.setText(f'Frame: {cur_frame}')
        self.ui.label_139.setText(f'Frame: {cur_frame}')

        total_time = time.time() - s_timer

        if total_frame == 0:
            cur_time = 0
        else:
            cur_time = total_time * cur_frame / total_frame

        timestr = f'Time: {round(cur_time, 1)}/{round(total_time, 1)} sec'
        cur_time = self.hhmmss(cur_time * 1000)
        total_time = self.hhmmss(total_time * 1000)

        self.ui.label_168.setText(cur_time)
        self.ui.label_174.setText(timestr)

        self.ui.label_136.setText(cur_time)
        self.ui.label_140.setText(timestr)

        if not self.slider_lock:
            self.ui.horizontalSlider_6.setMaximum(total_frame)
            self.ui.horizontalSlider_7.setMaximum(total_frame)
            self.ui.label_173.setText(total_time)
            self.ui.label_137.setText(total_time)

        self.ui.horizontalSlider_7.setValue(cur_frame)
        self.ui.horizontalSlider_6.setValue(cur_frame)

    # ------------------------------------------------------------------------
    #
    #                           motion correction
    #
    # ------------------------------------------------------------------------

    # def test_pre_process(self):
    #     mccdone = QMessageBox()
    #     mccdone.setWindowTitle("notice")
    #     mccdone.setWindowIcon(QtGui.QPixmap("info.png"))
    #     mccdone.setStandardButtons(QMessageBox.Apply | QMessageBox.Close)
    #     mccdone.setDefaultButton(QMessageBox.Apply)
    #     mccdone.setIcon(QMessageBox.Information)
    #     mccdone.setText("MCC process finished")
    #     mccdone.exec_()
    #     return

    def pre_process(self):
        print('preprocess clicked')
        if self.mini_num is None:
            return

        # scope_num = self.open_video_path ##0
        scope_num = self.mini_num + cv2.CAP_DSHOW
        # self.on_template = None

        text = self.ui.connectScopeCameraButton_2.text()
        if self.ui.checkBox_7.isChecked():
            ## video stop
            if text == 'Scope\nDisconnect' and self.on_scope is not None:
                self.on_scope.frameI.disconnect(self.online_frame)
                if self.timermode:
                    self.on_scope.timer.stop()
                else:
                    self.on_scope.stop()
                self.on_scope = None

                self.ui.connectScopeCameraButton_2.setText('Scope\nConnect')


            self.MC = MCC(scope_num, self)

            # d_i ### update policy - 다되면 없애는 거 등 필요 ##
            self.mccbar = QtWidgets.QProgressBar()
            self.ui.statusbar.addWidget(self.mccbar)
            self.mccbar.setMaximum(200)

            self.MC.signalPPe.connect(self.prebar)

            self.on_template = self.MC.g_temp(scope_num)
            print('button preprocess done')
            self.ui.statusbar.showMessage('-- preprocess done --')
        # get crop size
        ## crop_size=self.ui.comboBox_5.currentText()

        # get Neuron Size ##?

        # generate template

    ##prebar
    def prebar(self, n):  ## 중복해결필요    ## 200 template
        self.mccbar.setValue(n)

    # ------------------------------------------------------------------------
    #
    #                           ROI functions
    #
    # ------------------------------------------------------------------------

    # TODO:implement algorithm
    def on_auto_roi(self):
        if self.ui.comboBox_23.currentText() == 'OnACID':
            dialog = QUiLoader().load('220324_AutoROI_Dialog_onacid_for_msCam1.ui')
            if dialog.exec() == QDialog.Accepted:
                param_list = []

                param_list.append(int(dialog.lineEdit.text()))  # fr
                param_list.append(float(dialog.lineEdit_2.text()))  # decay_time

                sig = int(dialog.lineEdit_3.text())
                param_list.append((sig, sig))  # gSig

                param_list.append(int(dialog.lineEdit_4.text()))  # p
                param_list.append(float(dialog.lineEdit_5.text()))  # min_SNR
                param_list.append(float(dialog.lineEdit_6.text()))  # thresh_CNN_noisy
                param_list.append(int(dialog.lineEdit_7.text()))  # gnb
                param_list.append(str(dialog.lineEdit_8.text()))  # init_method
                param_list.append(int(dialog.lineEdit_9.text()))  # init_batch
                param_list.append(int(dialog.lineEdit_10.text()))  # patch_size
                param_list.append(int(dialog.lineEdit_11.text()))  # stride
                param_list.append(int(dialog.lineEdit_12.text()))  # K

                self.onacid(param_list)
            else:
                print('cancel')
        elif self.ui.comboBox_23.currentText() == 'OnACID_mes':
            dialog = QUiLoader().load('220324_AutoROI_Dialog_onacid_mes.ui')
            if dialog.exec() == QDialog.Accepted:
                param_list = []

                param_list.append(int(dialog.lineEdit.text()))  # fr
                param_list.append(float(dialog.lineEdit_2.text()))  # decay_time

                sig = int(dialog.lineEdit_3.text())
                param_list.append((sig, sig))  # gSig

                param_list.append(int(dialog.lineEdit_4.text()))  # p
                param_list.append(float(dialog.lineEdit_5.text()))  # min_SNR
                param_list.append(float(dialog.lineEdit_6.text()))  # ds_factor
                param_list.append(int(dialog.lineEdit_7.text()))  # gnb

                if dialog.checkBox.isChecked():  # mot_corr
                    param_list.append(True)
                else:
                    param_list.append(False)

                if dialog.checkBox_2.isChecked():  # pw_rigid
                    param_list.append(True)
                else:
                    param_list.append(False)

                if dialog.checkBox_3.isChecked():  # sniper_mode
                    param_list.append(True)
                else:
                    param_list.append(False)

                param_list.append(float(dialog.lineEdit_12.text()))  # rval_thr
                param_list.append(int(dialog.lineEdit_13.text()))  # init_batch
                param_list.append(int(dialog.lineEdit_14.text()))  # K
                param_list.append(int(dialog.lineEdit_15.text()))  # epochs

                if dialog.checkBox_4.isChecked():  # show_movie
                    param_list.append(True)
                else:
                    param_list.append(False)

                self.onacidmes(param_list)
            else:
                print('cancel')
        elif self.ui.comboBox_23.currentText() == 'OnACID_batch':
            dialog = QUiLoader().load('220324_AutoROI_Dialog_onacid_batch.ui')
            if dialog.exec() == QDialog.Accepted:
                param_list = []

                param_list.append(int(dialog.lineEdit.text()))  # fr
                param_list.append(float(dialog.lineEdit_2.text()))  # decay_time

                sig = int(dialog.lineEdit_3.text())
                param_list.append((sig, sig))  # gSig

                param_list.append(int(dialog.lineEdit_4.text()))  # p
                param_list.append(float(dialog.lineEdit_5.text()))  # min_SNR
                param_list.append(float(dialog.lineEdit_6.text()))  # ds_factor
                param_list.append(int(dialog.lineEdit_7.text()))  # gnb

                if dialog.checkBox.isChecked():  # mot_corr
                    param_list.append(True)
                else:
                    param_list.append(False)

                if dialog.checkBox_2.isChecked():  # pw_rigid
                    param_list.append(True)
                else:
                    param_list.append(False)

                if dialog.checkBox_3.isChecked():  # sniper_mode
                    param_list.append(True)
                else:
                    param_list.append(False)

                param_list.append(float(dialog.lineEdit_12.text()))  # rval_thr
                param_list.append(int(dialog.lineEdit_13.text()))  # init_batch
                param_list.append(int(dialog.lineEdit_14.text()))  # K
                param_list.append(int(dialog.lineEdit_15.text()))  # epochs

                if dialog.checkBox_4.isChecked():  # show_movie
                    param_list.append(True)
                else:
                    param_list.append(False)

                self.onacidbatch(param_list)
            else:
                print('cancel')

    def onacid(self, param_list):
        if self.on_scope is None:
            camera_ID = self.cameraID
            self.on_scope = OPlayer(camera=camera_ID, lock=self.data_lock, parent=self)
            if self.MC is not None and self.on_template is not None:
                self.MC.c_onmc = 0
                self.on_scope.MC = self.MC
                self.on_scope.ged_template = self.on_template
            self.on_scope.frameI.connect(self.online_frame)

            if self.timermode:
                self.on_scope.timer.start()
            else:
                # self.moveToThread(self.on_scope)
                self.on_scope.start()

            self.ui.connectScopeCameraButton_2.setText('Scope\nDisconnect')


        init_batch = param_list[8]
        frames = []
        for i in range(init_batch):
            ret, frame = self.on_scope.capture.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frames.append(frame.data.obj)
        frames = np.array(frames)

        from caiman_OnACID import Caiman_OnACID
        cm = Caiman_OnACID(self, param_list, self.open_video_path)
        cm.start_pipeline(frames)
        self.on_scope.setAutoROI(cm.online_runner.caiman)
        # self.on_scope.roi_pos.connect(self.addAutoOnRoi)
        # self.on_scope.isAutoROI = True

    def onacidmes(self, param_list):
        if self.on_scope is None:
            camera_ID = self.cameraID
            self.on_scope = OPlayer(camera=camera_ID, lock=self.data_lock, parent=self)
            if self.MC and self.on_template:
                self.on_scope.MC = self.MC
                self.on_scope.ged_template = self.on_template

        init_batch = param_list[11]
        # 强制使用原视频的前200帧初始化，并从201帧开始处理
        # frames = []
        # for i in range(init_batch):
        #     capture = cv2.VideoCapture("C:\\Users\zhuqin\caiman_data\example_movies\demoMovie_out.avi")
        #     ret, frame = capture.read()
        #     # ret, frame = self.on_scope.capture.read()
        #     frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #     frames.append(frame.data.obj)
        # capture.release()
        #
        # from caiman_OnACID_mesoscope import Caiman_OnACID_mes
        # cm = Caiman_OnACID_mes(self, param_list, self.open_video_path)
        # cm.start_pipeline(frames)
        # self.on_scope.setAutoROI(cm.online_runner)
        # self.on_scope.roi_pos.connect(self.addAutoOnRoi)
        # self.on_scope.isAutoROI = True
        # self.on_scope.capture.set(cv2.CAP_PROP_POS_FRAMES, 200)
        # print('Auto ROI init done')

        frames = []
        for i in range(init_batch):
            ret, frame = self.on_scope.capture.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frames.append(frame.data.obj)
        frames = np.array(frames)

        from caiman_OnACID_mesoscope import Caiman_OnACID_mes
        cm = Caiman_OnACID_mes(self, param_list, self.open_video_path)
        cm.start_pipeline(frames)
        self.on_scope.setAutoROI(cm.online_runner.caiman)
        # self.on_scope.roi_pos.connect(self.addAutoOnRoi)
        # self.on_scope.isAutoROI = True
        print('Auto ROI init done')

    def onacidbatch(self, param_list):
        from caiman_online_runner import OnlineRunner
        self.online_runner = OnlineRunner(parent=self, param_list=param_list)
        if self.on_scope is None:
            print('start online scope')
            self.online_scope()

        fps = int(self.on_scope.capture.get(cv2.CAP_PROP_FPS))
        height = int(self.on_scope.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(self.on_scope.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        # size = int(self.on_scope.capture.get(cv2.CAP_PROP_FRAME_COUNT))  # total recorded video length
        size = 1   # for test

        self.online_runner.tempFile(fps, width, height, size)




    # Online Tab add ROI button clicked
    def addOnRoi(self):
        itemlist = self.onplayer_scene.items()
        self.ui.pushButton_122.setStyleSheet(
            "background-color: %s" % ({True: "", False: "gray"}[self.check_onROI_add]))

        if not self.check_onROI_add:
            self.on_roi_clicked = self.roi_click(self.onplayer_scene, self.on_filter)
            self.on_roi_clicked.connect(self.addOnR)
            self.check_onROI_add = True

            if not self.ontrace_viewer:
                self.init_onchart()

        else:
            self.check_onROI_add = False
            self.on_roi_clicked.disconnect()
            self.on_roi_clicked = None
            self.onplayer_scene.removeEventFilter(self.on_filter)

    def addAutoOnRoi(self, comps):
        for item in comps:
            coors = item['coordinates']
            nanIdx = np.where(np.isnan(coors))[0]
            maxRange = nanIdx[1] - nanIdx[0]
            idx = 0
            if len(nanIdx) > 2:
                for i in range(2,len(nanIdx)):
                    r = nanIdx[i] - nanIdx[i-1]
                    if r > maxRange:
                        idx = i-1
                        maxRange = r
                coors = coors[nanIdx[idx]+1:nanIdx[idx+1], :]
            else:
                coors = coors[~np.isnan(coors).any(axis=1)]
            shapeX = coors.T[0]
            shapeY = coors.T[1]

            # smooth polygon
            tck, u = scipy.interpolate.splprep([shapeX, shapeY], s=50)
            out = scipy.interpolate.splev(u, tck)
            shapeX = out[0]
            shapeY = out[1]
            minx = min(shapeX)
            miny = min(shapeY)
            shape = [QtCore.QPointF(x-minx, y-miny) for x,y in zip(shapeX, shapeY)]
            self.addOnRoiPolygon(minx, miny, shape)

    # Online Tab add ROI
    def addOnR(self, scenePos, size=15):
        colr = self.onroi_table.randcolr()
        roi_circle = self.create_circle(colr, scenePos, size)
        self.onplayer_scene.addItem(roi_circle)
        self.onroi_table.add_to_table(roi_circle, colr)
        self.ontrace_viewer.add_trace(roi_circle)
        return roi_circle

    # Online Tab add ROI Polygon
    def addOnRoiPolygon(self, x, y, shape, name=""):
        # shape: list of QPointF
        colr = self.onroi_table.randcolr()
        roi_polygon = self.create_polygon(colr, x, y, shape)
        self.onplayer_scene.addItem(roi_polygon)
        self.onroi_table.add_to_table(roi_polygon, colr, name=name)
        self.ontrace_viewer.add_trace(roi_polygon)
        return roi_polygon

    def deleteOnRoi(self):
        rois = self.onroi_table.deleteRoi()
        for roi in rois:
            self.ontrace_viewer.remove_trace(roi)
            self.onplayer_scene.removeItem(roi)

    # ------------------------------------------------------------------------
    #
    #                          real time process
    #
    # ------------------------------------------------------------------------

    def rt_process(self):
        if self.rt:
            # real-time is processing
            return

        if not self.network_controller:
            self.network_controller = NetworkController(self.ui.ControllerLabel)

        if self.network_controller.dialog.exec() != QDialog.Accepted:
            # cancel
            return

        ## video start
        text = self.ui.connectScopeCameraButton_2.text()
        if text == 'Scope\nConnect' and self.on_scope is None:
            self.on_scope = self.connect_online_camera()

            self.on_scope.frameI.connect(self.online_frame)
            if self.timermode:
                self.on_scope.timer.start()
            else:
                self.on_scope.start()


            self.ui.connectScopeCameraButton_2.setText('Scope\nDisconnect')
            print('connection')

            if self.ui.checkBox_7.isChecked():  ## ?could be pre-checked
                if type(self.on_template) != type(None):
                    print('yes you have template')
                    self.MC.c_onmc = 0  ##
                    self.on_scope.MC = self.MC
                    self.on_scope.ged_template = self.on_template  ###
                    ##self.MCC.on_mc(self.on_template, )
                else:
                    print('no template')
                ## need to check process status of processing (motion corrected | ROI selected)
            else:
                print('check X - motion correction ')


        # self.receiver = DataReceiver(self.ontrace_viewer, self.on_scope.frameG, self.network_controller, self.ui.DecodingText)
        # self.receiver.start()
        self.receiver = ReceiverThread(self.ontrace_viewer, self.on_scope.frameG)
        self.receiver.start()
        #self.on_scope.frameG.connect(self.ontrace_viewer.recieve_img)
        # self.ontrace_viewer.timer_init()
        # self.on_scope.frameG.connect(self.ontrace_viewer.update_chart)

        # self.ui.horizontalSlider_7.setMaximum(1)
        # self.ui.horizontalSlider_7.setValue(1)
        # self.ui.pushButton_129.setText('pause')
        self.on_scope.rtProcess = True
        self.rt = True

    # initialize online trace viewer
    def init_onchart(self):
        from online_trace_viewer import OnTraceviewer
        self.ontrace_viewer = OnTraceviewer(self)
        trace_layout = QtWidgets.QHBoxLayout()
        trace_layout.addWidget(self.ontrace_viewer)
        trace_layout.setContentsMargins(0, 0, 0, 0)

        self.ui.scrollAreaWidgetContents_7.setLayout(trace_layout)
        # random addition for testing
        self.onroi_table.btn1.clicked.connect(self.onroi_table.randomAdd)

    #########################################################################
    #                                                                       #
    #                                                                       #
    #                                Decoding                               #
    #                                                                       #
    #                                                                       #
    #########################################################################

    def decoding(self):
        print('decoding pressed')
        if not self.on_scope.rtProcess:
            print('Start real time process before decoding')
            return

        if not self.receiver.decoding:
            print('Start decoding')
            self.ui.DecodingStatusText.setVisible(True)
            self.receiver.decoder_init()
            self.receiver.decoding_sig.connect(self.decodingText)

    def decodingText(self, v):
        if v:
            self.ui.DecodingText.setVisible(True)
        else:
            self.ui.DecodingText.setVisible(False)

    #########################################################################
    #                                                                       #
    #                                                                       #
    #                           Shared Functions                            #
    #                                                                       #
    #                                                                       #
    #########################################################################

    def connect_online_camera(self):
        if not self.dev_list:
            self.get_devlist()

        camera_ID = self.get_cam_n()
        miniscope = True
        if camera_ID is None:
            camera_ID = self.cameraID  # defalut device, make it seletable in the future
            miniscope = False

        return OPlayer(camera=camera_ID, lock=self.data_lock, parent=self, miniscope=miniscope)
    # time format
    def hhmmss(self, ms):
        ## 1000/60000/360000
        s = round(ms / 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return ("%d:%02d:%02d" % (h, m, s)) if h else ("%d:%02d" % (m, s))

    ## about ui +
    def setupUi(self):
        self.ui = QUiLoader().load('210513_OMBI_UI.ui')  ##'210202_ui.ui') ## "1011_ui.ui")  ##
        self.setCentralWidget(self.ui)
        ## self.show()

    def roi_click(self, widget, filter):  ## widget과 raphicsview 같이 받아서 해보면 어떨까.
        class Filter(QObject):
            clicked = Signal(QtCore.QPointF)

            def eventFilter(self, obj, event):
                if obj == widget:
                    if event.type() == QtCore.QEvent.GraphicsSceneMousePress:  ## mousePressEvent: ## ButtonRelease
                        if obj.sceneRect().contains(event.scenePos()):
                            self.clicked.emit(event.scenePos())
                            print(f'click pos: {event.scenePos()}')
                            return True
                return QObject.eventFilter(self, obj, event)

        filter = Filter(widget)
        widget.installEventFilter(filter)
        return filter.clicked


    def create_circle(self, c, pos, size=15):  ## circle 별도 class 만들어줄지
        r, g, b = c
        # roi_circle = QtWidgets.QGraphicsEllipseItem(0, 0, 30, 30)
        roi_circle = ROI(type=ROIType.CIRCLE, size=size)
        roi_circle.setPen(QtGui.QPen(QtGui.QColor(r, g, b), 1, Qt.SolidLine))
        roi_circle.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        roi_circle.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        roi_circle.setPos(pos.x() - size / 2, pos.y() - size / 2)
        return roi_circle

    def create_polygon(self, c, x, y, shape):
        r, g, b = c
        roi_polygon = ROI(type=ROIType.POLYGON, shape=shape)
        roi_polygon.setPen(QtGui.QPen(QtGui.QColor(r, g, b), 1, Qt.SolidLine))
        roi_polygon.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        roi_polygon.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        roi_polygon.setPos(x, y)
        return roi_polygon

    #########################################################################
    #                                                                       #
    #                                                                       #
    #                           Unused Functions                            #
    #                                                                       #
    #                                                                       #
    #########################################################################

    # def closeEvent(self, event):  ## how-signal ## temp ?
    #     if self.capturer is not None:  ##
    #         self.capturer.stop()  ##? -- stop
    #     QMainWindow.closeEvent(self, event)
    #
    # def closeEvent2(self, event):
    #     if self.capturer2 is not None:
    #         self.capturer2.stop()
    #     QMainWindow.closeEvent2(self, event)
    #
    # def closeEvent3(self, event):
    #     if self.player is not None:
    #         self.player.stop()
    #     QMainWindow.closeEvent3(self, event)
    #
    # @Slot()
    # def save_screen_shot(self):
    #     if self.capturer:
    #         self.capturer.save_one_screen_shot = True
    #     if self.capturer2:
    #         self.capturer2.save_one_screen_shot = True
    #
    # def motion_corr3(self):
    #     # self.ld_play()
    #
    #     self.mcctice = QMessageBox()
    #     self.mcctice.setWindowTitle("motion correction")
    #     self.mcctice.setWindowIcon(QtGui.QPixmap('ldld.gif').scaledToWidth(100))
    #     icon_label = self.mcctice.findChild(QLabel, 'qt_msgbox_icon_label')
    #     movie = QtGui.QMovie('ldld.gif')
    #     setattr(self.mcctice, '', movie)
    #     movie.start()
    #
    #     self.mcctice.setIcon(QMessageBox.Information)
    #     self.mcctice.setText('Loading...')
    #     self.mcctice.exec_()
    #
    #     # time.sleep(5)
    #     print('click')
    #     # self.ld_play()
    #
    #     from mcc_thr2 import MCCThread
    #     _mccthread = MCCThread(self.open_video_path)
    #
    #     self.wait = None
    #
    #     @Slot(str)
    #     def get_path(path):
    #         self.wait = path
    #
    #     while True:
    #         if not _mccthread.isRunning():
    #             if self.wait == None:
    #                 _mccthread.start()
    #                 _mccthread.signalPath.connect(get_path)
    #             # _mccthread.signalPath.emit()
    #         elif self.wait != None:
    #             _mccthread.terminate()
    #             print('exit')
    #             break
    #             # else:
    #
    #     self.mnotice.setText("motion correction saved")
    #     self.mnotice.exec_()
    #
    # def ld_play(self):
    #     print('ldplay', self.m_play_state)
    #     if self.m_play_state:
    #         self.ld_widget.hide()
    #         self.m_label_gif.hide()
    #         self.m_movie_gif.stop()
    #         self.m_play_state = False
    #     else:
    #         self.ld_widget.show()
    #         self.ld_widget.raise_()
    #         self.m_label_gif.show()
    #         self.m_movie_gif.start()
    #         self.m_play_state = True
    #
    #     self.mnotice = QMessageBox()
    #     self.mnotice.setWindowTitle("notice")
    #     self.mnotice.setWindowIcon(QtGui.QPixmap("info.png"))
    #     self.mnotice.setIcon(QMessageBox.Information)
    #     self.mnotice.setText("!")
    #
    # def motion_corr2(self):
    #     from mcc_thr import MCCThread
    #     _mccthread = MCCThread(self.open_video_path)
    #     self.wait = None
    #
    #     self.mnotice.setText("motion correction started")
    #     self.mnotice.exec_()
    #
    #     @Slot(str)
    #     def get_path(path):
    #         self.wait = path
    #
    #     while True:
    #         if not _mccthread.isRunning():
    #             if self.wait == None:
    #                 _mccthread.start()
    #                 _mccthread.signalPath.connect(get_path)
    #             # _mccthread.signalPath.emit()
    #         elif self.wait != None:
    #             _mccthread.terminate()
    #             print('exit')
    #             break
    #             # else:
    #
    #     self.mnotice.setText("motion correction saved")
    #     self.mnotice.exec_()
    #
    # def motion_corr1(self):
    #     import numpy as np
    #     from mcc.correlation_torch import NormXCorr2
    #     import matplotlib.pyplot as plt
    #     import cv2
    #     import time
    #     import torch
    #     from mcc.compute_offset import ApplyShifts
    #     from mcc.LoadData import load_data as ld
    #     from scipy.io import loadmat
    #     import scipy.io as io
    #     import torch.nn as nn
    #     from torch.nn import functional as F
    #     from mcc.NCCRegistration import NCCMotionCorrection as NMC
    #
    #     print('motion correction clicked')
    #     ## load data & set parameters
    #     startX = time.time()
    #
    #     path = self.open_video_path
    #     save_path = self.open_video_path.split('.')[0] + '_mcc.avi'  ## result .avi
    #
    #     crop_size = 150
    #     crop_frame = torch.zeros([crop_size, crop_size], dtype=torch.float)  ## temp 150*150
    #
    #     ldp = ld(path)
    #
    #     raw_video, size1, size2, size3, _, _ = ldp.Trans_GPU(False,
    #                                                          False)  ## ld(path).Trans_GPU(False, False) ## high_filter, crop
    #     sum1, a_rot_complex, b_compex, Zeros, theta, template_buffer = ldp.SetParameters(
    #         crop_frame)  ## ld(path).SetParameters(crop_frame)
    #
    #     new_video = torch.empty([size1, size2, size3], dtype=torch.float)
    #     y_shift = torch.empty([1, size3], dtype=torch.float)
    #     x_shift = torch.empty([1, size3], dtype=torch.float)
    #
    #     input_temp = torch.empty([crop_size, crop_size], dtype=torch.float)
    #
    #     ## data transformation .cuda()
    #
    #     crop_frame = crop_frame.cuda()
    #     new_video = new_video.cuda()
    #     y_shift = y_shift.cuda()
    #     x_shift = x_shift.cuda()
    #     input_temp = input_temp.cuda()
    #     psf = loadmat('psf.mat')
    #     kernel = torch.tensor(np.array(psf.get('psf')), dtype=torch.float)
    #     kernel = kernel.cuda()
    #
    #     ## 100 template generation
    #
    #     init_batch = 100
    #     init_video = raw_video[:, :, 0:init_batch]
    #     filtered_temp = ld.filter_frame(1, init_video[:, :, 0], kernel)
    #     preprocess_temp = ld.cut_frame(1, filtered_temp)
    #     MC = NMC(sum1, a_rot_complex, b_compex, Zeros, theta, template_buffer)
    #     preprocess_temp = MC.generate_template(init_batch, init_video, kernel)  ##
    #
    #     print('preprocessed')
    #     ## NCC registration
    #     startT = time.time()
    #     new_video, x_shift, y_shift = MC.OnlineNCC(raw_video, kernel, preprocess_temp, y_shift, x_shift, new_video)
    #     print(f'ncc registration: {time.time() - startT}s')
    #
    #     new_video = new_video.cpu().numpy()
    #     raw_video = raw_video.cpu().numpy()
    #     x_shift = x_shift.cpu().numpy()
    #     y_shift = y_shift.cpu().numpy()
    #     kernel = kernel.cpu().numpy()
    #
    #     print('starttonow: ', time.time() - startX)
    #
    #     R_new_video = np.array(new_video, dtype='uint8')
    #     writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'DIVX'), 20,
    #                              (752, 480))  ## 'ms_result.avi' ## ***size control
    #     for i in range(999):  ### *** size control
    #         img = cv2.cvtColor(R_new_video[:, :, i], cv2.COLOR_GRAY2BGR)
    #         writer.write(img)
    #     writer.release()
    #
    #     print('until saving: ', time.time() - startX)
    #
    # def motion_corr2(self):
    #     from registration_ed import Preprocess
    #     import cv2
    #     import numpy as np
    #
    #     path = self.open_video_path  ## input path
    #     result = self.open_video_path  ## result .avi
    #     fps = self.ui.scopeFRvalue.placeholderText()
    #
    #     ## prepr=Preprocess()
    #
    #     Preprocess.path = path
    #     Preprocess.result = result
    #
    #     result_tpl = Preprocess.generate_template(path, result)
    #     R_new_video = np.array(new_video, dtype='uint8')
    #     nums, height, width = Preprocess.size
    #     if (nums * height * width) == 0:
    #         print("check your process, template size 0")
    #
    #     else:
    #         mc_writer(nums, height, width, fps, result)
    #
    #     ## save +공유고려
    #     ## 일단 고정 추후 수정 encoder
    #     def mc_writer(self, num, height, width, fps, result):
    #         print(f'savefps: {fps}')
    #         writer = cv2.VideoWriter(result, cv2.VideoWriter_fourcc(*'DIVX'), fps, (width, height))
    #         for i in range(nums):
    #             img = cv2.cvtColor(Rnew_video[:, :, i], cv2.COLOR_GRAY2BGR)
    #             writer.write(img)
    #         writer.release()
    #
    # def push_img(self, state: int, capt: cv2.VideoCapture):
    #
    #     capt.set(cv2.CAP_PROP_POS_FRAMES, state)
    #     while True:
    #         ret, frame = capt.read()

    #########################################################################
    #                                                                       #
    #                                                                       #
    #                               End                                     #
    #                                                                       #
    #                                                                       #
    #########################################################################
