import os
import time

import cv2
import numpy as np
import torch
# from vplayer import VPlayerThread, VPlayerStatus
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Slot, Signal, QObject, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QDialog
from PySide2.QtWidgets import QFileDialog, QGraphicsScene, QGraphicsPixmapItem, QMessageBox
from PySide2.QtWidgets import QMainWindow, QWidget

from offline.ROI import ROIType, ROI
from vplayer import VPlayerStatus, VPlayer


## scope_video_view_item

class MainWindow(QMainWindow):
	def __init__(self, indep=False):
		super().__init__()
		self.indep = indep
		ui_path = '220929_Offline_iconUpdated.ui' #'220614_Offline_edited_fonted.ui' # '220614_Offline_edited.ui'
		self.setupUi(ui_path)

	# 	# button connection
	# 	self.offline.OffLoadVideoButton.clicked.connect(self.load_video)
	# 	self.offline.OffMotionCorrectionButton.clicked.connect(self.motion_corr)
	#
	# 	# initalize
	# 	self.data_lock = QMutex()
	# 	self.player = None
	#
	# 	self.player_scene = QGraphicsScene()
	# 	self.offline.scope_video_view_item.setScene(self.player_scene)
	# 	self.player_view_item = QGraphicsPixmapItem()
	# 	self.player_scene.addItem(self.player_view_item)
	#
	# 	self.offline.off_play_button.clicked.connect(self.play_button_clicked) ## pause
	# 	self.offline.off_next_button.clicked.connect(self.next_button_clicked)
	# 	self.offline.off_stop_button.clicked.connect(self.stop_button_clicked)
	# 	self.offline.off_slower_button.clicked.connect(self.slower_button_clicked)
	# 	self.offline.off_faster_button.clicked.connect(self.faster_button_clicked)
	#
	# def play_button_clicked(self): ## pause
	# 	pass
	# def next_button_clicked(self):
	# 	pass
	# def stop_button_clicked(self):
	# 	pass
	# def slower_button_clicked(self):
	# 	pass
	# def faster_button_clicked(self):
	# 	pass
		self.ui.OffLoadVideoButton.clicked.connect(self.load_video)  ### UI - need to change the name
		## motion correction --------------------------------------*****--------------------------
		self.ui.OffMotionCorrectionButton.clicked.connect(self.motion_corr)
		self.open_video_path = ''

		## player2
		self.player2 = None
		self.fin_record_status2 = False  ##- next function

		self.s_total2 = 0
		self.s_totalframe2 = 0
		self.present_time2 = 0

		self.temp_width = 0
		## -- window size width
		self.pl_width = 0

		self.pl_width2 = 0

		self.player_scene2 = QGraphicsScene()
		self.ui.scope_video_view_item.setScene(self.player_scene2)  ##-
		self.player_view2 = None
		self.player_view_item_i2 = QGraphicsPixmapItem()
		self.player_scene2.addItem(self.player_view_item_i2)

		self.playing = False
		self.filter = None

		self.data_lock = QtCore.QMutex()  # thread-vari.

		self.ui.off_play_button.clicked.connect(self.play_button_clicked2)
		self.ui.off_stop_button.clicked.connect(self.stop_button_clicked2)
		self.ui.off_faster_button.clicked.connect(self.play_finished2)
		self.ui.off_next_button.clicked.connect(self.after_player2)

		## player2 slider
		self.ui.horizontalSlider_10.sliderPressed.connect(self.player2slider_pressed)
		self.ui.horizontalSlider_10.valueChanged.connect(self.player2slider_valueChanged)
		self.ui.horizontalSlider_10.sliderReleased.connect(self.player2slider_released)

		self.ui.horizontalSlider_6.sliderPressed.connect(self.player2slider_pressed)
		self.ui.horizontalSlider_6.valueChanged.connect(self.player2slider_valueChanged)
		self.ui.horizontalSlider_6.sliderReleased.connect(self.player2slider_released)
		## ---- ROI
		from roi_table import Table
		self.roi_table = Table(0, self)
		# self.ui.tab_16.layout = QtWidgets.QVBoxLayout(self)
		roilist_layout = QtWidgets.QVBoxLayout()
		roilist_layout.addWidget(self.roi_table)
		self.ui.tab_16.setLayout(roilist_layout)

		# roilist_layout = QtWidgets.QVBoxLayout()
		# roilist_layout.addWidget(self.roi_table)
		# self.ui.tab_18.setLayout(roilist_layout)

		## ROI function
		self.check_ROI_add = False
		self.ui.pushButton_75.clicked.connect(self.addRoi)
		self.ui.OffROIDeleteButton.clicked.connect(self.deleteRoi)

		boundingRect = self.player_scene2.itemsBoundingRect()  ##여기서 하면, frame 좌표로 생성
		self.player_scene2.setSceneRect(0, 0, boundingRect.right(), boundingRect.bottom())

		## AUTO ROI function
		self.ui.connectBehaviorCameraButton_8.clicked.connect(self.auto_roi)

		## neuron extraction
		self.ui.OffNeuronExtractionButton.clicked.connect(self.neuronExtraction)
		self.trace_viewer = None

	# player2 slider
	def player2slider_pressed(self):
		if self.player2 is not None:
			if self.player2.vplayer_status == VPlayerStatus.STARTING:
				self.player2.vplayer_status = VPlayerStatus.PAUSING
				self.playing = False
				self.ui.pushButton_2.setStyleSheet("border-image: url(\"150ppi/play.png\")")

	def player2slider_released(self):
		if self.player2 is not None:
			self.player2.frame_update()

	def player2slider_valueChanged(self, slider_value):
		if self.player2 is not None:
			if self.player2.vplayer_status == VPlayerStatus.STARTING:
				self.player2.next_frame = slider_value - 1
			else:
				self.player2.set_frame(slider_value - 1)
				self.player2.frame_update()

	def auto_roi(self):
		dialog = QUiLoader().load(self.indep_path('220929_AutoROI_Dialog_layoutUpdated.ui'))
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

	def caimanpipe(self, param_list):
		if self.player2 is None:
			return

		from caiman_pipeline import Caiman
		cm = Caiman(self, param_list, self.open_video_path, self.player2.fps)
		cm.roi_pos.connect(self.addAutoRoi)
		cm.start_pipeline()

	def addRoi(self):
		if not self.check_ROI_add:
			self.ui.pushButton_75.setStyleSheet("border-image: url(\"150ppi/Asset 18_pre.png\")")
			self.roi_clicked = self.roi_click(self.player_scene2, self.filter)
			self.roi_clicked.connect(self.addR)
			self.check_ROI_add = True
		else:
			self.check_ROI_add = False
			self.roi_clicked.disconnect()
			self.roi_clicked = None
			self.player_scene2.removeEventFilter(self.filter)
			self.ui.pushButton_75.setStyleSheet("border-image: url(\"150ppi/Asset 18.png\")")

	def addAutoRoi(self, comps):
		for item in comps:
			centY, centX = item['CoM']
			coors = item['coordinates']
			coors = coors[~np.isnan(coors).any(axis=1)]
			shapeX = coors.T[0]
			shapeY = coors.T[1]
			minx = min(shapeX)
			miny = min(shapeY)
			shape = [QtCore.QPointF(x - minx, y - miny) for x, y in zip(shapeX, shapeY)]
			self.addRoiPolygon(minx, miny, shape)

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

	def addR(self, scenePos, size=30):  ## 시도
		# num, colr = self.roi_table.add_to_table()
		colr = self.roi_table.randcolr()
		roi_circle = self.create_circle(colr, scenePos, size)
		self.player_scene2.addItem(roi_circle)
		self.roi_table.add_to_table(roi_circle, colr)

	def addRoiPolygon(self, x, y, shape):
		# shape: list of QPointF
		colr = self.roi_table.randcolr()
		roi_polygon = self.create_polygon(colr, x, y, shape)
		self.player_scene2.addItem(roi_polygon)
		self.roi_table.add_to_table(roi_polygon, colr)
		return roi_polygon

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

	def deleteRoi(self):
		roi_circle = self.roi_table.deleteRoi()
		self.player_scene2.removeItem(roi_circle)

	## ---- funtions

	def load_video(self):
		self.open_video_path = str(
			QFileDialog.getOpenFileName(self, "select media file", './', 'Video (*.mp4 *.wma *.avi)')[
				0])  ## 형식*, Qurl 기본폴더
		print(f'selected file: {self.open_video_path}')

		self.startPlayer2()  ##

	def startPlayer2(self):

		# video2 = cv2.VideoCapture(self.open_video_path)
		# video2_fps = video2.get(cv2.CAP_PROP_FPS)
		#
		# self.player2 = VPlayer(v_path=self.open_video_path, lock=self.data_lock, parent=self, fps = video2_fps) ##* get fps
		self.player2 = VPlayer(v_path=self.open_video_path, lock=self.data_lock, parent=self)
		self.player2.start()
		self.player2.frameC.connect(self.update_player_frame2)

		time.sleep(0.5)

		self.s_totalframe2 = self.player2.total_frame
		self.s_total2 = int(self.s_totalframe2 / self.player2.fps)

		self.update_v_duration2(self.s_total2, self.s_totalframe2)

	def hhmmss(self, ms):
		## 1000/60000/360000
		s = round(ms / 1000)
		m, s = divmod(s, 60)
		h, m = divmod(m, 60)
		return ("%d:%02d:%02d" % (h, m, s)) if h else ("%d:%02d" % (m, s))

	## player2
	def stop_button_clicked2(self, a):
		if self.player2 is not None:
			self.player2.vplayer_status = VPlayerStatus.STOPPING  ## vplayer _
			self.playing = False
			self.ui.pushButton_2.setStyleSheet("border-image: url(\"150ppi/play.png\")")
			self.ui.horizontalSlider_10.setValue(0)  ##_
			print("set stopping")
		if a == 1:
			self.player2.stateCh.disconnect(self.stop_button_clicked2)

	## player2
	def frame_slider_update2(self, present_f):
		## if self.player is not None:
		self.ui.horizontalSlider_10.blockSignals(True)  ##_
		self.ui.horizontalSlider_10.setValue(present_f)  ##_
		self.ui.horizontalSlider_10.blockSignals(False)  ##_

		self.ui.horizontalSlider_6.blockSignals(True)  ##_
		self.ui.horizontalSlider_6.setValue(present_f)  ##_
		self.ui.horizontalSlider_6.blockSignals(False)  ##_
		print(f'sliderposition: {present_f}')
		self.frame_slider_update_p2(present_f)

	## player2
	def frame_slider_update_p2(self, present_f):
		self.ui.label_209.setText(f'Frame: {int(present_f)}')  # _72
		self.ui.OffPlayerFrameRight.setText(f'Frame: {int(present_f)}')

		# time update
		present_time = self.player2.total_time * present_f / self.player2.total_frame
		timestr = "Time: " + str(round(present_time, 1)) + "/" + str(round(self.player2.total_time, 1)) + "sec"
		self.ui.label_174.setText(timestr)
		self.ui.OffPlayerTimeRight.setText(timestr)
		timestr = self.player2.time_format(int(present_time))
		self.ui.label_204.setText(timestr)
		self.ui.OffPlayerStartTimeRight.setText(timestr)

	## player2
	def update_v_duration2(self, duration, f_duration):

		self.ui.horizontalSlider_10.setMaximum(f_duration)  ## see max ##_
		self.ui.horizontalSlider_6.setMaximum(f_duration)
		print(f'set maxvalue: {f_duration}')
		if duration >= 0:
			self.ui.label_206.setText(self.player2.time_format(duration))  ## _15
			self.ui.OffPlayerFinishTimeRight.setText(self.player2.time_format(duration))

	## duration update
	## label_206 _last 00:00 ## _206

	## player2
	@Slot()
	def play_finished2(self):
		if self.player2 is not None:
			self.player2.stop()
			self.player2 = None
			print("OK")
			self.fin_record_status2 = True

	## player2
	@Slot()
	def play_finished2(self):
		if self.player2 is not None:
			self.player2.stop()
			self.player2 = None
			print("OK")
			self.fin_record_status2 = True

	##player2
	def after_player2(self):
		self.play_finished2()
		self.ui.tabWidget.setCurrentIndex(3)

	## player2
	@Slot(QtGui.QImage)
	def update_player_frame2(self, image):
		pixmap = QtGui.QPixmap.fromImage(image)
		## width control
		self.player_view2 = self.ui.scope_video_view_item
		pl_width = self.player_view2.width()  # view?
		if self.pl_width2 != pl_width:
			self.pl_width2 = pl_width
			print('plW', self.pl_width2)
		self.player_view_item_i2.setPixmap(pixmap)
		self.frame_slider_update2(self.player2.present_frame)

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

	# addPermanetWidget()

	@Slot()
	def play_button_clicked2(self):
		text = self.ui.pushButton_2.text()
		if self.player2 is not None and not self.playing:
			# self.player2.frameC.connect(self.update_player_frame2)
			self.player2.vplayer_status = VPlayerStatus.STARTING
			print("set starting")
			self.playing = True
			self.ui.off_play_button.setStyleSheet("border-image: url(\"150ppi/pause.png\")")
		elif self.player2 is not None and self.playing:
			self.player2.vplayer_status = VPlayerStatus.PAUSING
			# self.player2.frameC.disconnect(self.update_player_frame2)
			print("set pausing")
			self.playing = False
			self.ui.off_play_button.setStyleSheet("border-image: url(\"150ppi/play.png\")")

	# self.player2.stateCh.connect(self.stop_button_clicked2)

	## ---- ROI

	## ------------------- Extraction -------------------------##
	def neuronExtraction(self):
		if self.player2 is None:
			return

		timer = time.time()
		frame_list = self.player2.frame_list

		itemlist = self.player_scene2.items().copy()

		brightlist = []  # store brightness

		for i in range(len(itemlist) - 1, -1, -1):
			if itemlist[i].__class__.__name__ == "ROI":
				brightlist.append([])
			else:
				itemlist.pop(i)

		if len(itemlist) == 0:
			return

		itemlist.reverse()
		for frame in frame_list:
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			for i in range(0, len(itemlist)):
				brightlist[i].append(self.getBrightness(frame, itemlist[i]))

		self.draw_chart(brightlist)
		print(f'total time: {time.time() - timer}')

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

		self.ui.scrollAreaWidgetContents_7 = ScrollArea(self.ui.scrollArea_7)
		scrollWidget = QWidget()
		scrollWidget.setLayout(trace_layout)
		self.ui.scrollAreaWidgetContents_7.setWidget(scrollWidget)
		self.ui.scrollArea_7.setWidget(self.ui.scrollAreaWidgetContents_7)

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


###################################################
###      frame update for vplayer
### get, take signals for vplayer

		#self.update_v_duration~

	def indep_path(self, path_):
		if not self.indep:
			path_ = os.path.join('offline', path_)
		return path_

	def setupUi(self, u_path):
		ui_path = u_path
		ui_path = self.indep_path(ui_path)

		self.ui = QUiLoader().load(ui_path) ##'220216_Offline_edited.ui')
		self.setCentralWidget(self.ui)


#

#
# class OldWindow(QMainWindow):
# 	def __init__(self):
# 		super().__init__()
# 		self.setupUi()
#
# 		self.ui.OffLoadVideoButton.clicked.connect(self.load_video)  ### UI - need to change the name
# 		## motion correction --------------------------------------*****--------------------------
# 		self.ui.OffMotionCorrectionButton.clicked.connect(self.motion_corr)
# 		self.open_video_path = ''
#
# 		## player2
# 		self.player2 = None
# 		self.fin_record_status2 = False  ##- next function
#
# 		self.s_total2 = 0
# 		self.s_totalframe2 = 0
# 		self.present_time2 = 0
#
# 		self.temp_width = 0
# 		## -- window size width
# 		self.pl_width = 0
#
# 		self.pl_width2 = 0
#
# 		self.player_scene2 = QGraphicsScene()
# 		self.ui.scope_video_view_item.setScene(self.player_scene2)  ##-
# 		self.player_view2 = None
# 		self.player_view_item_i2 = QGraphicsPixmapItem()
# 		self.player_scene2.addItem(self.player_view_item_i2)
#
# 		self.playing = False
# 		self.filter = None
#
# 		self.data_lock = QtCore.QMutex()  # thread-vari.
#
# 		## edit ui - player2
# 		# self.ui.pushButton_4.setText('OK')
# 		# self.ui.pushButton_68.setText('Next')
# 		# self.ui.pushButton_2.setText('play')
# 		# self.ui.pushButton_6.setText('stop')
#
# 		self.ui.off_play_button.clicked.connect(self.play_button_clicked2)
# 		self.ui.off_stop_button.clicked.connect(self.stop_button_clicked2)
# 		self.ui.off_faster_button.clicked.connect(self.play_finished2)
# 		self.ui.off_next_button.clicked.connect(self.after_player2)
#
# 		## player2 slider
# 		self.ui.horizontalSlider_10.sliderPressed.connect(self.player2slider_pressed)
# 		self.ui.horizontalSlider_10.valueChanged.connect(self.player2slider_valueChanged)
# 		self.ui.horizontalSlider_10.sliderReleased.connect(self.player2slider_released)
#
# 		self.ui.horizontalSlider_6.sliderPressed.connect(self.player2slider_pressed)
# 		self.ui.horizontalSlider_6.valueChanged.connect(self.player2slider_valueChanged)
# 		self.ui.horizontalSlider_6.sliderReleased.connect(self.player2slider_released)
# 		## ---- ROI
# 		from roi_table import Table
# 		self.roi_table = Table(0, self)
# 		# self.ui.tab_16.layout = QtWidgets.QVBoxLayout(self)
# 		roilist_layout = QtWidgets.QVBoxLayout()
# 		roilist_layout.addWidget(self.roi_table)
# 		self.ui.tab_16.setLayout(roilist_layout)
#
# 		# roilist_layout = QtWidgets.QVBoxLayout()
# 		# roilist_layout.addWidget(self.roi_table)
# 		# self.ui.tab_18.setLayout(roilist_layout)
#
# 		## ROI function
# 		self.check_ROI_add = False
# 		self.ui.pushButton_75.clicked.connect(self.addRoi)
# 		self.ui.OffROIDeleteButton.clicked.connect(self.deleteRoi)
#
# 		boundingRect = self.player_scene2.itemsBoundingRect()  ##여기서 하면, frame 좌표로 생성
# 		self.player_scene2.setSceneRect(0, 0, boundingRect.right(), boundingRect.bottom())
#
# 		## AUTO ROI function
# 		self.ui.connectBehaviorCameraButton_8.clicked.connect(self.auto_roi)
#
# 		## neuron extraction
# 		self.ui.OffNeuronExtractionButton.clicked.connect(self.neuronExtraction)
# 		self.trace_viewer = None
#
# 	# player2 slider
# 	def player2slider_pressed(self):
# 		if self.player2 is not None:
# 			if self.player2.vplayer_status == VPlayerStatus.STARTING:
# 				self.player2.vplayer_status = VPlayerStatus.PAUSING
# 				self.playing = False
# 				self.ui.pushButton_2.setStyleSheet("border-image: url(\"150ppi/play.png\")")
#
# 	def player2slider_released(self):
# 		if self.player2 is not None:
# 			self.player2.frame_update()
#
# 	def player2slider_valueChanged(self, slider_value):
# 		if self.player2 is not None:
# 			if self.player2.vplayer_status == VPlayerStatus.STARTING:
# 				self.player2.next_frame = slider_value - 1
# 			else:
# 				self.player2.set_frame(slider_value - 1)
# 				self.player2.frame_update()
#
# 	def auto_roi(self):
# 		dialog = QUiLoader().load('220324_AutoROI_Dialog.ui')
# 		if dialog.exec() == QDialog.Accepted:
# 			param_list = []
#
# 			param_list.append(int(dialog.lineEdit.text()))  # p
#
# 			if dialog.lineEdit_2.text() == 'None':  # K
# 				param_list.append(None)
# 			else:
# 				param_list.append(int(dialog.lineEdit_2.text()))
#
# 			sig = int(dialog.lineEdit_3.text())
# 			param_list.append((sig, sig))  # gSig
#
# 			siz = int(dialog.lineEdit_4.text())
# 			param_list.append((siz, siz))  # gSiz
#
# 			if dialog.lineEdit_5.text() == 'None':  # Ain
# 				param_list.append(None)
# 			else:
# 				param_list.append(int(dialog.lineEdit_5.text()))
#
# 			param_list.append(float(dialog.lineEdit_6.text()))  # merge_thr
# 			param_list.append(int(dialog.lineEdit_7.text()))  # rf
# 			param_list.append(int(dialog.lineEdit_8.text()))  # stride_cnmf
# 			param_list.append(int(dialog.lineEdit_9.text()))  # tsub
# 			param_list.append(int(dialog.lineEdit_10.text()))  # ssub
#
# 			if dialog.lineEdit_11.text() == 'None':  # low_rank_background
# 				param_list.append(None)
# 			else:
# 				param_list.append(int(dialog.lineEdit_11.text()))
#
# 			param_list.append(int(dialog.lineEdit_12.text()))  # gnb
# 			param_list.append(int(dialog.lineEdit_13.text()))  # nb_patch
# 			param_list.append(float(dialog.lineEdit_14.text()))  # min_corr
# 			param_list.append(int(dialog.lineEdit_15.text()))  # min_pnr
# 			param_list.append(int(dialog.lineEdit_16.text()))  # ssub_B
# 			param_list.append(float(dialog.lineEdit_17.text()))  # ring_size_factor
#
# 			self.caimanpipe(param_list)
#
# 	def caimanpipe(self, param_list):
# 		if self.player2 is None:
# 			return
#
# 		from caiman_pipeline import Caiman
# 		cm = Caiman(self, param_list, self.open_video_path, self.player2.fps)
# 		cm.roi_pos.connect(self.addAutoRoi)
# 		cm.start_pipeline()
#
# 	def addRoi(self):
# 		if not self.check_ROI_add:
# 			self.ui.pushButton_75.setStyleSheet("background-color: gray")
# 			self.roi_clicked = self.roi_click(self.player_scene2, self.filter)
# 			self.roi_clicked.connect(self.addR)
# 			self.check_ROI_add = True
# 		else:
# 			self.check_ROI_add = False
# 			self.roi_clicked.disconnect()
# 			self.roi_clicked = None
# 			self.player_scene2.removeEventFilter(self.filter)
# 			self.ui.pushButton_75.setStyleSheet("border-image: url(\"150ppi/Asset 18.png\")")
#
# 	def addAutoRoi(self, comps):
# 		for item in comps:
# 			centY, centX = item['CoM']
# 			coors = item['coordinates']
# 			coors = coors[~np.isnan(coors).any(axis=1)]
# 			shapeX = coors.T[0]
# 			shapeY = coors.T[1]
# 			size = max([max(shapeX) - min(shapeX), max(shapeY) - min(shapeY)])
# 			pos = QtCore.QPointF(centX, centY)
# 			self.addR(pos, size)
#
# 	def roi_click(self, widget, filter):  ## widget과 raphicsview 같이 받아서 해보면 어떨까.
# 		class Filter(QObject):
# 			clicked = Signal((QtCore.QPointF))
#
# 			def eventFilter(self, obj, event):
# 				if obj == widget:
# 					if event.type() == QtCore.QEvent.GraphicsSceneMousePress:  ## mousePressEvent: ## ButtonRelease
# 						if obj.sceneRect().contains(event.scenePos()):
# 							self.clicked.emit(event.scenePos())
# 							print(f'click pos: {event.scenePos()}')
# 							return True
# 				return QObject.eventFilter(self, obj, event)
#
# 		filter = Filter(widget)
# 		widget.installEventFilter(filter)
# 		return filter.clicked
#
# 	def addR(self, scenePos, size=30):  ## 시도
# 		# num, colr = self.roi_table.add_to_table()
# 		colr = self.roi_table.randcolr()
# 		roi_circle = self.create_circle(colr, scenePos, size)
# 		self.player_scene2.addItem(roi_circle)
# 		self.roi_table.add_to_table(roi_circle, colr)
#
# 	def create_circle(self, c, pos, size):  ## circle 별도 class 만들어줄지
# 		class ROIconnect(QObject):
# 			selected = Signal(str)
# 			moved = Signal(list)
# 			sizeChange = Signal(int)
#
# 		class ROIcircle(QtWidgets.QGraphicsEllipseItem):
# 			def __init__(self, x, y, w, h):
# 				super().__init__(x, y, w, h)
# 				self.signals = ROIconnect()
# 				self.id = 0
# 				self.name = None
# 				self.noise = None
# 				self.mat = self.matUpdate()
#
# 			def setName(self, str):
# 				self.name = str
#
# 			def setId(self, n):
# 				self.id = n
#
# 			def mousePressEvent(self, event):
# 				super().mousePressEvent(event)
# 				self.signals.selected.emit(self.name)
#
# 			def mouseReleaseEvent(self, event):
# 				super().mouseReleaseEvent(event)
# 				x = self.pos().x()
# 				y = self.pos().y()
# 				self.signals.moved.emit([x, y])
#
# 			def wheelEvent(self, event):
# 				super().wheelEvent(event)
# 				size = int(self.rect().width())
# 				if event.delta() > 0:
# 					size += 1
# 				else:
# 					size -= 1
# 				self.setRect(0, 0, size, size)
# 				self.signals.sizeChange.emit(size)
# 				self.mat = self.matUpdate()
#
# 			def matUpdate(self):
# 				h = int(self.rect().height())
# 				w = int(self.rect().width())
# 				mat = np.zeros((h, w))
# 				for i in range(h):
# 					for j in range(w):
# 						pt = QtCore.QPoint(j, i)
# 						if self.contains(pt):
# 							mat[i, j] = 1
# 				self.noise = (mat.copy() - 1) * (-1)
# 				return mat
#
# 		r, g, b = c
# 		# roi_circle = QtWidgets.QGraphicsEllipseItem(0, 0, 30, 30)
# 		roi_circle = ROIcircle(0, 0, size, size)
# 		roi_circle.setPen(QtGui.QPen(QtGui.QColor(r, g, b), 2, Qt.SolidLine))
# 		roi_circle.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
# 		roi_circle.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
# 		roi_circle.setPos(pos.x() - size / 2, pos.y() - size / 2)
# 		return roi_circle
#
# 	def deleteRoi(self):
# 		roi_circle = self.roi_table.deleteRoi()
# 		self.player_scene2.removeItem(roi_circle)
#
# 	## ---- funtions
#
# 	def load_video(self):
# 		self.open_video_path = str(
# 			QFileDialog.getOpenFileName(self, "select media file", './', 'Video (*.mp4 *.wma *.avi)')[
# 				0])  ## 형식*, Qurl 기본폴더
# 		print(f'selected file: {self.open_video_path}')
#
# 		self.startPlayer2()  ##
#
# 	def startPlayer2(self):
#
# 		# video2 = cv2.VideoCapture(self.open_video_path)
# 		# video2_fps = video2.get(cv2.CAP_PROP_FPS)
# 		#
# 		# self.player2 = VPlayer(v_path=self.open_video_path, lock=self.data_lock, parent=self, fps = video2_fps) ##* get fps
# 		self.player2 = VPlayer(v_path=self.open_video_path, lock=self.data_lock, parent=self)
# 		self.player2.start()
# 		self.player2.frameC.connect(self.update_player_frame2)
#
# 		time.sleep(0.1)
#
# 		self.s_totalframe2 = self.player2.total_frame
# 		self.s_total2 = int(self.s_totalframe2 / self.player2.fps)
#
# 		self.update_v_duration2(self.s_total2, self.s_totalframe2)
#
# 	def hhmmss(self, ms):
# 		## 1000/60000/360000
# 		s = round(ms / 1000)
# 		m, s = divmod(s, 60)
# 		h, m = divmod(m, 60)
# 		return ("%d:%02d:%02d" % (h, m, s)) if h else ("%d:%02d" % (m, s))
#
# 	## player2
# 	def stop_button_clicked2(self, a):
# 		if self.player2 is not None:
# 			self.player2.vplayer_status = VPlayerStatus.STOPPING  ## vplayer _
# 			self.playing = False
# 			self.ui.pushButton_2.setStyleSheet("border-image: url(\"150ppi/play.png\")")
# 			self.ui.horizontalSlider_10.setValue(0)  ##_
# 			print("set stopping")
# 		if a == 1:
# 			self.player2.stateCh.disconnect(self.stop_button_clicked2)
#
# 	## player2
# 	def frame_slider_update2(self, present_f):
# 		## if self.player is not None:
# 		self.ui.horizontalSlider_10.blockSignals(True)  ##_
# 		self.ui.horizontalSlider_10.setValue(present_f)  ##_
# 		self.ui.horizontalSlider_10.blockSignals(False)  ##_
#
# 		self.ui.horizontalSlider_6.blockSignals(True)  ##_
# 		self.ui.horizontalSlider_6.setValue(present_f)  ##_
# 		self.ui.horizontalSlider_6.blockSignals(False)  ##_
# 		print(f'sliderposition: {present_f}')
# 		self.frame_slider_update_p2(present_f)
#
# 	## player2
# 	def frame_slider_update_p2(self, present_f):
# 		self.ui.label_209.setText(f'Frame: {int(present_f)}')  # _72
# 		self.ui.OffPlayerFrameRight.setText(f'Frame: {int(present_f)}')
#
# 		# time update
# 		present_time = self.player2.total_time * present_f / self.player2.total_frame
# 		timestr = "Time: " + str(round(present_time, 1)) + "/" + str(round(self.player2.total_time, 1)) + "sec"
# 		self.ui.label_174.setText(timestr)
# 		self.ui.OffPlayerTimeRight.setText(timestr)
# 		timestr = self.player2.time_format(int(present_time))
# 		self.ui.label_204.setText(timestr)
# 		self.ui.OffPlayerStartTimeRight.setText(timestr)
#
# 	## player2
# 	def update_v_duration2(self, duration, f_duration):
#
# 		self.ui.horizontalSlider_10.setMaximum(f_duration)  ## see max ##_
# 		self.ui.horizontalSlider_6.setMaximum(f_duration)
# 		print(f'set maxvalue: {f_duration}')
# 		if duration >= 0:
# 			self.ui.label_206.setText(self.player2.time_format(duration))  ## _15
# 			self.ui.OffPlayerFinishTimeRight.setText(self.player2.time_format(duration))
#
# 	## duration update
# 	## label_206 _last 00:00 ## _206
#
# 	## player2
# 	@Slot()
# 	def play_finished2(self):
# 		if self.player2 is not None:
# 			self.player2.stop()
# 			self.player2 = None
# 			print("OK")
# 			self.fin_record_status2 = True
#
# 	## player2
# 	@Slot()
# 	def play_finished2(self):
# 		if self.player2 is not None:
# 			self.player2.stop()
# 			self.player2 = None
# 			print("OK")
# 			self.fin_record_status2 = True
#
# 	##player2
# 	def after_player2(self):
# 		self.play_finished2()
# 		self.ui.tabWidget.setCurrentIndex(3)
#
# 	## player2
# 	@Slot(QtGui.QImage)
# 	def update_player_frame2(self, image):
# 		pixmap = QtGui.QPixmap.fromImage(image)
# 		## width control
# 		self.player_view2 = self.ui.scope_video_view_item
# 		pl_width = self.player_view2.width()  # view?
# 		if self.pl_width2 != pl_width:
# 			self.pl_width2 = pl_width
# 			print('plW', self.pl_width2)
# 		self.player_view_item_i2.setPixmap(pixmap)
# 		self.frame_slider_update2(self.player2.present_frame)
#
# 	def motion_corr(self):
# 		# loading bar signal
# 		# motion correction
# 		from mccc import MCC
# 		mcstart = time.time()
# 		self.play_finished2()
# 		print('playfinished2: ', time.time() - mcstart)
# 		self.wait = None
# 		self.mccbar = QtWidgets.QProgressBar()
#
# 		## self.mccbar.setMininum(0)
# 		mccdone = QMessageBox()
# 		mccdone.setWindowTitle("notice")
# 		mccdone.setWindowIcon(QtGui.QPixmap("info.png"))
# 		mccdone.setStandardButtons(QMessageBox.Apply | QMessageBox.Close)
# 		mccdone.setDefaultButton(QMessageBox.Apply)
# 		mccdone.setIcon(QMessageBox.Information)
# 		mccdone.setText("!")
#
# 		@Slot(str)
# 		def get_path(path):
# 			self.wait = path
# 			self.ui.statusbar.showMessage('-- MCC process done --')
#
# 			mccdone.setText("MCC process finished")  ## temporary  ## button
# 			if mccdone.exec_() == QMessageBox.Apply:
# 				self.open_video_path = path
#
# 			## player restart
# 			self.startPlayer2()
#
# 		@Slot(int)
# 		def totallen(maxn):
# 			## self.total_len = nums
# 			self.mccbar.setMaximum(maxn)
#
# 		##self.ui.statusbar.showMessage('-- template generated --')
#
# 		@Slot(int)
# 		def prclen(nums):
# 			## self.prc_len = nums
# 			self.mccbar.setValue(nums)
#
# 		mccth = MCC(self.open_video_path, parent=self)
# 		print('mccth videopath: ', time.time() - mcstart)
# 		mccth.signalLen.connect(totallen)
# 		mccth.signalPath.connect(get_path)
# 		mccth.signalPrc.connect(prclen)
#
# 		self.ui.statusbar.addWidget(self.mccbar)
# 		print('addedwidget: ', time.time() - mcstart)
# 		mccth.mc()
# 		print('template generated')
# 		self.ui.statusbar.showMessage('-- MCC process done(2) --')
#
# 	# addPermanetWidget()
#
# 	@Slot()
# 	def play_button_clicked2(self):
# 		text = self.ui.pushButton_2.text()
# 		if self.player2 is not None and not self.playing:
# 			# self.player2.frameC.connect(self.update_player_frame2)
# 			self.player2.vplayer_status = VPlayerStatus.STARTING
# 			print("set starting")
# 			self.playing = True
# 			self.ui.off_play_button.setStyleSheet("border-image: url(\"150ppi/pause.png\")")
# 		elif self.player2 is not None and self.playing:
# 			self.player2.vplayer_status = VPlayerStatus.PAUSING
# 			# self.player2.frameC.disconnect(self.update_player_frame2)
# 			print("set pausing")
# 			self.playing = False
# 			self.ui.off_play_button.setStyleSheet("border-image: url(\"150ppi/play.png\")")
#
# 	# self.player2.stateCh.connect(self.stop_button_clicked2)
#
# 	## ---- ROI
#
# 	## ------------------- Extraction -------------------------##
# 	def neuronExtraction(self):
# 		if self.player2 is None:
# 			return
#
# 		timer = time.time()
# 		frame_list = self.player2.frame_list
#
# 		itemlist = self.player_scene2.items().copy()
#
# 		brightlist = []  # store brightness
#
# 		for i in range(len(itemlist) - 1, -1, -1):
# 			if itemlist[i].__class__.__name__ == "ROIcircle":
# 				brightlist.append([])
# 			else:
# 				itemlist.pop(i)
#
# 		if len(itemlist) == 0:
# 			return
#
# 		itemlist.reverse()
# 		for frame in frame_list:
# 			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
# 			for i in range(0, len(itemlist)):
# 				brightlist[i].append(self.getBrightness(frame, itemlist[i]))
#
# 		self.draw_chart(brightlist)
# 		print(f'total time: {time.time() - timer}')
#
# 	def draw_chart(self, brightlist):
# 		from trace_viewer import Traceviewer
# 		self.trace_viewer = Traceviewer(brightlist)
# 		trace_layout = QtWidgets.QHBoxLayout()
# 		trace_layout.addWidget(self.trace_viewer)
# 		trace_layout.setContentsMargins(0, 0, 0, 0)
#
# 		class ScrollArea(QtWidgets.QScrollArea):
# 			def eventFilter(self, obj, event):
# 				if obj == self.verticalScrollBar():
# 					if event.type() == QtCore.QEvent.Wheel:
# 						return True
# 				return False
#
# 		self.ui.scrollAreaWidgetContents_7 = ScrollArea(self.ui.scrollArea_7)
# 		scrollWidget = QWidget()
# 		scrollWidget.setLayout(trace_layout)
# 		self.ui.scrollAreaWidgetContents_7.setWidget(scrollWidget)
# 		self.ui.scrollArea_7.setWidget(self.ui.scrollAreaWidgetContents_7)
#
# 	# process for getting average brightness in one frame for a single item
# 	def getBrightness(self, frame, item):
# 		x = int(item.pos().x())
# 		y = int(item.pos().y())
# 		width = int(item.rect().width())
# 		height = int(item.rect().height())
#
# 		# extract gray value
# 		imgmat = frame[y:y + height, x:x + width]
#
# 		noise = imgmat * item.noise
# 		noise_exist = (item.noise != 0)
# 		noise_avg = int(noise.sum() / noise_exist.sum())
#
# 		# res = imgmat * item.mat
# 		res = imgmat * item.mat - noise_avg
# 		res[res < 0] = 0
# 		exist = (res != 0)
# 		if exist.sum() == 0:
# 			avg = 0
# 		else:
# 			avg = int(res.sum() / exist.sum())
#
# 		return avg
#
# 	## ---- ui setup
# 	def setupUi(self):
# 		self.ui = QUiLoader().load(
# 			# '210802_Offline.ui')
# 			'220614_Offline_edited_fonted.ui')
# 		self.setCentralWidget(self.ui)
