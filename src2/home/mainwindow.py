from PySide2.QtWidgets import QMainWindow
from PySide2.QtUiTools import QUiLoader


# [New] -------------------------------------------
class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		#self.setupUi()
		

		#interface
		## File
#		self.home.HomeNewButton.clicked.connect()
#		self.home.HomeLoadButton.clicked.connect()
#		self.home.HomeSaveButton.clicked.connect()
#		self.home.ReFileButton.clicked.connect()
#		self.home.OptionBUtton.clicked.connect()
#		## Camera Setting
#		self.home.HomeCamScanButton.clicked.connect()
#		self.home.HomeBehCamValue.clicked.connect()
#		self.home.HomeScopeCamValue.clicked.connect()
#		self.HomeCamSetButton24licked.connect()
#		## Lever Setting
#		self.home.HomeLeverCOMValue.clicked.connect()
#		self.home.HomeLeverBaudButton.clicked.connect()
# 		## Project Window

	def setupUi(self):
		self.home = QUiLoader().load('220524_Home_edited_fonted.ui')
		self.setCentralWidget(self.home)

	'''
		project_file_manager - type, parser, update method
		camera_setting 
		lever_setting
	'''


# [old] structure --------------------------------

##
from datetime import datetime
from PySide2.QtWidgets import QFileDialog
from PySide2.QtCore import Slot, Signal

class OldWindow(QMainWindow):

	def __init__(self):
		super().__init__()
		self.setupUi()

		n_data = datetime.now()
		
		# project window
		self.project_name = n_data.strftime("%Y-%m-%d")
		self.ui.lineEdit.setText(self.project_name)

		# file window
		self.ui.homeBrowseButton.clicked.connect(self.selectD)
		self.save_path = ""
		self.user_path = False

		self.ui.homeSaveButton.clicked.connect(self.push_dir)

		self.format_list = ["wmv","avi","mp4", "tiff"]
		self.save_format = ""

		self.ui.comboBox_3.currentIndexChanged.connect(self.format_change)


	def selectD(self):
		self.save_path = str(QFileDialog.getExistingDirectory(self,"select Directory"))
		self.ui.lineEdit_26.setText(self.save_path)
		self.user_path = True
	
	@Slot()
	def push_dir(self):
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
	
		## self.ui.scrollArea_4 

		self.ui.tabWidget.setCurrentIndex(1)

	def format_change(self):
		if self.capturer:
			self.capturer.save_format = self.ui.comboBox.currentText()
		if self.capturer2:
			self.capturer2.save_format = self.ui.comboBox.currentText()

	def setupUi(self):
		self.ui = QUiLoader().load('210810_Home.ui')
		self.setCentralWidget(self.ui)
