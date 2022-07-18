from PySide2.QtWidgets import (QMainWindow, QSlider, QFileDialog,QTableWidget, QTableWidgetItem,
                                QWidget, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLayout,
                                QHBoxLayout, QLabel)
from PySide2 import QtCore, QtGui
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import QObject, Signal, Slot

from PySide2.QtUiTools import QUiLoader ### +++++++++++++++++++++++++++++++++++++

from PySide2.QtWidgets import QApplication, QDesktopWidget #
from PySide2.QtCore import QFile #

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

#from test_chart2 import make_graph
import time
import numpy as np


### lever -- chart------------
import pandas as pd

## camera number
## from __future__ import print_function
## from pygrabber.dshow_graph import FilterGraph ### and get_devlist()


## status and log
from PySide2.QtWidgets import QMessageBox


## motion correction
from mccc import MCC


from online_player import OPlayer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__() ## //


        #- self.ui = Ui_MainWindow() ## ###+++++++++

        self.setupUi() ############################ +------

        self.on_scope = None
        self.data_lock = QtCore.QMutex()
        self.ui.OnScopeCamButton.clicked.connect(self.online_scope)  ## FTB, saved clip

        self.open_video_path = "C:\\Users\\ZJLAB\\caiman_data\\example_movies\\msCam13.avi"
        #self.open_video_path = "C:\\Users\\ZJLAB\\Desktop\\out_movie.avi"
        self.fakeCapture = False
        self.on_filter = None
        self.ontrace_viewer = None

        self.Statusbar = self.ui.statusBar()

        # on player
        self.onplayer_scene = QGraphicsScene()
        self.ui.scope_camera_view_item_3.setScene(self.onplayer_scene)
        self.onplayer_view = QGraphicsView(self.onplayer_scene, parent=self.ui.scope_camera_view_item_3)
        self.ui.scope_camera_view_item_3.setStyleSheet("background-color: rgb(0,0,0);")
        self.onplayer_view_item = QGraphicsPixmapItem()
        self.onplayer_scene.addItem(self.onplayer_view_item)

        # Processing Option
        self.ui.OnPreProcessingButton.clicked.connect(self.pre_process)
        self.ui.OnRealtimeProcessButton.clicked.connect(self.rt_process)
        self.ui.OnAutoROIButton.clicked.connect(self.on_auto_roi)
##      ## online processing tab -----------------------------------------------------------------

        # ## scope LED slider
        # self.ui.scopeLEDslider_2.valueChanged.connect(self.move_LEDslider2)
        # self.ui.scopeLEDvalue_2.returnPressed.connect(self.LEDslider2_box)
        #
        # ## scope Gain slider
        # self.ui.scopeGainSlider_2.valueChanged.connect(self.move_Gslider2)
        # self.ui.scopeGainValue_2.returnPressed.connect(self.Gslider2_box)
        #
        # ## scope FR slider
        # self.fvalue_2 = [5, 10, 15, 20, 30, 60]
        # self.ui.scopeFRslider_2.valueChanged.connect(self.move_FRslider2)
        # self.ui.scopeFRvalue_2.returnPressed.connect(self.FRslider2_box)
        #
        # ## scope exposure slider
        # self.ui.scopeExposureSlider_2.valueChanged.connect(self.move_Expslider2)
        # self.ui.scopeExposureValue_2.returnPressed.connect(self.Expslider_box)

        # check box check
        # self.ui.checkBox_7
        self.scope_connect = False
        self.on_template = None
        self.playing = False
#         on player buttons
        self.ui.DePlayerPlayButton_3.clicked.connect(self.onplayer_pause)
        self.ui.DePlayerNextButton_3.clicked.connect(self.onplayer_rt)

        # on_ROI
        from roi_table import Table
        self.onroi_table = Table(1, self)
        onroilist_layout = QtWidgets.QVBoxLayout()
        onroilist_layout.addWidget(self.onroi_table)
        self.ui.tab_3.setLayout(onroilist_layout)

        self.check_onROI_add = False
        self.ui.pushButton_75.clicked.connect(self.addOnRoi)
        self.ui.OnROIDeleteButton.clicked.connect(self.deleteOnRoi)

        # on_player slider
        self.slider_lock = False
        self.ui.horizontalSlider_9.sliderPressed.connect(self.onplayer_slider_pressed)
        self.ui.horizontalSlider_9.valueChanged.connect(self.onplayer_slider_valueChanged)
        self.ui.horizontalSlider_9.sliderReleased.connect(self.onplayer_slider_released)

        self.ui.horizontalSlider_6.sliderPressed.connect(self.onplayer_slider_pressed)
        self.ui.horizontalSlider_6.valueChanged.connect(self.onplayer_slider_valueChanged)
        self.ui.horizontalSlider_6.sliderReleased.connect(self.onplayer_slider_released)


# ## neuron extraction
#         self.ui.connectBehaviorCameraButton_10.clicked.connect(self.neuronExtraction)
#         self.trace_viewer = None
#
#         #self.ui.connectBehaviorCameraButton_9.clicked.connect(self.rt_process)
#         # from trace_viewer import Traceviewer
#         # self.trace_viewer = Traceviewer(None)
#         # trace_layout = QtWidgets.QHBoxLayout()
#         # trace_layout.addWidget(self.trace_viewer)
#         # trace_layout.setContentsMargins(0,0,0,0)
#         #
#         # self.ui.scrollAreaWidgetContents_8.setLayout(trace_layout)
#
#
#

#
#         itemlist = self.player_scene2.items()
#         print('item_after: ', itemlist)
#         #print('get pos: ', self.roi_circle.pos(), self.roi_circle2.pos(), self.roi_circle3.pos())
# ##        print('get pos: ', itemlist[0].pos(),itemlist[1].pos(),itemlist[2].pos())
#
#         # item-.isSelected()
#         # item-.isUnderMouse()
#

# ## functions ------------------------------------------------------------------------------------------------------------------------
#     def caimanpipe(self):
#         from caiman_pipeline import Caiman
#         cm = Caiman()
#         cm.start_pipeline()
# ### camera indexing
#     def cam_ix(self):
#         cam_list = []
#         for i in range(len(self.dev_list)):
#             cap = cv2.VideoCapture() ## cv2.CAP_DSHOW + i) ## cap open
#             cap.open(i, cv2.CAP_DSHOW)
#             if cap.read()[0]:
#                 cam_list.append(i)
#                 #cap.read()[0]
#             cap.release() ### --
#         return cam_list
#
#     ### ------ notice f ----
#     @Slot(str)
#     def record_finished(self, a):
#         self.ui.statusbar.showMessage('record finished',10000)
#         self.mnotice.setText(f"record finished \n {a}")
#
#
#
#     ### ------ software system ----
#
#     def d_widget_scope(self):
#         self.ui.widget_9.setEnabled(False)
#     def e_widget_scope(self):
#         self.ui.widget_9.setEnabled(True)
#
#
#     ## about ui +
    def setupUi(self):
        # self.ui = QUiLoader().load('210513_OMBI_UI.ui') ##'210202_ui.ui') ## "1011_ui.ui")  ##
        # self.ui = QUiLoader().load('220216_Offline_edited.ui')  ##'210202_ui.ui') ## "1011_ui.ui")  ##
        self.ui = QUiLoader().load('220216_Online_2_ROIEditShow_updated.ui')
        self.setCentralWidget(self.ui)
        ## self.show()
#
#     ## ------ default setting -----
#
#     def default_fps(self, v):
#         self.ui.scopeFRvalue.setText(str(v))
#         self.slider_box7()
#
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
        mcstart=time.time()
        self.play_finished2()
        print('playfinished2: ', time.time()-mcstart)
        self.wait = None
        self.mccbar = QtWidgets.QProgressBar()
        ## self.mccbar.setMininum(0)

        mccdone = QMessageBox()
        mccdone.setWindowTitle("notice")
        mccdone.setWindowIcon(QtGui.QPixmap("info.png"))
        mccdone.setStandardButtons(QMessageBox.Apply|QMessageBox.Close)
        mccdone.setDefaultButton(QMessageBox.Apply)
        mccdone.setIcon(QMessageBox.Information)
        mccdone.setText("!")

        @Slot(str)
        def get_path(path):
            self.wait = path
            self.ui.statusbar.showMessage('-- MCC process done --')

            mccdone.setText("MCC process finished") ## temporary  ## button
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
        print('mccth videopath: ', time.time()-mcstart)
        mccth.signalLen.connect(totallen)
        mccth.signalPath.connect(get_path)
        mccth.signalPrc.connect(prclen)

        self.ui.statusbar.addWidget(self.mccbar)
        print('addedwidget: ', time.time() - mcstart)
        mccth.mc()
        print('template generated')
        self.ui.statusbar.showMessage('-- MCC process done(2) --')

        #addPermanetWidget()
#     ## ---------   online player    ---------------------------------------------------
    def onplayer_pause(self):
        if self.on_scope == None or not self.on_scope.rtProcess:
            return
        if self.playing:
            self.on_scope.pause()
            self.playing = False
            self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/play.png\")")
        else:
            self.on_scope.play()
            self.playing = True
            self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/pause.png\")")

    def onplayer_rt(self):
        if self.on_scope == None or not self.on_scope.rtProcess:
            return
        self.on_scope.cur_frame = self.on_scope.total_frame

        if not self.playing:
            self.on_scope.play()
            self.playing = True
            self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/pause.png\")")

#     # on_player sliders
    def onplayer_slider_pressed(self):
        if self.on_scope is not None:
            if self.on_scope.isPlaying:
                self.on_scope.pause()
                self.playing = False
                self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/play.png\")")
            self.slider_lock = True

    def onplayer_slider_released(self):
        self.slider_lock = False

    def onplayer_slider_valueChanged(self, slider_value):
        if self.on_scope is not None:
            if self.slider_lock:
                self.on_scope.cur_frame = slider_value

#     ## ---------   online processing   -------------------------------------------------
#     ## scope LED slider
#     @Slot()
#     def move_LEDslider2(self, sl_val):
#         print(sl_val)
#         print("moved")
#         self.ui.scopeLEDvalue_2.setPlaceholderText(str(sl_val))
#         self.on_scope.hue_value = sl_val
#
#     @Slot()
#     def LEDslider2_box(self):
#         set_v = int(self.ui.scopeLEDvalue_2.text())
#         self.move_LEDslider2(set_v)
#         self.ui.scopeLEDslider_2.setValue(set_v)
#         self.ui.scopeLEDvalue_2.setText("")
#
#     ## scope Gain slider  #####
#     @Slot()
#     def move_Gslider2(self, sl_val):
#         print(sl_val)
#         print("moved")
#         self.ui.scopeGainValue_2.setPlaceholderText(str(sl_val))
#         # ab gain scale/
#         # self.capturer2.gain_status = sl_val
#         self.on_scope.gain_status = sl_val
#
#     @Slot()
#     def Gslider2_box(self):
#         set_v = int(self.ui.scopeGainValue_2.text())
#         # self.ui.scopeGainValue.setPlaceholderText(str(set_v))
#         self.move_Gslider2(set_v)
#         self.ui.scopeGainSlider_2.setValue(set_v)
#         self.ui.scopeGainValue_2.setText("")
#
#     ## scope FR slider
#     @Slot()
#     def move_FRslider2(self, sl_val_r):
#         print("dex ", sl_val_r)
#         sl_val = self.fvalue_2[sl_val_r]  # [5,10,15,20,30,60]
#         print(sl_val)
#         print("moved")
#         self.ui.scopeFRvalue_2.setPlaceholderText(str(sl_val))
#         if self.on_scope is not None:
#             self.set_onscope_fps(sl_val)
#
#     @Slot()
#     def FRslider2_box(self):
#         set_v = int(self.ui.scopeFRvalue_2.text())
#         ## self.ui.scopeFRvalue.setPlaceholderText(str(set_v))
#
#         if (set_v / 5 - 1) >= 8:
#             v = 5
#         elif (set_v / 5 - 1) >= 4:
#             v = 4
#         elif (set_v / 5 - 1) < 0:
#             v = 0
#         else:
#             v = int(set_v / 5 - 1)
#         print('v ', v)
#         self.move_FRslider2(v)  # set_v
#         self.ui.scopeFRslider_2.setValue(v)
#         self.ui.scopeFRvalue_2.setText("")
#
#     ## scope Exposure slider
#     @Slot()
#     def move_Expslider2(self, sl_val):
#         print(sl_val)
#         print("moved")
#         self.ui.scopeExposureValue_2.setPlaceholderText(str(sl_val))
#         val = sl_val/100*64
#         self.on_scope.exposure_status = val
#
#     @Slot()
#     def Expslider_box(self):
#         set_v = int(self.ui.scopeExposureValue_2.text())
#         # self.ui.scopeExposureValue.setPlaceholderText(str(set_v))
#         self.move_Expslider2(set_v)
#         self.ui.scopeExposureSlider_2.setValue(set_v)
#         self.ui.scopeExposureValue_2.setText("")
#
#
    def online_scope(self):
        if not self.scope_connect and self.on_scope is None:
            if self.fakeCapture:
                camera_ID = self.open_video_path ### temp
            else:
                camera_ID = 0

            self.on_scope = OPlayer(camera=camera_ID, lock=self.data_lock, parent=self)
            self.on_scope.frameI.connect(self.online_frame)

            self.on_scope.start()
            # self.on_scope.timer.start()

            self.scope_connect = True
            self.playing = True
            self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/pause.png\")")

        elif self.scope_connect and self.on_scope is not None:
            self.on_scope.frameI.disconnect(self.online_frame)

            self.on_scope.stop()
            #self.on_scope.timer.stop()

            self.on_scope = None
            self.scope_connect = False
            self.playing = False
            self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/play.png\")")
#
#     # def test_pre_process(self):
#     #     mccdone = QMessageBox()
#     #     mccdone.setWindowTitle("notice")
#     #     mccdone.setWindowIcon(QtGui.QPixmap("info.png"))
#     #     mccdone.setStandardButtons(QMessageBox.Apply | QMessageBox.Close)
#     #     mccdone.setDefaultButton(QMessageBox.Apply)
#     #     mccdone.setIcon(QMessageBox.Information)
#     #     mccdone.setText("MCC process finished")
#     #     mccdone.exec_()
#     #     return
#
    def pre_process(self):
        print('preprocess clicked')
        if self.fakeCapture:
            scope_num = self.open_video_path ##0
        else:
            scope_num = 0
        #self.on_template = None
        # motion correction box - Hwa? pre-definition

        if self.ui.OnMotionCorrectionCheck.isChecked():
            ## video stop
            if self.scope_connect and self.on_scope is not None:
                self.on_scope.frameI.disconnect(self.online_frame)
                self.on_scope.stop()
                self.on_scope = None
                self.scope_connect = False
                self.playing = False
                self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/play.png\")")

            self.MC = MCC(scope_num, self)

            #d_i ### update policy - 다되면 없애는 거 등 필요 ##
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

    def hhmmss(self, ms):
        ## 1000/60000/360000
        s = round(ms/1000)
        m,s = divmod(s,60)
        h,m = divmod(m,60)
        return ("%d:%02d:%02d" % (h,m,s)) if h else ("%d:%02d" % (m,s))

#     ##prebar
    def prebar(self, n): ## 중복해결필요    ## 200 template

        #d_i
        #c
        self.mccbar.setValue(n)

    def on_auto_roi(self):
        x = [267, 119, 106, 211, 229, 49, 206]
        y = [81, 94, 169, 235, 133, 17, 202]
        for i in range(len(x)):
            self.addOnR(QtCore.QPointF(x[i] + 15.0, y[i] + 15.0))


    def rt_process(self):
        ## video start

        if not self.scope_connect and self.on_scope is None:
            if self.fakeCapture:
                camera_ID = self.open_video_path ### temp
            else:
                camera_ID = 0

            self.on_scope = OPlayer(camera=camera_ID, lock=self.data_lock, parent=self)
            self.on_scope.frameI.connect(self.online_frame)

            # self.on_scope.timer.start()
            self.on_scope.start()

            self.scope_connect = True
            self.playing = True
            self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/pause.png\")")

            print('connection')

        if self.ui.OnMotionCorrectionCheck.isChecked(): ## ?could be pre-checked
            if type(self.on_template) != type(None):
                print('yes you have template')
                self.MC.c_onmc = 0 ##
                self.on_scope.MC = self.MC
                self.on_scope.ged_template = self.on_template ###
                ##self.MCC.on_mc(self.on_template, )
            else: print('no template')
             ## need to check process status of processing (motion corrected | ROI selected)
        else: print('check X - motion correction ')

        # itemlist = self.onplayer_scene.items().copy()
        # rangelist = []  # store area for each item
        #
        # for i in range(len(itemlist) - 1, -1, -1):
        #     if itemlist[i].__class__.__name__ == "ROIcircle":
        #         rangelist.append(self.getItemRange(itemlist[i]))
        #     else:
        #         itemlist.pop(i)
        #
        # if len(itemlist) == 0:
        #     return
        # itemlist.reverse()

        self.on_scope.frameG.connect(self.ontrace_viewer.recieve_img)
        # self.ontrace_viewer.timer_init()
        # self.on_scope.frameG.connect(self.ontrace_viewer.update_chart)

        self.ui.horizontalSlider_9.setMaximum(1)
        self.ui.horizontalSlider_9.setValue(1)
        self.on_scope.rtProcess = True


    @Slot(QtGui.QImage)
    def online_frame(self, image):
        pixmap = QtGui.QPixmap.fromImage(image)
        self.onplayer_view_item.setPixmap(pixmap)
        if self.on_scope.rtProcess:
            self.update_onplayer_slider(self.on_scope.cur_frame, self.on_scope.total_frame, self.on_scope.s_timer)

    def update_onplayer_slider(self, cur_frame, total_frame, s_timer):
        self.ui.DePlayerFrame_3.setText(f'Frame: {cur_frame}')
        self.ui.OffPlayerFrameRight.setText(f'Frame: {cur_frame}')

        total_time = time.time() - s_timer

        if total_frame == 0:
            cur_time = 0
        else:
            cur_time = total_time * cur_frame / total_frame

        timestr = f'Time: {round(cur_time,1)}/{round(total_time,1)} sec'
        cur_time = self.hhmmss(cur_time*1000)
        total_time = self.hhmmss(total_time*1000)

        self.ui.label_179.setText(cur_time)
        self.ui.DePlayerTime_3.setText(timestr)

        self.ui.OffPlayerStartTimeRight.setText(cur_time)
        self.ui.OffPlayerTimeRight.setText(timestr)

        if not self.slider_lock:
            self.ui.horizontalSlider_6.setMaximum(total_frame)
            self.ui.horizontalSlider_9.setMaximum(total_frame)
            self.ui.label_183.setText(total_time)
            self.ui.OffPlayerFinishTimeRight.setText(total_time)

        self.ui.horizontalSlider_9.setValue(cur_frame)
        self.ui.horizontalSlider_6.setValue(cur_frame)


    def addOnRoi(self):

        if not self.check_onROI_add:
            self.on_roi_clicked = self.roi_click(self.onplayer_scene, self.on_filter)
            self.on_roi_clicked.connect(self.addOnR)
            self.ui.pushButton_75.setStyleSheet("background-color: gray")
            self.check_onROI_add = True

            if not self.ontrace_viewer:
                self.init_onchart()
        else:
            self.check_onROI_add = False
            self.on_roi_clicked.disconnect()
            self.on_roi_clicked = None
            self.onplayer_scene.removeEventFilter(self.on_filter)
            self.ui.pushButton_75.setStyleSheet("border-image: url(\"150ppi/Asset 18.png\")")

    def roi_click(self, widget, filter): ## widget과 raphicsview 같이 받아서 해보면 어떨까.
        class Filter(QObject):
            clicked = Signal((QtCore.QPointF))
            def eventFilter(self, obj, event):
                if obj == widget:
                    if event.type() == QtCore.QEvent.GraphicsSceneMousePress: ## mousePressEvent: ## ButtonRelease
                        if obj.sceneRect().contains(event.scenePos()):
                            self.clicked.emit(event.scenePos())
                            print(f'click pos: {event.scenePos()}')
                            return True
                return QObject.eventFilter(self, obj, event)

        filter = Filter(widget)
        widget.installEventFilter(filter)
        return filter.clicked
#
#     def addR(self, scenePos, size=30):  ## 시도
#         #num, colr = self.roi_table.add_to_table()
#         colr = self.roi_table.randcolr()
#         roi_circle = self.create_circle(colr, scenePos, size)
#         self.player_scene2.addItem(roi_circle)
#         self.roi_table.add_to_table(roi_circle, colr)
#
    def addOnR(self, scenePos, size=30):
        colr = self.onroi_table.randcolr()
        roi_circle = self.create_circle(colr, scenePos, size)
        self.onplayer_scene.addItem(roi_circle)
        self.onroi_table.add_to_table(roi_circle, colr)
        self.ontrace_viewer.add_trace(roi_circle)

    def deleteOnRoi(self):
        roi_circle = self.onroi_table.deleteRoi()
        self.ontrace_viewer.remove_trace(roi_circle)
        self.onplayer_scene.removeItem(roi_circle)

    def create_circle(self, c, pos, size):  ## circle 별도 class 만들어줄지
        class ROIconnect(QObject):
            selected = Signal(str)
            moved = Signal(list)
            sizeChange = Signal(int)

        class ROIcircle(QtWidgets.QGraphicsEllipseItem):
            def __init__(self, x, y, w, h):
                super().__init__(x, y, w, h)
                self.signals = ROIconnect()
                self.id = 0
                self.name = None
                self.noise = None
                self.mat = self.matUpdate()

            def setName(self, str):
                self.name = str

            def setId(self, n):
                self.id = n

            def mousePressEvent(self, event):
                super().mousePressEvent(event)
                self.signals.selected.emit(self.name)

            def mouseReleaseEvent(self, event):
                super().mouseReleaseEvent(event)
                x = self.pos().x()
                y = self.pos().y()
                self.signals.moved.emit([x, y])

            def wheelEvent(self, event):
                super().wheelEvent(event)
                size = int(self.rect().width())
                if event.delta() > 0:
                    size += 1
                else:
                    size -= 1
                self.setRect(0, 0, size, size)
                self.signals.sizeChange.emit(size)
                self.mat = self.matUpdate()

            def matUpdate(self):
                h = int(self.rect().height())
                w = int(self.rect().width())
                mat = np.zeros((h, w))
                for i in range(h):
                    for j in range(w):
                        pt = QtCore.QPoint(j, i)
                        if self.contains(pt):
                            mat[i, j] = 1
                self.noise = (mat.copy() - 1) * (-1)
                return mat

        r, g, b = c
        # roi_circle = QtWidgets.QGraphicsEllipseItem(0, 0, 30, 30)
        roi_circle = ROIcircle(0, 0, size, size)
        roi_circle.setPen(QtGui.QPen(QtGui.QColor(r, g, b), 2, Qt.SolidLine))
        roi_circle.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        roi_circle.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        roi_circle.setPos(pos.x() - size / 2, pos.y() - size / 2)
        return roi_circle
#
#     def auto_roi(self):
#         if not self.player2:
#             return
#
#         from caiman_pipeline import Caiman
#         cm = Caiman(self.open_video_path)
#         cm.start_pipeline()
#
#     ## ------------------- Extraction -------------------------##

    def init_onchart(self):
        from online_trace_viewer import OnTraceviewer
        self.ontrace_viewer = OnTraceviewer(self)
        trace_layout = QtWidgets.QHBoxLayout()
        trace_layout.addWidget(self.ontrace_viewer)
        trace_layout.setContentsMargins(0, 0, 0, 0)

        self.ui.scrollArea_7.setLayout(trace_layout)

    # pre-process for getting item range
    def getItemRange(self, item):
        timer = time.time()
        topleft = item.boundingRect().topLeft()
        pos = item.pos()
        bottomright = item.boundingRect().bottomRight()
        rangelist = []

        for i in range(int(topleft.x()),int(bottomright.x())):
            for j in range(int(topleft.y()), int(bottomright.y())):
                pt = QtCore.QPoint(i,j)
                if item.contains(pt):
                    rangelist.append([i+int(pos.x()),j+int(pos.y())])

        print(f'Size: {len(rangelist)}')
        print(f'Item Range time: {time.time()-timer}')
        return rangelist

    # process for getting average brightness in one frame for a single item
    def getBrightness(self, frame, item, area):
        sum = 0
        for pos in area:
            sum += frame[pos[1]][pos[0]][2]
        mean = sum/len(area)
        return mean