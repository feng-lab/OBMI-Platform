from PySide2.QtWidgets import QMainWindow
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import Slot, QTime, QTimer
from PySide2 import QtCore, QtGui
import cv2
import time
import os

#from u150ppi import iconlist
import iconlist_iconUpdated

from PySide2.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
									 QHBoxLayout, QMessageBox, QLabel, QWidget)

# from capture_thread import VideoSavingStatus, CaptureThread
from capture_thread_v3 import VideoSavingStatus, CaptureThread
from player_thread import VPlayer, VPlayerStatus
from PySide2.QtWidgets import QFileDialog

from pygrabber.dshow_graph import FilterGraph


class MainWindow(QMainWindow):
	def __init__(self, indep=False):
		super().__init__()
		self.indep = indep
		ui_path = '220929_DAQ_iconUpdated.ui' #220726_DAQ_edited_fonted.ui #'220621_DAQ_edited_fonted.ui' #'220621_DAQ_edited.ui'
		self.setupUi(ui_path) #'220523_DAQ_edited.ui')
		self.buttonSet()

		#self.daq.DAQScopeViewPanel.hide()
		self.daq.DAQPlayBar.hide()

		# os setting
		self.set_os('windows') ## set os_num

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

		# Camera numbers - Temporary
		self.daq.BnumBox.setText(str(self.behavior_camera_number))
		self.daq.SnumBox.setText(str(self.scope_camera_number))
		self.daq.BnumBox.editingFinished.connect(self.Bnum_change)
		self.daq.SnumBox.editingFinished.connect(self.Snum_change)

		# Recording init ##
		self.record_player = None ##
		self.daq_brightness_and_contrast = self.daq.widget_25
		self.daq_brightness_and_contrast.setEnabled(False)

		# Recording Function Connection
		self.video_path = None
		self.user_path = None
		self.project_name = None
		self.save_format = 'avi'
		self.daq.DAQRecordButton.clicked.connect(self.recording_start_stop)
		## Recoding option - duration on/off
		self.daq.DAQRecordDurationCheckbox.clicked.connect(self.set_duration)
		self.daq.DAQRecordingDuration.timeChanged.connect(self.set_duration)
		self.dtime = 0

		# Slider Control (#returnPressed)
		## Behavior Exposure Slider
		self.behavior_camera_exposure_value = 0
		self.daq.DAQBehExposureValue.editingFinished.connect(self.bcam_exposure_box_changed)
		self.daq.DAQBehExposureSlider.valueChanged.connect(self.bcam_exposure_slider_changed)
		## Scope LED Power Slider
		self.scope_camera_LED_value = 0
		self.daq.DAQScopeLEDValue.editingFinished.connect(self.scam_LED_box_changed)
		self.daq.DAQScopeLEDSlider.valueChanged.connect(self.scam_LED_slider_changed)
		self.daq.DAQScopeLEDSlider.sliderReleased.connect(self.scam_LED_slider_released)
		## Scope Gain Slider
		self.scope_camera_gain_value = 16
		self.daq.DAQScopeGainValue.editingFinished.connect(self.scam_gain_box_changed)
		self.daq.DAQScopeGainSlider.valueChanged.connect(self.scam_gain_slider_changed)
		self.daq.DAQScopeGainSlider.sliderReleased.connect(self.scam_gain_slider_released)
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
		self.daq.DAQBrightnessSlider.sliderReleased.connect(self.brightness_slider_released)
		self.contrast_value = 0
		self.daq.DAQContrastValue.editingFinished.connect(self.contrast_box_changed)
		self.daq.DAQContrastSlider.valueChanged.connect(self.contrast_slider_changed)
		self.daq.DAQContrastSlider.sliderReleased.connect(self.contrast_slider_released)
		## Overay Opacity
		self.overay_value = 0
		self.daq.DAQOverayValue.editingFinished.connect(self.overay_box_changed)
		self.daq.DAQOveraySlider.valueChanged.connect(self.overay_slider_changed)

		## Recording Slider
		self.daq.DAQPlayerSlider.valueChanged.connect(self.player_slider_changed)
		self.daq.DAQPlayerSlider.sliderReleased.connect(self.player_slider_controlled)
		self.player_slider_released = False
		
		# Message Box
		self.inform_window = QMessageBox()
		self.inform_window.setWindowTitle("notice")
		self.inform_window.setWindowIcon(QtGui.QPixmap("info.png"))
		self.inform_window.setIcon(QMessageBox.Information)

		## frame_drop
		drop_frame_img_path = self.indep_path('droppedFrameImage.bmp')
		self.drop_frame_image = cv2.imread(drop_frame_img_path)

		# camera scan
		self.daq.catch_camlist.clicked.connect(self.cam_refresh)
		## notation
		self.daq.note_box_export_button.clicked.connect(self.saving_note)
		## initial setting
		self.system_info_gen()

	def buttonSet(self): ## ui change
		# default setting
		self.bcam_layout_on = True
		self.scam_layout_on = True

		self.daq.bcam_layout_button.clicked.connect(self.change_bcam_layout)
		self.daq.scam_layout_button.clicked.connect(self.change_scam_layout)

		self.daq_layout1_on = True
		self.daq_layout3_on = True
		self.daq.DAQLayout1.clicked.connect(self.change_layout1)
		#self.daq.DAQLayout2.clicked.connect()
		self.daq.DAQLayout3.clicked.connect(self.change_layout3)

	def change_layout1(self):
		if self.daq_layout1_on:
			self.daq.DAQRightPanel.hide()
			self.daq_layout1_on = False
		else:
			self.daq.DAQRightPanel.show()
			self.daq_layout1_on = True

	def change_layout3(self):
		if self.daq_layout3_on:
			self.daq.DAQBottom.hide()
			self.daq_layout3_on = False
		else:
			self.daq.DAQBottom.show()
			self.daq_layout3_on = True


	def change_scam_layout(self):
		if self.scam_layout_on:
			self.daq.scam_layout_button.setStyleSheet('border-image: url(:/sidebar/Asset 8.png);')
			self.daq.temp_space.hide()
			self.daq.temp_space2.hide()
			#self.daq.DAQScopeViewPanel2.hide()
			self.daq.DAQScopeViewPanel.hide()
			self.scam_layout_on = False
		else:
			self.daq.scam_layout_button.setStyleSheet('border-image: url(:/home/ScopeCamOn.png);')
			self.daq.temp_space.show()
			self.daq.temp_space2.show()
			#self.daq.DAQScopeViewPanel2.show()
			self.daq.DAQScopeViewPanel.show()
			self.scam_layout_on = True


	def change_bcam_layout(self):
		if self.bcam_layout_on:
			self.daq.bcam_layout_button.setStyleSheet('border-image: url(:/sidebar/Asset 6.png);')
			self.daq.DAQBehViewPanel.hide()
			self.bcam_layout_on = False
		else:
			self.daq.bcam_layout_button.setStyleSheet('border-image: url(:/home/BehaviorCamOn.png);')
			self.daq.DAQBehViewPanel.show()
			self.bcam_layout_on = True






	def get_default_project_name(self):
		if not self.project_name:
			t = time.localtime()
			self.project_name = f'{t.tm_year}_{t.tm_mon}_{t.tm_mday}'
		return self.project_name

	def system_info_gen(self):
		project_name = self.get_default_project_name()
		system_info = f'os setting: {["Windows", "Linux"][self.os_num]}\n'
		system_info += f'project name: {project_name}'
		sys_info = QLabel(system_info)
		self.daq.system_info_win.setWidget(sys_info)


	def saving_note(self):
		## save_path
		note_text = self.daq.note_box.toPlainText()
		note_saving_path = QFileDialog.getSaveFileName(self, "save note","", ".txt")
		note_saving_path = ''.join(list(note_saving_path))
		print(note_saving_path)
		#getExistingDirectory(self, "select Directory"))
		with open(note_saving_path, 'w') as note:
			note.write(note_text)



	def recording_view_init(self):
		self.DAQPlayerView = self.DAQScopeCamView #self.daq.DAQScopePlayerView
		#self.DAQPlayerScene = QGraphicsScene()
		#self.DAQPlayerView.setScene(self.DAQPlayerScene)
		self.DAQPlayerItem = self.DAQScopeCamItem #QGraphicsPixmapItem()
		#self.DAQPlayerScene.addItem(self.DAQPlayerItem)

	def Bnum_change(self):
		self.behavior_camera_number = int(self.daq.BnumBox.text())
		self.daq.BnumBox.setText(str(self.behavior_camera_number))
		
	def Snum_change(self):
		self.scope_camera_number = int(self.daq.SnumBox.text())
		self.daq.SnumBox.setText(str(self.scope_camera_number))


	## Camera Connection - Scope
	def connect_scope_camera_button_clicked(self):
		##text = self.daq.DAQScopeCamButton.text()
		text = self.daq.DAQScopeCamStatus.text()
		##if text == 'Scope\n''Connect' and self.scope_cam is None:
		if text == 'Disconnected' and self.scope_cam is None:

			if  self.daq.DAQPlayBar.isVisible(): ##self.daq.DAQScopeViewPanel.isVisible():
				print('visible')
				self.player_done_button()

			self.daq.SnumBox.setEnabled(False)

			camera_ID = self.scope_camera_number
			print(camera_ID)
			camera_size = None
			if self.daq.DAQScopeVersion.isChecked(): 
				camera_size = (608,608)
				## temp default value
				##self.daq.DAQScopeFRSlider.setValue(self.frame_rate_list.index(30))
			else: 
				camera_size = (752,480)
				## temp default value
				##self.daq.DAQScopeFRSlider.setValue(self.frame_rate_list.index(60))

			init_fps = float(self.daq.DAQScopeFRValue.placeholderText()) if self.daq.DAQScopeFRValue.placeholderText() != '' else 30.0
			print(f'initfps: {init_fps}')
			self.scope_cam = CaptureThread(camera=camera_ID, camera_type='S', camera_size=camera_size,
											lock=self.data_lock2, parent=self, user_path=self.user_path, 
											file_type=self.save_format, pj_name=self.project_name,
										    os_type = self.os_num, init_fps=init_fps, drop_f=self.drop_frame_image)
			self.scope_cam.frameCaptured.connect(self.update_scope_camera_frame)
			self.fps_for_mk = []
			self.scope_cam.fpsChanged.connect(self.update_scope_camera_FPS)
			self.scope_cam_view_size = None
			self.scope_cam.start()
	

			if self.scope_cam:
				self.DAQScopeCamView.setStyleSheet('background-color: rgb(0,0,0);')
				## self.daq.DAQScopeCamButton.setText('Scope\n''Disconnect')
				self.daq.DAQScopeSign.setStyleSheet('background-color: rgb(0, 255, 0);')
				self.daq.DAQScopeCamStatus.setText('Connected')
				self.daq.DAQScopeCamPanel.setEnabled(True)
				self.daq.DAQScopeExposureSlider.setValue(self.scope_cam.exposure_status)

		## elif text == 'Scope\n''Disconnect' and self.scope_cam is not None:
		elif text in ['Connected', 'Recording'] and self.scope_cam is not None:
			self.scope_cam.frameCaptured.disconnect(self.update_scope_camera_frame)
			self.scope_cam.fpsChanged.disconnect(self.update_scope_camera_FPS)
			self.scope_cam.stop()
			self.scope_cam = None

			## self.daq.DAQScopeCamButton.setText('Scope\n''Connect')
			self.daq.DAQScopeSign.setStyleSheet('background-color: rgb(85,85,127);')
			self.daq.DAQScopeCamStatus.setText('Disconnected')
			self.daq.DAQScopeCamPanel.setEnabled(False)
			
			self.daq.SnumBox.setEnabled(True)

	## Camera Connection - Behavior
	def connect_behavior_camera_button_clicked(self):
		## text = self.daq.DAQBehCamButton.text()
		text = self.daq.DAQBehCamStatus.text()
		## if text == 'Behavior\n''Connect' and self.behavior_cam is None:
		if text == 'Disconnected' and self.behavior_cam is None:
			self.daq.BnumBox.setEnabled(False)
			#camera_ID = cv2.CAP_DSHOW + self.behavior_camera_number
			camera_ID = self.behavior_camera_number
			print(camera_ID)
			self.behavior_cam = CaptureThread(camera=camera_ID, camera_type='B', camera_size=None,
										lock=self.data_lock, parent=self, user_path=self.user_path, 
										file_type=self.save_format, pj_name=self.project_name,
										os_type=self.os_num, drop_f=self.drop_frame_image)
			self.behavior_cam.frameCaptured.connect(self.update_behavior_camera_frame)
			self.behavior_cam.fpsChanged.connect(self.update_behavior_camera_FPS)
			self.behavior_cam.start()

			# cam status slot - function connection
			'''끊길시 push 해주는 것이 어떨까. '''
			#if self.behavior_camera_status: 
			if self.behavior_cam:
				self.DAQBehCamView.setStyleSheet('background-color: rgb(0,0,0);')
				## self.daq.DAQBehCamButton.setText('Behavior\n''Disconnect')
				self.daq.DAQBehSign.setStyleSheet('background-color: rgb(0, 255, 0);')
				self.daq.DAQBehCamStatus.setText('Connected')
				self.daq.DAQBehCamPanel.setEnabled(True)
				self.daq.DAQBehExposureSlider.setValue(self.behavior_cam.exposure_status)

			## widget .setEnabled(True)

		## elif text == 'Behavior\n''Disconnect' and self.behavior_cam is not None:
		elif text in ['Connected', 'Recording'] and self.behavior_cam is not None:
			self.behavior_cam.frameCaptured.disconnect(self.update_behavior_camera_frame)
			self.behavior_cam.fpsChanged.disconnect(self.update_behavior_camera_FPS)
			self.behavior_cam.stop()
			self.behavior_cam = None

			## self.daq.DAQBehCamButton.setText('Behavior\n''Connect')
			self.daq.DAQBehSign.setStyleSheet('background-color: rgb(85,85,127);')
			self.daq.DAQBehCamStatus.setText('Disconnected')
			self.daq.DAQBehCamPanel.setEnabled(False)

			self.daq.BnumBox.setEnabled(True)

			## widget .setEnabled(False)


	## Recording start and stop - Scope and Behavior camera
	def set_duration(self):
		duration = 0
		if self.daq.DAQRecordDurationCheckbox.isChecked():
			dtime = self.daq.DAQRecordingDuration.time()
			self.dtime = dtime.minute()*60 + dtime.second() ## duration time

	def recording_start_stop(self):
		##text = self.daq.DAQRecordButton.text()
		stext = self.daq.DAQScopeCamStatus.text()
		btext = self.daq.DAQBehCamStatus.text()
		## - (?.time check for sync)
		## if text == 'Record':  
		if stext == 'Connected' or btext == 'Connected':
			if self.scope_cam is not None: # Chcek Scope Camera
				# preparation of recording scope camera
				self.scope_cam.save_format = str(self.daq.DAQRecordFormatSelection.currentText())
				# Scope Cam Recoding
				self.scope_cam.video_saving_status = VideoSavingStatus.STARTING
				
			## Scope  
			#if self.scope_cam.video_saving_status == VideoSavingStatus.STARTED:
				if self.daq.DAQRecordDurationCheckbox.isChecked(): # duration mode on
					## Send Stop after DurationTime
					self.record_counting('dura')
				else: self.record_counting('start')
				self.daq.DAQScopeSign.setStyleSheet('background-color: rgb(255, 0, 0);')
				self.daq.DAQScopeCamStatus.setText('Recording')
				
				
				if self.behavior_cam is not None: # Check Behavior Camera
					## Behavior Cam Recoding
					self.behavior_cam.save_format = str(self.daq.DAQRecordFormatSelection.currentText())
					self.behavior_cam.video_saving_status = VideoSavingStatus.STARTING 
					
				## Behavior 
				#if self.behavior_cam.video_saving_status == VideoSavingStatus.STARTED:
					self.daq.DAQBehSign.setStyleSheet('background-color: rgb(255, 0, 0);')
					self.daq.DAQBehCamStatus.setText('Recording')
				
				## Status Sign Change - (?.signal from CaptureThread)		

				## self.daq.DAQRecordButton.setText('Stop Recording')
			elif self.behavior_cam is not None: # Check Behavior Camera
					## Behavior Cam Recoding
					self.behavior_cam.save_format = str(self.daq.DAQRecordFormatSelection.currentText())
					self.behavior_cam.video_saving_status = VideoSavingStatus.STARTING 
					## Behavior Status Sign
					##if self.behavior_cam.video_saving_status == VideoSavingSta tus.STARTED:
					self.daq.DAQBehSign.setStyleSheet('background-color: rgb(255, 0, 0);')
					self.daq.DAQBehCamStatus.setText('Recording')
					## self.daq.DAQRecordButton.setText('Stop Recording')
			else:
				print('Check Camera Connection')
				
		## elif text == 'Stop Recording':
		elif stext == 'Recording' or btext == 'Recording':
			if self.behavior_cam is not None:
				self.behavior_cam.video_saving_status = VideoSavingStatus.STOPPING
				self.connect_behavior_camera_button_clicked()
				## player ..?
			## self.daq.DAQRecordButton.setText('Record')
			
			if self.scope_cam is not None:
				self.video_path = self.scope_cam.video_file
				self.scope_cam.video_saving_status = VideoSavingStatus.STOPPING
				self.record_counting('stop')
				

				self.connect_scope_camera_button_clicked()
				
				## temp function for FPS counting 
				import pandas as pd
				pd.DataFrame(self.fps_for_mk).to_csv('./fps_per_frame')
				## player ..

				self.start_player()
			## pause cameras
			## start player

	def XX_time_based_player_slider_controlled(self):
		#self.player_slider_released = True
		value = self.daq.DAQPlayerSlider.value()
		self.record_player.starting_msec = value*self.player_max_value/1000
		if self.record_player.vplayer_status == VPlayerStatus.STARTED:
			self.playing = True
			
		self.record_player.vplayer_status = VPlayerStatus.MOVING


		self.update_player_slider(value)
		print('controlled value: ', value)

	def player_slider_controlled(self):
		value = self.daq.DAQPlayerSlider.value()
		self.record_player.present_frame = value
		self.record_player.frame_moved = True
		

	def XX_time_based_player_slider_changed(self, v):
		## update time or control time?
		vsec = int(v*self.player_max_value/1000000)
		print('v: ', v, vsec)
		present_time = time.strftime('%M:%S', time.gmtime(vsec))
		self.daq.DAQPlayerPresentTime.setText(present_time)
		print('something slider changed')
		pass

	def player_slider_changed(self, frame_v):
		vsec = int(frame_v / self.video_fps)
		present_time = time.strftime('%M:%S', time.gmtime(vsec))
		self.daq.DAQPlayerPresentTime.setText(present_time)
		self.daq.DAQFrameCount.setText(f'Frame: {frame_v:>6}')
		print('something slider changed')

	def start_player(self):

		data_lock3 = QtCore.QMutex()
		
		self.daq_brightness_and_contrast.setEnabled(True) ##

		self.recording_view_init() ##
		self.record_player = VPlayer(user_path=self.video_path, lock=data_lock3, parent=self)
		print('videopath: ', self.video_path)
		self.record_player.frameC.connect(self.update_player_frame)
		self.record_player.stopS.connect(self.player_stopped_signal)
		self.daq.DAQPlayerPlayButton.clicked.connect(self.player_start_button)
		self.daq.DAQPlayerStopButton.clicked.connect(self.player_stop_button)
		self.daq.DAQPlayerDoneButton.clicked.connect(self.player_done_button)
		totalframe = self.record_player.total_frame
		self.video_fps = self.record_player.fps
		self.set_player_slider(totalframe, self.video_fps)
		#self.daq.DAQScopeViewPanel.show()
		self.daq.DAQPlayBar.show()
		self.daq.DAQScopeViewFPS.hide()

	def set_player_slider(self, totalframe, fps):
		player_max_value = int(totalframe) -1
		print('player max value: ', player_max_value)
		self.daq.DAQPlayerSlider.setMinimum(0)
		self.daq.DAQPlayerSlider.setMaximum(player_max_value)
		print('maximum: ', self.daq.DAQPlayerSlider.maximum())
		self.player_max_value = player_max_value
		finish_time = time.strftime('%M:%S', time.gmtime(int(totalframe/fps)))
		self.daq.DAQPlayerFinishTime.setText(finish_time)

	def XX_time_based_set_player_slider(self, totalframe, fps):
		player_max_value = totalframe / fps * 1000
		print('player max value: ', player_max_value)
		self.daq.DAQPlayerSlider.setMinimum = 0
		self.daq.DAQPlayerSlider.setMaximum = player_max_value
		print('maximum: ', self.daq.DAQPlayerSlider.maximum())
		self.player_max_value = player_max_value

		finish_time = time.strftime('%M:%S', time.gmtime(totalframe/fps))
		self.daq.DAQPlayerFinishTime.setText(finish_time)


	def player_start_button(self):
		play_or_pause = self.daq.DAQPlayerPlayButton.text()
		if play_or_pause == 'Play':
			if self.record_player.vplayer_status == VPlayerStatus.STOPPED:
				self.record_player.start()
			self.record_player.vplayer_status = VPlayerStatus.STARTING
			self.daq.DAQPlayerPlayButton.setText('Pause')
		elif play_or_pause == 'Pause': ## consider icon ||
			self.record_player.vplayer_status = VPlayerStatus.PAUSING
			self.daq.DAQPlayerPlayButton.setText('Play') 
	def player_stop_button(self):
		self.record_player.vplayer_status = VPlayerStatus.STOPPING
		#self.record_player.done()
	def player_done_button(self):
		self.record_player.frameC.disconnect(self.update_player_frame)
		self.record_player.stopS.disconnect(self.player_stopped_signal)
		#self.daq.DAQScopeViewPanel.hide()
		self.daq.DAQPlayBar.hide()
		self.daq.DAQScopeViewFPS.show()
		self.daq_brightness_and_contrast.setEnabled(False)
		self.record_player.done() ##
		## need - save b and c edited video


	@Slot(QtGui.QImage)
	def update_player_frame(self, image):
		print('putput')
		pixmap = QtGui.QPixmap.fromImage(image)
		temp_width = self.DAQPlayerView.size() + QtCore.QSize(-2,-2) #width() ## changable or not
		#pixmap = pixmap.scaledToWidth(temp_width)
		pixmap = pixmap.scaled(temp_width, QtCore.Qt.KeepAspectRatio)
		self.DAQPlayerItem.setPixmap(pixmap)
		print('B image updating', temp_width, pixmap)
		self.update_player_slider(self.record_player.frame_counter)
	
	def player_stopped_signal(self, stopped):
		if stopped == True:
			self.update_player_slider(0)
				## cap restart?
			if self.daq.DAQPlayerPlayButton.text() == 'Pause':
				self.daq.DAQPlayerPlayButton.setText('Play') ## consider pause icon ||


	def update_player_slider(self, presentframe):
		self.daq.DAQPlayerSlider.setValue(presentframe)
		presentsec = presentframe / self.video_fps 
		
		print('presentframe: ', presentframe)
		print('presentsec: ', int(presentsec))
		print('singlestep: ', self.daq.DAQPlayerSlider.value())
		#presentsecond = presentframe / self.video_fps
		#self.daq.DAQPlayerSlider.setValue(presentsecond)

	def XX_time_based_update_player_slider(self, presentsec):
		presentsec = presentsec / self.player_max_value * 1000
		self.daq.DAQPlayerSlider.setValue(int(presentsec))
		print('presentsec: ', int(presentsec))
		print('singlestep: ', self.daq.DAQPlayerSlider.value())
		#presentsecond = presentframe / self.video_fps
		#self.daq.DAQPlayerSlider.setValue(presentsecond)

	def record_counting(self, status):
		if status == 'stop':
			self.recording_timer.stop()
		elif status == 'start' or status == 'dura':
			self.recording_timer = QTimer(self)
			self.count_time = 0
			if status == 'dura': 
				self.daq.RecordingElapsedTime.setText('Elapsed time: 00:00:00')	
				self.daq.RecordLength.setText(f'Record length: {time.strftime("%H:%M:%S", time.gmtime(self.dtime))}')
				self.recording_timer.timeout.connect(self.update_recording_timer_dura)
			else: 
				self.recording_timer.timeout.connect(self.update_recording_timer)
			self.recording_timer.start(1000)

	def update_recording_timer(self):
		self.count_time += 1
		ctime = time.strftime('%H:%M:%S', time.gmtime(self.count_time))
		self.daq.RecordingElapsedTime.setText(f'Elapsed time: {ctime}')

	def update_recording_timer_dura(self):
		self.count_time += 1
		ctime = time.strftime('%H:%M:%S', time.gmtime(self.count_time))
		self.daq.RecordingElapsedTime.setText(f'Elapsed time: {ctime}')
		if self.count_time == self.dtime:
			self.recording_start_stop()
			#self.daq.RecordingElapsedTime.setText('Elapsed time: 00:00:00')
			


			
		



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
		#if self.scope_cam_view_size == None:
		#	self.viewer_size_control()
		pixmap = QtGui.QPixmap.fromImage(image)
		temp_width = self.DAQScopeCamView.size() + QtCore.QSize(-2,-2)
		pixmap = pixmap.scaled(temp_width, QtCore.Qt.KeepAspectRatio) ###
		self.DAQScopeCamItem.setPixmap(pixmap)
		print('S image updating', temp_width, pixmap)
	def update_scope_camera_FPS(self, fps):
		self.daq.DAQScopeViewFPS.setText(str(fps))
		self.fps_for_mk.append(fps)
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
		print(self.daq.DAQScopeLEDSlider.isSliderDown())
		if not self.daq.DAQScopeLEDSlider.isSliderDown():
			self.scope_cam.led_control_value = value  ## set slider value
		self.daq.DAQScopeLEDValue.setPlaceholderText(str(value))
		self.scope_camera_LED_value = value
		print("LED called, ", self.scope_camera_LED_value)
	def scam_LED_slider_released(self):
		self.scope_cam.led_control_value = self.scope_camera_LED_value

	def scam_gain_box_changed(self):
		text = self.daq.DAQScopeGainValue.text()
		if not text == "": 
			self.daq.DAQScopeGainValue.setPlaceholderText(text)
			self.daq.DAQScopeGainSlider.setValue(int(text))
			self.daq.DAQScopeGainValue.setText("")
	def scam_gain_slider_changed(self, value):
		if not self.daq.DAQScopeGainSlider.isSliderDown():
			self.scope_cam.gain_control_value = value ## set slider value
		self.daq.DAQScopeGainValue.setPlaceholderText(str(value))
		self.scope_camera_gain_value = value
		print("GAIN called, ", self.scope_camera_gain_value)
	def scam_gain_slider_released(self):
		self.scope_cam.gain_control_value = self.scope_camera_gain_value

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
		self.scope_cam.fps_control_value = fps
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
		if not self.daq.DAQBrightnessSlider.isSliderDown() and self.record_player:
			self.record_player.brightness = value
		self.brightness_value = value
		print("BRI called, ", self.brightness_value)
	def brightness_slider_released(self):
		if self.record_player:
			self.record_player.brightness = self.brightness_value
	def contrast_box_changed(self):
		text = self.daq.DAQContrastValue.text()
		if not text == "":
			self.daq.DAQContrastValue.setPlaceholderText(text)
			self.daq.DAQContrastSlider.setValue(int(text))
			self.daq.DAQContrastValue.setText("")
	def contrast_slider_changed(self, value):
		self.daq.DAQContrastValue.setPlaceholderText(str(value))
		if not self.daq.DAQContrastSlider.isSliderDown() and self.record_player:
			self.record_player.contrast = value
		self.contrast_value = value
		print("CONT called, ", self.contrast_value)
	def contrast_slider_released(self):
		if self.record_player:
			self.record_player.contrast = self.contrast_value
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

	def indep_path(self, path_):
		if not self.indep:  # main call
			path_ = os.path.join('acquisition', path_)
		return path_

	# < load & set UI >

	# def setupUi(self, ui_path):
	def setupUi(self, ui_path):
		# ui_path = u_path #'220523_DAQ_edited.ui' #'220322_0404_DAQ_edited.ui'

		ui_path = '220929_DAQ_iconUpdated.ui'
		ui_path = self.indep_path(ui_path)

		# self.indep = indep
		# ui_path = '220929_DAQ_iconUpdated.ui' #220726_DAQ_edited_fonted.ui #'220621_DAQ_edited_fonted.ui' #'220621_DAQ_edited.ui'
		# self.setupUi(ui_path) #'220523_DAQ_edited.ui')
		# self.buttonSet()

		self.daq = QUiLoader().load(ui_path) ##211102 #edited.ui') ## .ui')
		self.setCentralWidget(self.daq)

		self.ui_update()
		#self.ui_name_update()

	def ui_update(self):
		#self.daq.label_153.setText("255") #exposure maximum
		self.daq.DAQScopeExposureSlider.setMaximum(255)
		#self.daq.label_146.setText("16") #gain min 1x
		#self.daq.label_152.setText("64") #gain max 4x
		self.daq.DAQScopeGainSlider.setMinimum(16)
		self.daq.DAQScopeGainSlider.setMaximum(64)
		self.daq.DAQScopeFRValue.setEnabled(False) #ban FPS control with typing
		self.daq.DAQScopeFRSlider.setTracking(False) #slider tracking off

	def ui_name_update(self):
		self.daq.DAQLayout1 = self.daq.pushButton_32
		self.daq.DAQLayout2 = self.daq.pushButton_33
		self.daq.DAQLayout3 = self.daq.pushButton_34

	def set_os(self, os_name):
		os_name_list = ['windows', 'linux']
		assert os_name in os_name_list, 'check os name setting'
		self.os_num = os_name_list.index(os_name)

	### camera indexing
	def cam_ix(self, leng):
		cam_list = []
		for i in range(leng):
			cap = cv2.VideoCapture()  ## cv2.CAP_DSHOW + i) ## cap open
			cap.open(i, cv2.CAP_DSHOW)
			if cap.read()[0]:
				cam_list.append(i)
			cap.release()  ### --
		return cam_list

	## TODO: can be replaced by pycameralist
	def cam_refresh(self):

		self.daq.statusbar.showMessage('camara scan started')
		a = ""

		print("refresh start")
		dev_list = self.get_devlist()
		cam_nlist = self.cam_ix(len(dev_list))
		print("get camnlist: ", cam_nlist)
		print("dev list: ", dev_list)

		for i in cam_nlist:
			a = a + str(i) + ': ' + dev_list[i] + '\n'

		if a == '':
			self.daq.statusbar.showMessage('--no camera detected--')
		self.daq.camera_list.setText(a)



	def get_devlist(self):
		dev_list = []  ### temp
		graph = FilterGraph() ## can be replaced by pycameralist
		try:
			dev_list = graph.get_input_devices()
		except ValueError:
			print("-- No device found --")  ## cn sys_info_data
			self.daq.statusbar.showMessage('-- No device found --', 7000)
			self.inform_window.setText("no device found ")  ##
			self.inform_window.exec_()

		return dev_list

