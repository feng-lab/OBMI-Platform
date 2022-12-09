import time

import cv2
import numpy as np
import scipy
from PySide2.QtWidgets import QMainWindow, QDialog
from PySide2.QtUiTools import QUiLoader
import os

from online.ROI import ROI, ROIType
from online.caiman_online_runner import OnlineRunner
from online.data_receiver import ReceiverThread

from PySide2.QtWidgets import QFileDialog, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem
from PySide2.QtCore import Slot, QObject, Signal, Qt
from PySide2 import QtCore, QtGui, QtWidgets
from online_player import OPlayer
#from online_player_multiprocess import OPlayer
from mccc import MCC
import iconlist_iconUpdated


class MainWindow(QMainWindow):
	def __init__(self, indep=False):
		super().__init__()
		self.indep = indep
		ui_path = '220929_Online_2_ROIEditShow_iconUpdated.ui' #220705_Online_2_ROIEditShow_edited.ui #'220425_Online_3_ScopeConnectShow_edited.ui'
		self.setupUi(ui_path)
		self.on_scope = None
		self.data_lock = QtCore.QMutex()
		self.ui.OnScopeCamButton.clicked.connect(self.online_scope)  ## FTB, saved clip

		self.open_video_path = "C:\\Users\\ZJLAB\\caiman_data\\example_movies\\msCam13.avi"
		# self.open_video_path = "C:\\Users\\ZJLAB\\Desktop\\out_movie.avi"
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
		# self.ui.OnRealtimeProcessButton.clicked.connect(self.rt_process)
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
		self.auto_roi_process = False
		self.scope_connect = False
		self.on_template = None
		self.playing = False
		self.MC = None
		self.timermode = True
		self.cameraID = 0
		#         on player buttons
		#         self.ui.DePlayerPlayButton_3.clicked.connect(self.onplayer_pause)
		#         self.ui.DePlayerNextButton_3.clicked.connect(self.onplayer_rt)

		# on_ROI
		from roi_table import Table
		self.onroi_table = Table(1, self)
		onroilist_layout = QtWidgets.QVBoxLayout()
		onroilist_layout.addWidget(self.onroi_table)
		self.ui.roi_tab.setLayout(onroilist_layout)

		self.check_onROI_add = False
		self.ui.pushButton_134.clicked.connect(self.addOnRoi)
		self.ui.OffROIDeleteButton_5.clicked.connect(self.deleteOnRoi)

		# on_player slider
		self.slider_lock = False
		# self.ui.horizontalSlider_9.sliderPressed.connect(self.onplayer_slider_pressed)
		# self.ui.horizontalSlider_9.valueChanged.connect(self.onplayer_slider_valueChanged)
		# self.ui.horizontalSlider_9.sliderReleased.connect(self.onplayer_slider_released)
		#
		# self.ui.horizontalSlider_6.sliderPressed.connect(self.onplayer_slider_pressed)
		# self.ui.horizontalSlider_6.valueChanged.connect(self.onplayer_slider_valueChanged)
		# self.ui.horizontalSlider_6.sliderReleased.connect(self.onplayer_slider_released)
		self.init_onchart()


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

	# def motion_corr(self):
	#     # loading bar signal
	#     # motion correction
	#     from mccc import MCC
	#     mcstart=time.time()
	#     self.play_finished2()
	#     print('playfinished2: ', time.time()-mcstart)
	#     self.wait = None
	#     self.mccbar = QtWidgets.QProgressBar()
	#     ## self.mccbar.setMininum(0)
	#
	#     mccdone = QMessageBox()
	#     mccdone.setWindowTitle("notice")
	#     mccdone.setWindowIcon(QtGui.QPixmap("info.png"))
	#     mccdone.setStandardButtons(QMessageBox.Apply|QMessageBox.Close)
	#     mccdone.setDefaultButton(QMessageBox.Apply)
	#     mccdone.setIcon(QMessageBox.Information)
	#     mccdone.setText("!")
	#
	#     @Slot(str)
	#     def get_path(path):
	#         self.wait = path
	#         self.ui.statusbar.showMessage('-- MCC process done --')
	#
	#         mccdone.setText("MCC process finished") ## temporary  ## button
	#         if mccdone.exec_() == QMessageBox.Apply:
	#             self.open_video_path = path
	#
	#         ## player restart
	#         self.startPlayer2()
	#
	#
	#     @Slot(int)
	#     def totallen(maxn):
	#         ## self.total_len = nums
	#         self.mccbar.setMaximum(maxn)
	#         ##self.ui.statusbar.showMessage('-- template generated --')
	#
	#     @Slot(int)
	#     def prclen(nums):
	#         ## self.prc_len = nums
	#         self.mccbar.setValue(nums)
	#
	#     mccth = MCC(self.open_video_path, parent=self)
	#     print('mccth videopath: ', time.time()-mcstart)
	#     mccth.signalLen.connect(totallen)
	#     mccth.signalPath.connect(get_path)
	#     mccth.signalPrc.connect(prclen)
	#
	#     self.ui.statusbar.addWidget(self.mccbar)
	#     print('addedwidget: ', time.time() - mcstart)
	#     mccth.mc()
	#     print('template generated')
	#     self.ui.statusbar.showMessage('-- MCC process done(2) --')

	# addPermanetWidget()
	#     ## ---------   online player    ---------------------------------------------------
	#     def onplayer_pause(self):
	#         if self.on_scope == None or not self.on_scope.rtProcess:
	#             return
	#         if self.playing:
	#             self.on_scope.pause()
	#             self.playing = False
	#             self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/play.png\")")
	#         else:
	#             self.on_scope.play()
	#             self.playing = True
	#             self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/pause.png\")")
	#
	#     def onplayer_rt(self):
	#         if self.on_scope == None or not self.on_scope.rtProcess:
	#             return
	#         self.on_scope.cur_frame = self.on_scope.total_frame
	#
	#         if not self.playing:
	#             self.on_scope.play()
	#             self.playing = True
	#             self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/pause.png\")")
	#
	# #     # on_player sliders
	#     def onplayer_slider_pressed(self):
	#         if self.on_scope is not None:
	#             if self.on_scope.isPlaying:
	#                 self.on_scope.pause()
	#                 self.playing = False
	#                 self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/play.png\")")
	#             self.slider_lock = True
	#
	#     def onplayer_slider_released(self):
	#         self.slider_lock = False
	#
	#     def onplayer_slider_valueChanged(self, slider_value):
	#         if self.on_scope is not None:
	#             if self.slider_lock:
	#                 self.on_scope.cur_frame = slider_value

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
				camera_ID = self.open_video_path  ### temp
			else:
				camera_ID = 0

			self.on_scope = OPlayer(camera=camera_ID, lock=self.data_lock, parent=self)
			self.on_scope.frameI.connect(self.online_frame)

			if self.MC is not None and self.on_template is not None:
				self.MC.c_onmc = 0
				self.on_scope.MC = self.MC
				self.on_scope.ged_template = self.on_template

			if self.timermode:
				self.on_scope.timer.start()
			else:
				# self.moveToThread(self.on_scope)
				self.on_scope.start()

			self.scope_connect = True
			self.playing = True
			self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/pause.png\")")

		elif self.scope_connect and self.on_scope is not None:
			self.on_scope.frameI.disconnect(self.online_frame)

			if self.auto_roi_process:
				self.on_scope.autoROI.stop()
				self.auto_roi_process = False

			if self.timermode:
				self.on_scope.timer.stop()
			else:
				self.on_scope.stop()

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
		scope_num = self.cameraID + cv2.CAP_DSHOW

		if self.ui.OnMotionCorrectionCheck.isChecked():
			## video stop
			if self.scope_connect and self.on_scope is not None:
				self.on_scope.frameI.disconnect(self.online_frame)
				if self.timermode:
					self.on_scope.timer.stop()
				else:
					self.on_scope.stop()
				self.on_scope = None
				self.scope_connect = False
				self.playing = False
				self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/play.png\")")

			self.MC = MCC(scope_num, self)

			# d_i ### update policy - 다되면 없애는 거 등 필요 ##
			self.mccbar = QtWidgets.QProgressBar()
			self.ui.statusbar.addWidget(self.mccbar)
			self.mccbar.setMaximum(200)

			self.MC.signalPPe.connect(self.prebar)

			self.on_template = self.MC.g_temp(scope_num)
			print('button preprocess done')
			self.ui.statusbar.showMessage('-- preprocess done --')

	def hhmmss(self, ms):
		## 1000/60000/360000
		s = round(ms / 1000)
		m, s = divmod(s, 60)
		h, m = divmod(m, 60)
		return ("%d:%02d:%02d" % (h, m, s)) if h else ("%d:%02d" % (m, s))

	#     ##prebar
	def prebar(self, n):  ## 중복해결필요    ## 200 template
		self.mccbar.setValue(n)

	def on_auto_roi(self):
		if self.ui.comboBox_23.currentText() == 'OnACID':
			dialog = QUiLoader().load(self.indep_path('220929_AutoROI_Dialog_onacid_for_msCam1_layoutUpdated.ui'))
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
			dialog = QUiLoader().load(self.indep_path('220929_AutoROI_Dialog_onacid_layoutUpdated.ui'))
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
			dialog = QUiLoader().load(self.indep_path('220929_AutoROI_Dialog_onacid_batch_layoutUpdated.ui'))
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

			self.scope_connect = True
			#self.ui.connectScopeCameraButton_2.setText('Scope\nDisconnect')

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
		self.auto_roi_process = True

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
		self.online_runner = OnlineRunner(parent=self, param_list=param_list)
		if self.on_scope is None:
			print('start online scope')
			self.online_scope()

		fps = int(self.on_scope.capture.get(cv2.CAP_PROP_FPS))
		height = int(self.on_scope.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
		width = int(self.on_scope.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
		# size = int(self.on_scope.capture.get(cv2.CAP_PROP_FRAME_COUNT))  # total recorded video length
		size = 1  # for test

		self.online_runner.tempFile(fps, width, height, size)

	def rt_process(self):
		## video start

		if not self.scope_connect and self.on_scope is None:
			camera_ID = self.cameraID

			self.on_scope = OPlayer(camera=camera_ID, lock=self.data_lock, parent=self)
			self.on_scope.frameI.connect(self.online_frame)

			if self.timermode:
				self.on_scope.timer.start()
			else:
				self.on_scope.start()

			self.scope_connect = True
			self.playing = True
			self.ui.DePlayerPlayButton_3.setStyleSheet("border-image: url(\"150ppi/pause.png\")")

			print('connection')

		if self.auto_roi_process:
			self.on_scope.autoROI.stop()
			self.auto_roi_process = False

		if self.ui.OnMotionCorrectionCheck.isChecked():  ## ?could be pre-checked
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

		# self.on_scope.frameG.connect(self.ontrace_viewer.recieve_img)
		# self.ontrace_viewer.timer_init()
		# self.on_scope.frameG.connect(self.ontrace_viewer.update_chart)
		self.thread = ReceiverThread(self.ontrace_viewer, self)
		self.thread.start()
		self.ui.horizontalSlider_9.setMaximum(1)
		self.ui.horizontalSlider_9.setValue(1)
		self.on_scope.rtProcess = True

	@Slot(QtGui.QImage)
	def online_frame(self, image):
		print('get image')
		pixmap = QtGui.QPixmap.fromImage(image)
		self.onplayer_view_item.setPixmap(pixmap)
		# if self.on_scope.rtProcess:
		# 	self.update_onplayer_slider(self.on_scope.cur_frame, self.on_scope.total_frame, self.on_scope.s_timer)

	def update_onplayer_slider(self, cur_frame, total_frame, s_timer):
		self.ui.DePlayerFrame_3.setText(f'Frame: {cur_frame}')
		self.ui.OffPlayerFrameRight.setText(f'Frame: {cur_frame}')

		total_time = time.time() - s_timer

		if total_frame == 0:
			cur_time = 0
		else:
			cur_time = total_time * cur_frame / total_frame

		timestr = f'Time: {round(cur_time, 1)}/{round(total_time, 1)} sec'
		cur_time = self.hhmmss(cur_time * 1000)
		total_time = self.hhmmss(total_time * 1000)

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
			self.ui.pushButton_134.setStyleSheet("background-color: gray")
			self.check_onROI_add = True

			if not self.ontrace_viewer:
				self.init_onchart()
		else:
			self.check_onROI_add = False
			self.on_roi_clicked.disconnect()
			self.on_roi_clicked = None
			self.onplayer_scene.removeEventFilter(self.on_filter)
			self.ui.pushButton_134.setStyleSheet("border-image: url(\"150ppi/Asset 18.png\")")

	def addAutoOnRoi(self, comps):
		for item in comps:
			coors = item['coordinates']
			nanIdx = np.where(np.isnan(coors))[0]
			maxRange = nanIdx[1] - nanIdx[0]
			idx = 0
			if len(nanIdx) > 2:
				for i in range(2, len(nanIdx)):
					r = nanIdx[i] - nanIdx[i - 1]
					if r > maxRange:
						idx = i - 1
						maxRange = r
				coors = coors[nanIdx[idx] + 1:nanIdx[idx + 1], :]
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
			shape = [QtCore.QPointF(x - minx, y - miny) for x, y in zip(shapeX, shapeY)]
			self.addOnRoiPolygon(minx, miny, shape)

	def roi_click(self, widget, filter):  ## widget과 raphicsview 같이 받아서 해보면 어떨까.
		class Filter(QObject):
			clicked = Signal((QtCore.QPointF))

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

	# Online Tab add ROI Polygon
	def addOnRoiPolygon(self, x, y, shape):
		# shape: list of QPointF
		colr = self.onroi_table.randcolr()
		roi_polygon = self.create_polygon(colr, x, y, shape)
		self.onplayer_scene.addItem(roi_polygon)
		self.onroi_table.add_to_table(roi_polygon, colr)
		self.ontrace_viewer.add_trace(roi_polygon)
		return roi_polygon

	def deleteOnRoi(self):
		roi_circle = self.onroi_table.deleteRoi()
		self.ontrace_viewer.remove_trace(roi_circle)
		self.onplayer_scene.removeItem(roi_circle)

	def create_circle(self, c, pos, size=30):  ## circle 별도 class 만들어줄지
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

	#     ## ------------------- Extraction -------------------------##

	def init_onchart(self):
		from online_trace_viewer import OnTraceviewer
		self.ontrace_viewer = OnTraceviewer(self)
		trace_layout = QtWidgets.QHBoxLayout()
		trace_layout.addWidget(self.ontrace_viewer)
		trace_layout.setContentsMargins(0, 0, 0, 0)

		self.ui.scrollArea_7.setLayout(trace_layout)

	def indep_path(self, path_):
		if not self.indep:
			path_ = os.path.join('online', path_)
		return path_

	def setupUi(self, ui_path):
		#ui_path = '210802_Online_1_Hide.ui'
		#ui_path = '210802_Online_2_ROIEditShow.ui'
		#ui_path = '220216_Online_3_ScopeConnectShow_edited.ui'
		ui_path = self.indep_path(ui_path)

		## expand version -> default hide 방식으로. 
		#self.online1 = QUiLoader().load()
		#self.online2 = QUiLoader().load()
		self.ui = QUiLoader().load(ui_path)
		self.setCentralWidget(self.ui)
