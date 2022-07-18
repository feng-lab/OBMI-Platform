from PySide2.QtWidgets import QMainWindow
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import Slot, QTime
from PySide2 import QtCore, QtGui
import cv2

from PySide2.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
									 QHBoxLayout, QMessageBox, QLabel, QWidget)

from capture_thread import VideoSavingStatus, CaptureThread

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setupUi()

		self.daq.DAQScopeViewPanel.hide()

		# Behavior Camera Connection
		self.behavior_cam = None
		self.behavior_camera_status = False
		self.behavior_camera_number = 0
		self.daq.DAQBehCamButton.clicked.connect(self.connect_behavior_camera_button_clicked)
		self.daq.DAQBehCamPanel.setEnabled(False)	
		# Scope Camera Connection
		self.scope_cam = None
		self.scope_camera_status = False
		self.scope_camera_number = 1
		self.daq.DAQScopeCamButton.clicked.connect(self.connect_scope_camera_button_clicked)
		self.daq.DAQScopeCamPanel.setEnabled(False)
		# Camera Setting
		self.data_lock = QtCore.QMutex()
		print(f'data_lock QMutex: {id(self.data_lock)}')
		self.data_lock2 = QtCore.QMutex()
		print(f'data_lock2 QMutex: {id(self.data_lock2)}')
		
		self.DAQBehCamView = self.daq.DAQBehCamView
		self.DAQBehCamScene = QGraphicsScene()
		self.DAQBehCamView.setScene(self.DAQBehCamScene)
		self.DAQBehCamItem = QGraphicsPixmapItem()
		self.DAQBehCamScene.addItem(self.DAQBehCamItem)

		self.DAQScopeCamView = self.daq.DAQScopeCamView
		self.DAQScopeCamScene = QGraphicsScene()
		self.DAQScopeCamView.setScene(self.DAQScopeCamScene)
		self.DAQScopeCamItem = QGraphicsPixmapItem()
		self.DAQScopeCamScene.addItem(self.DAQScopeCamItem)

		# Recording Function Connection
		self.user_path = None
		self.project_name = ''
		self.save_format = 'avi'
		self.daq.DAQRecordButton.clicked.connect(self.recording_start_stop)
		## Recoding option - duration on/off
		self.daq.DAQRecordDurationCheckbox.clicked.connect(self.set_duration)

		# Slider Control (#returnPressed)
		## Behavior Exposure Slider
		self.behavior_camera_exposure_value = 0
		self.daq.DAQBehExposureValue.editingFinished.connect(self.bcam_exposure_box_changed)
		self.daq.DAQBehExposureSlider.valueChanged.connect(self.bcam_exposure_slider_changed)
		## Scope LED Power Slider
		self.scope_camera_LED_value = 0
		self.daq.DAQScopeLEDValue.editingFinished.connect(self.scam_LED_box_changed)
		self.daq.DAQScopeLEDSlider.valueChanged.connect(self.scam_LED_slider_changed)
		## Scope Gain Slider
		self.scope_camera_gain_value = 0
		self.daq.DAQScopeGainValue.editingFinished.connect(self.scam_gain_box_changed)
		self.daq.DAQScopeGainSlider.valueChanged.connect(self.scam_gain_slider_changed)
		## Scope Exposure Slider
		self.scope_camera_exposure_value = 0
		self.daq.DAQScopeExposureValue.editingFinished.connect(self.scam_exposure_box_changed)
		self.daq.DAQScopeExposureSlider.valueChanged.connect(self.scam_exposure_slider_changed)
		## Scope Frame rate (*need to check about Hardware and CountedValue)
		self.frame_rate_list = [5,10,15,20,30,60]
		self.scope_camera_FPS_value = 0
		self.daq.DAQScopeFRSlider.valueChanged.connect(self.scam_FPS_slider_changed)

		## Visualization Slider | brightness & Contrast
		self.brightness_value = 0
		self.daq.DAQBrightnessValue.editingFinished.connect(self.brightness_box_changed)
		self.daq.DAQBrightnessSlider.valueChanged.connect(self.brightness_slider_changed)
		self.contrast_value = 0
		self.daq.DAQContrastValue.editingFinished.connect(self.contrast_box_changed)
		self.daq.DAQContrastSlider.valueChanged.connect(self.contrast_slider_changed)
		## Overay Opacity
		self.overay_value = 0
		self.daq.DAQOverayValue.editingFinished.connect(self.overay_box_changed)
		self.daq.DAQOveraySlider.valueChanged.connect(self.overay_slider_changed)
		
		# Message Box
		self.inform_window = QMessageBox()
		self.inform_window.setWindowTitle("notice")
		self.inform_window.setWindowIcon(QtGui.QPixmap("info.png"))
		self.inform_window.setIcon(QMessageBox.Information)
	
	def move_slider1():
		pass

	## Camera Connection - Scope
	def connect_scope_camera_button_clicked(self):
		text = self.daq.DAQScopeCamButton.text()
		if text == 'Scope\n''Connect' and self.scope_cam is None:
			camera_ID = self.scope_camera_number
			print(camera_ID)
			self.scope_cam = CaptureThread(camera=camera_ID, camera_type='S', 
											lock=self.data_lock2, parent=self, user_path=self.user_path, 
											file_type=self.save_format, pj_name=self.project_name)
			self.scope_cam.frameCaptured.connect(self.update_scope_camera_frame)
			self.scope_cam.fpsChanged.connect(self.update_scope_camera_FPS)
			self.scope_cam_view_size = None
			self.scope_cam.start()

			if self.scope_cam:
				self.DAQScopeCamView.setStyleSheet('background-color: rgb(0,0,0);')
				self.daq.DAQScopeCamButton.setText('Scope\n''Disconnect')
				self.daq.DAQScopeSign.setStyleSheet('background-color: rgb(0, 255, 0);')
				self.daq.DAQScopeCamStatus.setText('Connected')
				self.daq.DAQScopeCamPanel.setEnabled(True)
				self.daq.DAQScopeExposureSlider.setValue(self.scope_cam.exposure_status)

		elif text == 'Scope\n''Disconnect' and self.scope_cam is not None:
			self.scope_cam.frameCaptured.disconnect(self.update_scope_camera_frame)
			self.scope_cam.fpsChanged.disconnect(self.update_scope_camera_FPS)
			self.scope_cam.stop()
			self.scope_cam = None

			self.daq.DAQScopeCamButton.setText('Scope\n''Connect')
			self.daq.DAQScopeSign.setStyleSheet('background-color: rgb(85,85,127);')
			self.daq.DAQScopeCamStatus.setText('Disconnected')
			self.daq.DAQScopeCamPanel.setEnabled(False)

	## Camera Connection - Behavior
	def connect_behavior_camera_button_clicked(self):
		text = self.daq.DAQBehCamButton.text()
		if text == 'Behavior\n''Connect' and self.behavior_cam is None:
			#camera_ID = cv2.CAP_DSHOW + self.behavior_camera_number
			camera_ID = self.behavior_camera_number
			print(camera_ID)
			self.behavior_cam = CaptureThread(camera=camera_ID, camera_type='B', 
										lock=self.data_lock, parent=self, user_path=self.user_path, 
										file_type=self.save_format, pj_name=self.project_name)
			self.behavior_cam.frameCaptured.connect(self.update_behavior_camera_frame)
			self.behavior_cam.fpsChanged.connect(self.update_behavior_camera_FPS)
			self.behavior_cam.start()


			# cam status slot - function connection
			'''끊길시 push 해주는 것이 어떨까. '''
			#if self.behavior_camera_status: 
			if self.behavior_cam:
				self.DAQBehCamView.setStyleSheet('background-color: rgb(0,0,0);')
				self.daq.DAQBehCamButton.setText('Behavior\n''Disconnect')
				self.daq.DAQBehSign.setStyleSheet('background-color: rgb(0, 255, 0);')
				self.daq.DAQBehCamStatus.setText('Connected')
				self.daq.DAQBehCamPanel.setEnabled(True)
				self.daq.DAQBehExposureSlider.setValue(self.behavior_cam.exposure_status)

			## widget .setEnabled(True)

		elif text == 'Behavior\n''Disconnect' and self.behavior_cam is not None:
			self.behavior_cam.frameCaptured.disconnect(self.update_behavior_camera_frame)
			self.behavior_cam.fpsChanged.disconnect(self.update_behavior_camera_FPS)
			self.behavior_cam.stop()
			self.behavior_cam = None

			self.daq.DAQBehCamButton.setText('Behavior\n''Connect')
			self.daq.DAQBehSign.setStyleSheet('background-color: rgb(85,85,127);')
			self.daq.DAQBehCamStatus.setText('Disconnected')
			self.daq.DAQBehCamPanel.setEnabled(False)

			## widget .setEnabled(False)


	## Recording start and stop - Scope and Behavior camera
	def set_duration(self):
		duration = 0
		if self.daq.DAQRecordDurationCheckbox.isChecked():
			dtime = self.daq.DAQRecordingDuration.time()
			print(dtime.minute()*60 + dtime.second()) ##

	def recording_start_stop(self):
		text = self.daq.DAQRecordButton.text()
		## - (?.time check for sync)
		if text == 'Record':  
			if self.scope_cam is not None: # Chcek Scope Camera
				# preparation of recording scope camera
				self.scope_cam.save_format = str(self.DAQRecordFormatSelection.currentText())
				if self.daq.DAQRecordDurationCheckbox.isChecked(): # duration mode on
					## Send Stop after DurationTime
					print('!!', self.daq.DAQRecordingDuration.time())
				# Scope Cam Recoding
				self.scope_cam.video_saving_status = VideoSavingStatus.STARTING
					
				if self.behavior_cam is not None: # Check Behavior Camera
					## Behavior Cam Recoding
					self.behvior_cam.save_format = str(self.DAQRecordFormatSelection.currentText())
					self.behavior_cam.video_saving_status = VideoSavingStatus.STARTING 
				
				## Status Sign Change - (?.signal from CaptureThread)
				## Scope  
				if self.scope_cam.video_saving_status == VideoSavingStatus.STARTED:
					self.daq.DAQScopeSign.setStyleSheet('background-color: rgb(255, 0, 0);')
					self.daq.DAQScopeCamStatus.setText('Recording')
				## Behavior 
				if self.behavior_cam.video_saving_status == VideoSavingStatus.STARTED:
					self.daq.DAQBehSign.setStyleSheet('background-color: rgb(255, 0, 0);')
					self.daq.DAQBehCamStatus.setText('Recording')

				self.daq.DAQRecordButton.setText('Stop Recording')
			elif self.behavior_cam is not None: # Check Behavior Camera
					## Behavior Cam Recoding
					self.behvior_cam.save_format = str(self.DAQRecordFormatSelection.currentText())
					self.behavior_cam.video_saving_status = VideoSavingStatus.STARTING 
					## Behavior Status Sign
					if self.behavior_cam.video_saving_status == VideoSavingStatus.STARTED:
						self.daq.DAQBehSign.setStyleSheet('background-color: rgb(255, 0, 0);')
						self.daq.DAQBehCamStatus.setText('Recording')
					self.daq.DAQRecordButton.setText('Stop Recording')
			else:
				print('Check Camera Connection')
				
		elif text == 'Stop Recording':
			if self.scope_cam is not None:
				self.scope_cam.video_saving_status = VideoSavingStatus.STOPPING
				self.connect_scope_camera_button_clicked()
				## player ..
			if self.behavior_cam is not None:
				self.behavior_cam.video_saving_status = VideoSavingStatus.STOPPING
				self.connect_behavior_camera_button_clicked()
				## player ..?
			self.daq.DAQRecordButton.setText('Record')
			
			## pause cameras
			## start player

	# < Camera Functions >
	## Behavior Camera
	@Slot(QtGui.QImage)
	def update_behavior_camera_frame(self, image):
		pixmap = QtGui.QPixmap.fromImage(image)
		temp_width = self.DAQBehCamView.size() + QtCore.QSize(-2,-2) #width() ## changable or not
		#pixmap = pixmap.scaledToWidth(temp_width)
		pixmap = pixmap.scaled(temp_width, QtCore.Qt.KeepAspectRatio)
		self.DAQBehCamItem.setPixmap(pixmap)
		print('B image updating', temp_width, pixmap)
	def update_behavior_camera_FPS(self):
		pass

	## Scope Camera
	@Slot(QtGui.QImage)
	def update_scope_camera_frame(self, image):
		if self.scope_cam_view_size == None:
			self.viewer_size_control()
		pixmap = QtGui.QPixmap.fromImage(image)
		temp_width = self.DAQScopeCamView.size()
		self.DAQScopeCamItem.setPixmap(pixmap)
		print('S image updating', temp_width, pixmap)
	def update_scope_camera_FPS(self, fps):
		self.daq.DAQScopeViewFPS.setText(str(fps))
	def viewer_size_control(self):
		scope_cam_view_size = (self.scope_cam.frame_width, self.scope_cam.frame_height)
		print(scope_cam_view_size)
		self.daq.DAQScopeCamView.fitInView(0, 0, scope_cam_view_size[0], scope_cam_view_size[1], 
										QtCore.Qt.KeepAspectRatio)
		self.scope_cam_view_size = scope_cam_view_size



	# < Slider Control Functions >
	## Behavior Camera
	def bcam_exposure_box_changed(self):
		text = self.daq.DAQBehExposureValue.text()
		if not text == "": 
			self.daq.DAQBehExposureValue.setPlaceholderText(text)
			self.daq.DAQBehExposureSlider.setValue(int(text))
			self.daq.DAQBehExposureValue.setText("")
	def bcam_exposure_slider_changed(self, value:int):
		self.behavior_cam.exposure_control_value = value #아니면 놓을 때 보내기. 
		self.daq.DAQBehExposureValue.setPlaceholderText(str(value))
		self.behavior_camera_exposure_value = value
		print("BEXP called, ", self.behavior_camera_exposure_value)

	## Scope Camera
	def scam_LED_box_changed(self):
		text = self.daq.DAQScopeLEDValue.text()
		if not text == "": 
			self.daq.DAQScopeLEDValue.setPlaceholderText(text)
			self.daq.DAQScopeLEDSlider.setValue(int(text))
			self.daq.DAQScopeLEDValue.setText("")
	def scam_LED_slider_changed(self, value):
		self.daq.DAQScopeLEDValue.setPlaceholderText(str(value))
		self.scope_camera_LED_value = value
		print("LED called, ", self.scope_camera_LED_value)

	def scam_gain_box_changed(self):
		text = self.daq.DAQScopeGainValue.text()
		if not text == "": 
			self.daq.DAQScopeGainValue.setPlaceholderText(text)
			self.daq.DAQScopeGainSlider.setValue(int(text))
			self.daq.DAQScopeGainValue.setText("")
	def scam_gain_slider_changed(self, value):
		self.daq.DAQScopeGainValue.setPlaceholderText(str(value))
		self.scope_camera_gain_value = value
		print("GAIN called, ", self.scope_camera_gain_value)

	def scam_exposure_box_changed(self):
		text = self.daq.DAQScopeExposureValue.text()
		if not text == "": 
			self.daq.DAQScopeExposureValue.setPlaceholderText(text)
			self.daq.DAQScopeExposureSlider.setValue(int(text))
			self.daq.DAQScopeExposureValue.setText("")
	def scam_exposure_slider_changed(self, value):
		self.scope_cam.exposure_control_value = value
		self.daq.DAQScopeExposureValue.setPlaceholderText(str(value))
		self.scope_camera_exposure_value = value
		print("SEXP called, ", self.scope_camera_exposure_value)

	def scam_FPS_slider_changed(self, value):
		fps = self.frame_rate_list[value]
		self.daq.DAQScopeFRValue.setPlaceholderText(str(fps))
		self.scope_camera_FPS_value = fps
		print("FPS called, ", self.scope_camera_FPS_value)

	## Visualization

	def brightness_box_changed(self):
		text = self.daq.DAQBrightnessValue.text()
		if not text == "":
			self.daq.DAQBrightnessValue.setPlaceholderText(text)
			self.daq.DAQBrightnessSlider.setValue(int(text))
			self.daq.DAQBrightnessValue.setText("")
	def brightness_slider_changed(self, value):
		self.daq.DAQBrightnessValue.setPlaceholderText(str(value))
		self.brightness_value = value
		print("BRI called, ", self.brightness_value)
	def contrast_box_changed(self):
		text = self.daq.DAQContrastValue.text()
		if not text == "":
			self.daq.DAQContrastValue.setPlaceholderText(text)
			self.daq.DAQContrastSlider.setValue(int(text))
			self.daq.DAQContrastValue.setText("")
	def contrast_slider_changed(self, value):
		self.daq.DAQContrastValue.setPlaceholderText(str(value))
		self.contrast_value = value
		print("CONT called, ", self.contrast_value)
	def overay_box_changed(self):
		text = self.daq.DAQOverayValue.text()
		if not text == "":
			self.daq.DAQOverayValue.setPlaceholderText(text)
			self.daq.DAQOveraySlider.setValue(int(text))
			self.daq.DAQOverayValue.setText("")
	def overay_slider_changed(self, value):
		self.daq.DAQOverayValue.setPlaceholderText(str(value))
		self.overay_value = value
		print("OVE called, ", self.overay_value)

	# < load & set UI >

	def setupUi(self):
		self.daq = QUiLoader().load('210927_DAQ.ui')
		self.setCentralWidget(self.daq)


