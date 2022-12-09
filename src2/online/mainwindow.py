from PySide2.QtWidgets import QMainWindow
from PySide2.QtUiTools import QUiLoader

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setupUi()

	def setupUi(self):

		# ## expand version -> default hide 방식으로.
		# self.online1 = QUiLoader().load('210802_Online_1_Hide.ui')
		# self.online2 = QUiLoader().load('210802_Online_2_ROIEditShow.ui')
		# self.online3 = QUiLoader().load('210802_Online_3_ScopeConnectShow.ui')
		self.online1 = QUiLoader().load('220705_Online_1_Hide_edited.ui')
		self.online2 = QUiLoader().load('220705_Online_2_ROIEditShow_edited.ui')
		self.online3 = QUiLoader().load('220705_Online_3_ScopeConnectShow_edited.ui')
		self.setCentralWidget(self.online1)


from PySide2.QtWidgets import QFileDialog, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem
from PySide2.QtCore import Slot
from PySide2 import QtCore, QtGui, QtWidgets
from online_player import OPlayer
from mccc import MCC

class OldWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setupUi()
		
		self.on_scope = None
		self.data_lock = QtCore.QMutex()
		self.ui.OnScopeCamButton.clicked.connect(self.online_scope) ## FTB, saved clip

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
		self.ui.OnAutoROIButton.clicked.connect(self.auto_roi)

	# scope camera connection
	def online_scope(self):
		## video connect
		text = self.ui.OnScopeCamButton.text()
		if text == 'Scope\nConnect' and self.on_scope is None:
			print('button clicked')
			self.open_video_path = str(QFileDialog.getOpenFileName(self, "select media file",'./','Video (*.mp4 *.wma *.avi)')[0])
			camera_ID = self.open_video_path ### temp  

			self.on_scope = OPlayer(camera=camera_ID, lock=self.data_lock, parent=self)
			self.on_scope.frameI.connect(self.online_frame)
			self.on_scope.start()

			self.ui.OnScopeCamButton.setText('Scope\nDisconnect')

		elif text == 'Scope\nDisconnect' and self.on_scope is not None:
			self.on_scope.frameI.disconnect(self.online_frame)
			self.on_scope.stop()
			self.on_scope = None
            
			self.ui.OnScopeCamButton.setText('Scope\nConnect')

	@Slot(QtGui.QImage)
	def online_frame(self, image):
		pixmap = QtGui.QPixmap.fromImage(image)
		self.onplayer_view_item.setPixmap(pixmap)


	# processing    ## need to be re-organized
	def pre_process(self):
		print('preprocess clicked')
        
		scope_num = self.open_video_path ##0
		#self.on_template = None
		# motion correction box - Hwa? pre-definition

		text = self.ui.OnScopeCamButton.text()
		if self.ui.OnMotionCorrectionCheck.isChecked(): 
			## video stop
			if text == 'Scope\nDisconnect' and self.on_scope is not None:
				self.on_scope.frameI.disconnect(self.online_frame)
				self.on_scope.stop()
				self.on_scope = None
            
				self.ui.OnScopeCamButton.setText('Scope\nConnect')
                
			self.MC = MCC(scope_num, self)

			#d_i ### update policy - 다되면 없애는 거 등 필요 ##
			self.mccbar = QtWidgets.QProgressBar()
			self.Statusbar.addWidget(self.mccbar)
			self.mccbar.setMaximum(200)

			self.MC.signalPPe.connect(self.prebar)
            
			self.on_template = self.MC.g_temp(scope_num)
			print('button preprocess done')
			self.Statusbar.showMessage('-- preprocess done --')

		else: ### arrange if phrase with options ----- ***
			print('---- no option selected ----')
			self.Statusbar.showMessage('-- motion correction X --')
			
        # get crop size
        ## crop_size=self.ui.comboBox_5.currentText()
        
        # get Neuron Size ##?

        # generate template

    ##prebar
	def prebar(self, n): ## 중복해결필요    ## 200 template 
        
		#d_i
		#c
		self.mccbar.setValue(n)
    
	def auto_roi(self):
		pass
		if not self.ui.OnMotionCorrectionCheck.isChecked(): ## need to change  - check option **
			self.Statusbar.showMessage('-- auto roi - processing.. --')
			pass
        ## need to think about how many/ data for input will be used

	def rt_process(self):
		## video start
		if self.ui.OnMotionCorrectionCheck.isChecked(): ## ?could be pre-checked
			if type(self.on_template) != type(None):
				print('yes you have template')
				text = self.ui.OnScopeCamButton.text() ## 따로 
				if text == 'Scope\nConnect' and self.on_scope is None:
					camera_ID = self.open_video_path ### temp  

					self.on_scope = OPlayer(camera=camera_ID, lock=self.data_lock, parent=self)
					self.on_scope.frameI.connect(self.online_frame)
                    
					self.on_scope.start()

					self.ui.OnScopeCamButton.setText('Scope\nDisconnect')
					print('connection')

					self.MC.c_onmc = 0 ##
					self.on_scope.MC = self.MC
					self.on_scope.ged_template = self.on_template ### 
					##self.MCC.on_mc(self.on_template, )
			else: print('no template')
             ## need to check process status of processing (motion corrected | ROI selected)
		else: print('check X - motion correction ')


	def setupUi(self):
		self.ui = QUiLoader().load('210831_Online_1_Hide.ui')
		self.setCentralWidget(self.ui)



