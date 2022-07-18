from PySide2.QtCore import Slot
from PySide2.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QHBoxLayout,
								QMessageBox, QLabel, QWidget)
from PySide2 import QtGui, QtCore, QtWidgets
from PySide2.QtCharts import QtCharts
import cv2
import os
import pandas as pd
import platform


class OldWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setupUi()

	# camera connection

		## Behavior Camera Connection
		self.ui.connectBehaviorCameraButton.clicked.connect(self.connect_behavior_camera_button_clicked)
		self.ui.recordButton.clicked.connect(self.recording_start_stop)
		## Scope Camera Connection
		self.ui.connectScopeCameraButton.clicked.connect(self.connect_scope_camera_button_clicked)

	# slider
		## behavior exposure slider
		self.ui.exposureSliderBCam.valueChanged.connect(self.move_slider1) #self.ui.exposureValueBCam, self.ui.exposureSliderBCam.value
		self.ui.exposureValueBCam.returnPressed.connect(self.slider_box1) ## if get value  #self.ui.exposureValueBCam, self.ui.exposureSliderBCam
		## scope exposure slider
		self.ui.scopeExposureSlider.valueChanged.connect(self.move_slider8)
		self.ui.scopeExposureValue.returnPressed.connect(self.slider_box8)
		## scope LED slider
		self.ui.scopeLEDslider.valueChanged.connect(self.move_slider5)
		self.ui.scopeLEDvalue.returnPressed.connect(self.slider_box5)
		## scope Gain slider
		self.ui.scopeGainSlider.valueChanged.connect(self.move_slider6)
		self.ui.scopeGainValue.returnPressed.connect(self.slider_box6)
		## scope FR slider
		self.fvalue = [5,10,15,20,30,60]
		self.ui.scopeFRslider.valueChanged.connect(self.move_slider7)
		self.ui.scopeFRvalue.returnPressed.connect(self.slider_box7)
		## visualization slider | brightness & Constrast
		self.ui.visualBrightnessSlider.valueChanged.connect(self.move_slider2)
		self.ui.visualBrightnessValue.returnPressed.connect(self.slider_box2)
		self.ui.visualContrastSlider.valueChanged.connect(self.move_slider3)
		self.ui.visualContrastValue.returnPressed.connect(self.slider_box3)
		## overlay slider
		self.ui.overlaySlider.valueChanged.connect(self.move_slider4)
		self.ui.overlayValue.returnPressed.connect(self.slider_box4)
		
    ##------------ Recoding ---------
		self.format_list = ["wmv","avi","mp4", "tiff"]
		self.save_format = ""
		self.ui.comboBox.currentIndexChanged.connect(self.format_change) ##

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

	## -- recorded video viewer
		self.ui.pushButton_58.setText('stop')

		self.player = None
		self.fin_record_status = False

		self.s_fps = 0.0
		self.s_fps_up = False
		self.e_timer = None
		self.s_total = 0
		self.s_totalframe = 0
		self.present_time = 0

		self.ui.horizontalSlider_3.valueChanged.connect(self.slider_value_changed)
		
		self.ui.pushButton_58.clicked.connect(self.stop_button_clicked)## VPlayerStatus.-- stop>start, slider move)
		self.ui.pushButton_49.clicked.connect(self.play_button_clicked)## VPlayerStatus.-- start to pause / pause to start)
		self.ui.pushButton_55.clicked.connect(self.play_finished)
		## self.ui.pushButton_58.clicked.connect(self.player_)
		self.ui.pushButton_56.clicked.connect(self.after_player)

		self.player_scene = QGraphicsScene()
		self.ui.graphicsView_5.setScene(self.player_scene) ##-
		self.player_view = None
		self.player_view = QGraphicsView(self.player_scene, parent=self.ui.graphicsView_5) ##ui.widget_46)
		self.ui.graphicsView_5.setStyleSheet("background-color: rgb(0,0,0);")  # *# ##-

		self.player_view_item_i = QGraphicsPixmapItem()
		self.player_scene.addItem(self.player_view_item_i)

	## lever pressure_ 4 graph -------------------------------- **** ------------------------------------------------------
		p_path = os.getcwd()
		self.file_csv = p_path + '/test.csv'
		self.im_data(self.file_csv)
		## -----------------------------------------
		self.test_chart = QtCharts.QChart()
		self.test_chart.setAnimationOptions(QtCharts.QChart.AllAnimations) ## realtime-re
		## 중복조심 name
    ##    self.test_model = self.loadChartData(self.chart_df) ## self 필요 check
		self.add_series("lever-data", [0,1])
		## creating QChartView
		self.chart_view = QtCharts.QChartView(self.test_chart)
		self.chart_view.setRenderHint(QtGui.QPainter.Antialiasing) ## clear line
		self.main_layout = QHBoxLayout(self.ui.widget_10) #######################3)
    #widgetsize#    size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    #widgetsize#    self.chart_view.setSizePolicy(size)
		self.main_layout.addWidget(self.chart_view)
		self.setLayout(self.main_layout)  #####################

	### default cam widget disable--------------------------
		self.ui.widget_8.setEnabled(False) ## behavior
		self.ui.widget_9.setEnabled(False) ## scope

		self.ui.widget_2.setEnabled(False) ## record

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

	## os check
		self.user_os = platform.system()
		sys_info_data = ("system OS: " + self.user_os + "\n")*10 + (f'device: {self.dev_list}') ## H add function 처리
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
		self.ui.BnumBox.setValidator(QtGui.QRegExpValidator(regExp,self))
		self.ui.SnumBox.setValidator(QtGui.QRegExpValidator(regExp,self))
		self.ui.set_cnum_button.clicked.connect(self.set_cam_number)
		## self.cam_nlist = None


	## scope camera box

		self.scope_camera_scene = QGraphicsScene()

		self.scope_camera_view = QGraphicsView(self.scope_camera_scene, parent=self.ui.widget_71) ## w5->widget_71-> graphicsView_5
		#+# self.scope_camera_view = QGraphicsView(self.scope_camera_scene)#, parent=self.ui.graphicsView_5) ## w5->widget_71->

		#self.behavior_camera_view.setMinimumSize(QtCore.QSize(1020, 640))
		self.scope_camera_view.setStyleSheet("background-color: rgb(0, 0, 0);")
		#self.behavior_camera_view.setObjectName("scope_camera_view")
		self.scope_camera_view_item_i = QGraphicsPixmapItem()
		self.scope_camera_scene.addItem(self.scope_camera_view_item_i)

		##### ui 처리
		self.gridLayout_f71 = QtWidgets.QGridLayout(self.ui.scope_camera_view_item)
		self.gridLayout_f71.addWidget(self.scope_camera_view)
		self.ui.widget_71.hide()

		self.ui.tabWidget.setCurrentIndex(0)
		
		self.ui.pushButton_19.pressed.connect(self.ww1)
		self.ui.pushButton_18.pressed.connect(self.ww2)

	## behavior camera box
		self.behavior_camera_view = self.ui.behavior_camera_view_item
		self.behavior_camera_scene = QGraphicsScene()
		self.behavior_camera_view = QGraphicsView(self.behavior_camera_scene, parent=self.ui.widget_4)
		#self.behavior_camera_view.setMinimumSize(QtCore.QSize(1020, 640))
		self.behavior_camera_view.setStyleSheet("background-color: rgb(0, 0, 0);")
		#self.behavior_camera_view.setObjectName("scope_camera_view")
		self.behavior_camera_view_item_i = QGraphicsPixmapItem()
		self.behavior_camera_scene.addItem(self.behavior_camera_view_item_i)
		#왜 없냐 self.ui.gridLayout_6.addWidget(self.behavior_camera_view, 1, 1, 1, 2)

	## loading box
		t_lay_parent = QtWidgets.QVBoxLayout()
		self.ld_widget=QWidget(self.ui.widget_103)
		#self.ui.widget_103.setLayout(t_lay_parent)
		self.ld_widget.setLayout(t_lay_parent)
		self.ld_widget.setGeometry(218,20,895,556)
#        t_lay_parent=ld_widget.QVBoxLayout()

		self.m_play_state=False

		self.m_label_gif = QLabel()
		t_lay_parent.addWidget(self.m_label_gif)
		#self.ui.scope_camera_view_item_2.addWidget(self.m_label_gif)
				
		self.m_movie_gif = QtGui.QMovie("ldld.gif")
		self.m_label_gif.setMovie(self.m_movie_gif)
		self.m_label_gif.setScaledContents(True)
		self.m_label_gif.hide()
		self.ld_widget.hide()

# 		funtions -----------

	## close event
	def closeEvent(self, event): ## how-signal ## temp ?
		if self.capturer is not None: ##
			self.capturer.stop() ##? -- stop
		QMainWindow.closeEvent(self, event)

	def closeEvent2(self, event):
		if self.capturer2 is not None:
			self.capturer2.stop()
		QMainWindow.closeEvent2(self, event)

	def closeEvent3(self, event):
		if self.player is not None:
			self.player.stop()
		QMainWindow.closeEvent3(self, event)

	## recording
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
			self.stop_connection() ##

		## screen shot
	@Slot()
	def save_screen_shot(self):
		if self.capturer:
			self.capturer.save_one_screen_shot = True
		if self.capturer2:
			self.capturer2.save_one_screen_shot = True

	@Slot()                                              
	def connect_behavior_camera_button_clicked(self):
		text = self.ui.connectBehaviorCameraButton.text()
		if text == 'Behavior\n''Connect' and self.capturer is None:

            ## camera_ID = self.cam_num #1
			#camera_ID = cv2.CAP_DSHOW + self.Bnum ##
			camera_ID = self.Bnum

			self.capturer = CaptureThread(camera=camera_ID, video_path=self.save_path, lock=self.data_lock, parent=self, user_path=self.user_path, f_type=self.save_format, pj_name=self.project_name, scopei=True) ##받는 ##par-처리
			self.capturer.frameCaptured.connect(self.update_behavior_camera_frame) ## frame 연결
			self.capturer.fpsChanged.connect(self.update_behavior_camera_FPS) ##
			self.capturer.start() 
		
			## default fps
			self.default_fps(20)

          #  self.exposure_control(int(self.ui.exposureSliderBCam.value))
          # self.capturer.
          ### nd2 set policy / (!>interruption 고려)
			self.ui.connectBehaviorCameraButton.setText('Behavior\n''Disconnect')
			self.ui.signBehaviorCamera.setStyleSheet("background-color: rgb(0, 255, 0);") ## > func or not
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
            
			self.capturer.frameCaptured.disconnect(self.update_behavior_camera_frame) ##
			self.capturer.fpsChanged.disconnect(self.update_behavior_camera_FPS)
			self.capturer.stop()
			self.capturer = None

			self.ui.connectBehaviorCameraButton.setText('Behavior\n''Connect') ## set text ##
			self.ui.signBehaviorCamera.setStyleSheet("background-color: rgb(85, 85, 127);") ## > func or not
			self.ui.behaviorcamStatusLabel.setText('Disconnected')

			self.disable_cam('B')
			self.ui.widget_2.setEnabled(False)
			## self.disable_cam('S') ## temp

	# scope camera connection
	@Slot()
	def connect_scope_camera_button_clicked(self):
		print("sign-sign")
		text = self.ui.connectScopeCameraButton.text()
		if text == 'Scope\n''Connect' and self.capturer2 is None: ## check - capturer
			## camera_ID = self.mini_num #0
			camera_ID = cv2.CAP_DSHOW + self.Snum ##

			print("Camera_no.1")
			self.capturer2 = CaptureThread(camera=camera_ID, video_path=self.save_path, lock=self.data_lock, parent=self, user_path=self.user_path, f_type=self.save_format, pj_name=self.project_name, scopei=False) ## VP- ##par-처리
			self.capturer2.frameCaptured.connect(self.update_scope_camera_frame)
			self.capturer2.fpsChanged.connect(self.update_scope_camera_FPS)
			self.capturer2.start()

			## record finished
			self.capturer2.videoSaved.connect(self.record_finished)

			self.ui.connectScopeCameraButton.setText('Scope\n''Disconnect')
			self.ui.signScopeCamera.setStyleSheet("background-color: rgb(0, 255, 0);")
			self.ui.scopecamStatusLabel.setText('Connected')

			self.ui.widget_2.setEnabled(True) ##

			if self.player is not None:
				self.play_finished()

			if self.fin_record_status:
				self.ui.widget_71.hide()
				self.scope_camera_view.show()

			self.capturer2.fps_calculating = True ###

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

    # behavior camera image frame/FPS
	@Slot(QtGui.QImage) ## camera image
	def update_behavior_camera_frame(self, image):
		pixmap = QtGui.QPixmap.fromImage(image)
		#self.ui.behavior_camera_view_item.setPixmap(pixmap)
		## rule/
		temp_width2 = self.behavior_camera_view.width()
		if self.temp_width != temp_width2:
			self.temp_width = temp_width2
			print(self.temp_width)
		## print(self.behavior_camera_view.width())
		pixmap = pixmap.scaledToWidth(self.behavior_camera_view.width()) ## 4
		## pixmap = pixmap.scaledToWidth(self.ui.widget_4.width())
		self.behavior_camera_view_item_i.setPixmap(pixmap)

	@Slot(float)
	def update_behavior_camera_FPS(self, fps):
		self.ui.behavior_fps.setText(f'FPS: {fps}')
		# print('B_fps: ', fps)
##        self.ui.behavior_camera_FPS_label.setText(f'FPS: {fps}') ## --format--/stEr 
        ## behavior_camera_FPS_label

    # scope camera image frame/FPS
	@Slot(QtGui.QImage)
	def update_scope_camera_frame(self, image):
		pixmap = QtGui.QPixmap.fromImage(image)
		pixmap = pixmap.scaledToWidth(self.scope_camera_view.width()) ## 5
		## pixmap = pixmap.scaledToWidth(self.ui.widget_5.width())
		self.scope_camera_view_item_i.setPixmap(pixmap) ## ui, _i
		#self.ui.scope_camera_view_item_i.setPixmap(pixmap)

	@Slot(float)
	def update_scope_camera_FPS(self,fps):
		self.ui.scope_fps.setText(f'FPS: {fps}')

        ## self.s_fps = fps
        ## self.s_fps_up = True
        ## self.ui.scopeFRvalue.setText(f'{round(self.s_fps)}')
        ## self.slider_box7()
        ## print('S_fps: ', fps) ####
        ## self.s_fps_up = False

	def set_scope_fps(self, fps):

		fps_d = {5:4,7:6,8:6,9:6,10:12,11:12}
		fps = fps/5
		if fps in list(fps_d.keys()):
			fps = fps_d[fps]

		self.capturer2.cfps = fps*5
		## self.capturer2.set(cv2.CAP_PROP_FPS, fps)

	def set_behavior_fps(self, fps):
		self.capturer.cfps = fps

	## exposure control   ### seems, miniscope used brightness for exposure > need to change
	def exposure_control_b(self, val):
		val = val/100 * 64
		self.capturer.exposure_status = val ##self.ui.exposureSliderBCam.value() ## ab on/
		## self.ui.label_59.setText("FPS: " + str(self.capturer.exposure_status))
		## self.ui.label_59.setText(f"FPS: {self.ui.exposureSliderBCam.value()}")

	def exposure_control_s(self, val):
		val = val/100 * 64
		self.capturer2.exposure_status = val

	@Slot()
	def move_slider1(self, sl_val):
		#happy = self.ui.exposureSliderBCam.value()
		#print(happy)
		print(sl_val)
		print("moved")
		self.ui.exposureValueBCam.setPlaceholderText(str(sl_val))
		#a.setPlaceholderText(str(sl_val))
		#sl_value = QtGui.QMouseEvent(sl_val)
				
		## exposure - apply value
		self.exposure_control_b(sl_val)

    # # self.exposureValueBCam.setPlaceholderText

	@Slot()
	def slider_box1(self):
		#=self.ui.exposureValueBCam.setPlaceholderText()
		
		##
		set_v=int(self.ui.exposureValueBCam.text())
		#print(v.text())
		#set_v=v.text()
		#self.ui.exposureValueBCam.setPlaceholderText(str(set_v))
		self.move_slider1(set_v)
		#v.setPlaceholderText(set_v)
		self.ui.exposureSliderBCam.setValue(set_v)
		#if v.text() != "":
		#    s.setValue(int(set_v))
		self.ui.exposureValueBCam.setText("")
		#v.setText("")
		#exposure

    ## binding. super.class / @slot

## Visualization brightness 
	@Slot()
	def move_slider2(self, sl_val):
		print(sl_val)
		print("moved")
		self.ui.visualBrightnessValue.setPlaceholderText(str(sl_val))
   
	@Slot()
	def slider_box2(self):    
		set_v=int(self.ui.visualBrightnessValue.text())
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
		set_v=int(self.ui.visualContrastValue.text())
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
		set_v=int(self.ui.overlayValue.text())
		self.ui.overlayValue.setPlaceholderText(str(set_v))
		self.ui.overlaySlider.setValue(set_v)
		self.ui.overlayValue.setText("")


## scope LED slider

	@Slot()
	def move_slider5(self, sl_val):
		print(sl_val)
		print("moved")
		self.ui.scopeLEDvalue.setPlaceholderText(str(sl_val))
		self.capturer2.hue_value = sl_val
   
	@Slot()
	def slider_box5(self):    
		set_v=int(self.ui.scopeLEDvalue.text())
		self.move_slider5(set_v)
		self.ui.scopeLEDslider.setValue(set_v)
		self.ui.scopeLEDvalue.setText("")

## scope Gain slider  #####

	@Slot()
	def move_slider6(self, sl_val):
		print(sl_val)
		print("moved")
		self.ui.scopeGainValue.setPlaceholderText(str(sl_val))
		# ab gain scale/
		# self.capturer2.gain_status = sl_val
		self.capturer2.gain_status = sl_val
		
	@Slot()
	def slider_box6(self):
		set_v=int(self.ui.scopeGainValue.text())
		#self.ui.scopeGainValue.setPlaceholderText(str(set_v))
		self.move_slider6(set_v)
		self.ui.scopeGainSlider.setValue(set_v)
		self.ui.scopeGainValue.setText("")


## scope FR slider

	@Slot()
	def move_slider7(self, sl_val_r):
		print("dex ",sl_val_r)
		sl_val = self.fvalue[sl_val_r] #[5,10,15,20,30,60]
		print(sl_val)
		print("moved")
		self.ui.scopeFRvalue.setPlaceholderText(str(sl_val))
		if self.capturer2 is not None and not self.s_fps_up:
			self.set_scope_fps(sl_val)
		if self.capturer is not None and not self.s_fps_up:
			self.set_behavior_fps(sl_val)
   
	@Slot()
	def slider_box7(self):    
		set_v=int(self.ui.scopeFRvalue.text())
		## self.ui.scopeFRvalue.setPlaceholderText(str(set_v))

		if (set_v/5 -1)>= 8: v = 5
		elif (set_v/5 -1)>= 4: v = 4
		elif (set_v/5 - 1)<0 : v = 0
		else:  v = int(set_v/5 - 1)
		print('v ',v)
		self.move_slider7(v) #set_v
		self.ui.scopeFRslider.setValue(v)
		self.ui.scopeFRvalue.setText("")
				

## scope Exposure slider

	@Slot()
	def move_slider8(self, sl_val):
		print(sl_val)
		print("moved")
		self.ui.scopeExposureValue.setPlaceholderText(str(sl_val))
		self.exposure_control_s(sl_val)
		
	@Slot()
	def slider_box8(self):    
		set_v=int(self.ui.scopeExposureValue.text())
		# self.ui.scopeExposureValue.setPlaceholderText(str(set_v))
		self.move_slider8(set_v)
		self.ui.scopeExposureSlider.setValue(set_v)
		self.ui.scopeExposureValue.setText("")
				

## scope Exposuretime slider

	@Slot()
	def move_slider9(self, sl_val):
		print(sl_val)
		print("moved")
####        self.ui.scopeETvalue.setPlaceholderText(str(sl_val))
   
####    @Slot()
####    def slider_box9(self):    
####        set_v=int(self.ui.scopeETvalue.text())
####        self.ui.scopeETvalue.setPlaceholderText(str(set_v))
####        self.ui.scopeETslider.setValue(set_v)
####        self.ui.scopeETvalue.setText("")


## --------window------
	@Slot()
	def selectD(self):
		self.save_path = str(QFileDialog.getExistingDirectory(self,"select Directory"))
		self.ui.lineEdit_26.setText(self.save_path)
		self.user_path = True


	@Slot()
	def push_dir(self): ## Home
		saving_location = self.save_path
		self.project_name = self.ui.lineEdit.text() ## project name - rbmi 연계변경

		if self.capturer: 
			self.capturer.video_path = self.save_path
			self.capturer.project_dir = self.project_name
		if self.capturer2: 
			self.capturer2.video_path = self.save_path
			self.capturer2.project_dir = self.project_name
        
        ## default data - auto/
        ## Hwabt- cache save/

		self.save_format = self.format_list[self.ui.comboBox_3.currentIndex()]   ## number check/
		print("saveformat: ", self.save_format)
		self.ui.comboBox.setCurrentIndex(self.ui.comboBox_3.currentIndex())
	
		window_name = f'New Project - {self.project_name}({saving_location})' # project
		
		self.ui.label_113.setGeometry(QtCore.QRect(20,12,500,21)) ## temp size up
		self.ui.label_113.setText(window_name) ## throw data
		
        #82 21 500 21
       
        ## self.ui.scrollArea_4 

		##self.ui.tabWidget.setCurrentIndex(1)

	@Slot()
	def leverP_vi(self): ## leverwindow
		if self.leverpVS:
			self.ui.widget_10.hide()
			self.leverpVS = False
		else: 
			self.ui.widget_10.show()
			self.leverpVS = True

	@Slot()
	def behavP_vi(self): ##behavwindow
		if self.behavPVS:
			self.ui.widget_4.hide()
			self.behavPVS = False
		else: 
			self.ui.widget_4.show()
			self.behavPVS = True

	@Slot()
	def scopeP_vi(self):
		if self.scopeVS:
			self.scope_camera_view.hide() ## -ui
			self.scopeVS = False
		else: 
			self.scope_camera_view.show() ## -ui
			self.scopeVS = True


### format change
	@Slot()
	def format_change(self):
		if self.capturer:
			self.capturer.save_format = self.ui.comboBox.currentText()
		if self.capturer2:
			self.capturer2.save_format = self.ui.comboBox.currentText()

### record timer
	def rec_timer(self, status: bool):
		if status:
			self.s_total = 0
			self.e_timer = QtCore.QTimer(self)
			self.e_timer.timeout.connect(self.elapsed_time)
			self.e_timer.start(10)
		else:
			self.e_timer.stop()

## camera indexing
	def cam_ix(self):
		cam_list = []
		for i in range(len(self.dev_list)):
			cap = cv2.VideoCapture() ## cv2.CAP_DSHOW + i) ## cap open
			cap.open(i, cv2.CAP_DSHOW)
			if cap.read()[0]:
				cam_list.append(i)
				#cap.read()[0]
			cap.release() ### --
		return cam_list


### lever press record
	@Slot()
	def leverP_rec(self):

		if self.leverP_recVS:
			self.ui.graphicsView.hide()
			self.leverP_recVS = False
		else: 
			self.ui.graphicsView.show()
			self.leverP_recVS = True

## import data -- lever
	def im_data(self, file_name):
		self.chart_df = pd.read_csv(file_name)

	def add_series(self, name, columns):
		self.series = QtCharts.QLineSeries()
		self.series.setName(name)

		for i in range(self.chart_df.shape[0]): ##self.coulumn_count):
			## t = self.input_time[i]
			t = self.chart_df['time'][i]
			x = t ## .toMSecsSinceEpoch()
			## y = float(self.input_value[i])
			y = float(self.chart_df['mag'][i])

			if x>= 0 and y>=0:
				self.series.append(x,y)
		self.test_chart.addSeries(self.series)

	def stop_connection(self):
		### Hwab con/
		if self.ui.connectBehaviorCameraButton.text() == 'Behavior\n''Disconnect' and self.capturer is not None: 
			self.connect_behavior_camera_button_clicked()
			self.set_cam_number() ## func 보완필요
		if self.ui.connectScopeCameraButton.text() == 'Scope\n''Disconnect' and self.capturer2 is not None:
			self.connect_scope_camera_button_clicked()
			self.set_cam_number() ## func 보완필요

## show player

	## player1
	@Slot(QtGui.QImage)
	def update_player_frame(self, image):
		pixmap = QtGui.QPixmap.fromImage(image)
		## width control
		pl_width2 = self.player_view.width() #view?
		if self.pl_width != pl_width2:
			self.pl_width = pl_width2
			print('plW', self.pl_width)
		self.player_view_item_i.setPixmap(pixmap)
		self.frame_slider_update(self.player.present_frame)

	def show_player(self):
		print('saving file...')
		time.sleep(0.5)
		self.scope_camera_view.hide()
		print('opening file...')
		time.sleep(0.5)
		self.ui.widget_71.show()

		self.player = VPlayer(v_path=self.capturer2.video_file, lock=self.data_lock, parent=self, fps=self.s_fps)
		self.player.start()

		duration = self.s_total
				
		print(duration)
		self.s_totalframe = self.capturer2.count_frames
		self.update_v_duration(duration*10, self.s_totalframe) ## self.player.total_frame)
				

		print('player started')
		## self.push_img(self.present_status,capture)

	def push_img(self, state: int, capt: cv2.VideoCapture):

		capt.set(cv2.CAP_PROP_POS_FRAMES, state)
		while True:
			ret, frame = capt.read()
			## 상태 확인해서 계속 진행 또는 종료.
            ## 미리 set 상태. 

	@Slot()
	def play_button_clicked(self):
		text = self.ui.pushButton_49.text()
		if self.player is not None and text == 'play':
			self.player.frameC.connect(self.update_player_frame)
			self.player.vplayer_status = VPlayerStatus.STARTING
			print("set starting")
			self.ui.pushButton_49.setText('pause')
		elif self.player is not None and text == 'pause':
			self.player.vplayer_status = VPlayerStatus.PAUSING
			self.player.frameC.disconnect(self.update_player_frame)
			print("set pausing")
			self.ui.pushButton_49.setText('play')
        
		self.player.stateCh.connect(self.stop_button_clicked)

    ## player1
	@Slot()
	def stop_button_clicked(self, a):
		if self.player is not None:
			self.player.vplayer_status = VPlayerStatus.STOPPING 
			self.ui.pushButton_49.setText('play')
			self.ui.horizontalSlider_3.setValue(0)
			print("set stopping")
		if a == 1:
			self.player.stateCh.disconnect(self.stop_button_clicked) ## _

	@Slot()
	def play_finished(self):
		if self.player is not None:
			self.player.stop()
			self.player = None
			print("OK")
			self.fin_record_status = True

	def after_player(self):
		self.play_finished()
		## self.ui.tabWidget.setCurrentIndex(2)
		print('next tab --')

	def frame_slider_update(self, present_f):
		## if self.player is not None:
				
		self.ui.horizontalSlider_3.blockSignals(True)
		self.ui.horizontalSlider_3.setValue(present_f)
		self.ui.horizontalSlider_3.blockSignals(False)
		print(f'sliderposition: {present_f}')
		self.frame_slider_update_p(present_f)

	def elapsed_time(self):
		self.s_total = self.s_total + 1
		total = self.s_total*10
		## print(total)
		time = self.hhmmss(total)
		self.ui.label_24.setText(f'Elapsed time: {time}')
		self.ui.label_25.setText(f'Record length: {self.capturer2.count_frames}')

	def frame_slider_update_p(self, present_f):
		self.ui.label_87.setText(f'Frame: {int(present_f)}')
		self.present_time = present_f*self.s_total*10/self.s_totalframe
		self.ui.label_84.setText(self.hhmmss(self.present_time))

## camera list
	@Slot()
	def cam_refresh(self):
		if self.ui.widget_2.isEnabled():
			self.mnotice.setText("turn off the camera first please") ## temporary
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

	def ww1(self):
		self.ui.graphicsView_5.hide()

	def ww2(self):
		self.ui.graphicsView_5.show()


	def hhmmss(self, ms):
		## 1000/60000/360000
		s = round(ms/1000)
		m,s = divmod(s,60)
		h,m = divmod(m,60)
		return ("%d:%02d:%02d" % (h,m,s)) if h else ("%d:%02d" % (m,s))            


	## player1
	def update_v_duration(self, duration, f_duration):

		self.ui.horizontalSlider_3.setMaximum(f_duration) ## see max
		print(f'set maxvalue: {f_duration}')
		if duration >= 0:
			self.ui.label_131.setText(self.hhmmss(duration))

        ## duration update
        ## label_131 _last 00:00

	def update_v_position(self, position): #upt

		if position >= 0:
            ## self. timer 생산  start restart stop elasped

			self.ui.label_84.setText(self.hhmmss(position)) ## moving -

		self.ui.horizontalSlider_3.blockSignals(True)
		self.ui.horizontalSlider_3.setValue(position)
		self.ui.horizontalSlider_3.blockSignals(False)

	@Slot()
	def slider_value_changed(self):
		if self.player is not None:

			present_f = self.ui.horizontalSlider_3.value()
			self.player.present_frame = present_f  ##self
			self.frame_slider_update_p(present_f)

			if self.ui.pushButton_49.text() == 'pause':
				## self.ui.pushButton_49.setText('play') # autoplay
				self.play_button_clicked() ##with stateCh
			else:
				self.player.vplayer_status = VPlayerStatus.MOVING
            



	def get_devlist(self):
		self.dev_list = [] ### temp
		graph = FilterGraph()
		try: self.dev_list = graph.get_input_devices()
		except ValueError:
			print("-- No device found --") ## cn sys_info_data
			self.ui.statusbar.showMessage('-- No device found --',7000)
			self.mnotice.setText("no device found ") ##
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
			self.ui.statusbar.showMessage('-- No miniscope found --',7000)
			print('--no miniscope found--')
		return self.mini_num


	@Slot()
	def set_cam_number(self): ## check mini_num and cam_num ###

		self.ui.statusbar.showMessage('camera setting') ## ch2 emit
		Bn = self.ui.BnumBox.text()
		Sn = self.ui.SnumBox.text()

		if Bn == '' and Sn == '':
			self.mnotice.setText("(temp) set camera number again please ") ## temporary
			self.mnotice.exec_()
			return

		Bn = int(Bn)
		Sn = int(Sn)

        #if type(Bn) or type(Sn) is not :
        #    self.mnotice.setText("check your input please")
        #    self.mnotice.exec_()

        ## print(type(self.ui.BnumBox.text()))
        ## print(self.cam_nlist, type(self.cam_nlist[0])) ## int
        ## print("Bnt: ", type(Bn)) ## str
        ## print(f'b: {Bn}, s: {Sn}')

		if (Bn in self.cam_nlist) and (Sn in self.cam_nlist): ## 각 조건
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
			self.ui.statusbar.showMessage('check the numbers please',10000)
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
		self.ui.statusbar.showMessage('record finished',10000)
		self.mnotice.setText(f"record finished \n {a}")



    ### ------ software system ----

	def d_widget_scope(self):
		self.ui.widget_9.setEnabled(False)
	def e_widget_scope(self):
		self.ui.widget_9.setEnabled(True)

	## ------ default setting -----?
	def default_fps(self, v):
		self.ui.scopeFRvalue.setText(str(v))
		self.slider_box7()


	## < setup UI >

	def setupUi(self):
		#self.ui = QUiLoader().load('210831_DAQp.ui')
		self.ui = QUiLoader().load('210513_OMBI_UI.ui')
		self.setCentralWidget(self.ui)
		
'''
		self.connectBehaviorCameraButton
		self.widget_8
		self.behavior_camera_view_item
		self.pushButton_21
		self.behaviorcamStatusLabel
		self.cam_nums
		self.widget_4
		self.exposureSliderBCam
		self.exposureValueBCam
		self.signBehaviorCamera
		self.visualBrightnessSlider
		self.visualBrightnessValue
		self.widget_21
		self.catch_camlist
		self.visualContrastSlider
		self.label_21
		self.label_131
		self.label_87
		self.pushButton_17
		self.pushButton_18
		self.pushButton_19
		self.graphicsView
		self.widget_10
		self.pushButton_22
		self.scrollArea_2
		self.overaySlider
		self.overlayValue
		self.pushButton_56
		self.pushButton_55
		self.pushButton_49
		self.hrizontalSlider_3
		self.pushButton_58
		self.widget_2
		self.recordButton
		self.comboBox
		self.label_25
'''
