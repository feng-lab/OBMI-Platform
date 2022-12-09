from PySide2.QtWidgets import QMainWindow, QTabWidget, QLabel, QMessageBox, QProgressBar, QProgressDialog
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import Qt
from PySide2 import QtGui
from acquisition.mainwindow import MainWindow as daqWindow
from offline.mainwindow import MainWindow as offWindow
# from online.mainwindow import MainWindow as onWindow
# from SiyiRef.offline.mainwindow import OldWindow as offWindow
# from SiyiRef.online.mainwindow import OldWindow as onWindow
from online.mainwindow import MainWindow as onWindow
from decoding.mainwindow import MainWindow as decWindow
from home.pjmanager import ProjectWindow as pjwindow
from home.progresswin import ProgressWindow as pgwindow
from home.optionwin import OptionWindow as optwindow
import os
import iconlist_iconUpdated
from glob import glob
import cv2
import time

# [New] -------------------------------------------

class uMainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.daqwindow = daqWindow()
		self.offwindow = offWindow() # Siyi
		self.onwindow = onWindow()   # Siyi
		self.decwindow = decWindow()

class MainWindow(uMainWindow):
	def __init__(self, indep=False):
		self.indep = indep
		super().__init__()
		ui_path = '220929_Home_iconUpdated.ui' #'220726_Home_edited_fonted.ui' #'220524_Home_edited_fonted.ui '220524_Home_edited.ui'

		self.setupUi(ui_path, unify=True)
		self.system_info = ''
		self.opts = None
		self.message_box()
		#print('4: ', id(self.daq))

		#interface
		## File
		self.home.HomeNewButton.clicked.connect(self.NewProject)
		self.home.HomeLoadButton.clicked.connect(self.LoadVideo)
		self.home.HomeSaveButton.clicked.connect(self.save_project)
		self.home.HomeReFileButton.clicked.connect(self.show_recent_file) # temp
		self.home.HomeOptionButton.clicked.connect(self.show_options2) # temp

#		## Camera Setting
		self.home.HomeCamScanButton.clicked.connect(self.camera_scan)
#		self.home.HomeBehCamValue.clicked.connect()
#		self.home.HomeScopeCamValue.clicked.connect()
#		self.HomeCamSetButton24licked.connect()
#		## Lever Setting
#		self.home.HomeLeverCOMValue.clicked.connect()
#		self.home.HomeLeverBaudButton.clicked.connect()
# 		## Project Window

		self.current_tab_num = 0

		self.tab_icon_list = [self.home.home_button,
							  self.home.daq_button,
							  self.home.offl_button,
							  self.home.onl_button,
							  self.home.dec_button]

		self.tab_icon_path = [('border-image: url(:/home/tab_home_1.png);','border-image: url(:/home/tab_home_2.png);'), ## on off
							  ('border-image: url(:/home/tab_acq_1.png);', 'border-image: url(:/home/tab_acq_2.png);'),
							  ('border-image: url(:/home/tab_off_1.png);','border-image: url(:/home/tab_off_2.png);'),
							  ('border-image: url(:/home/tab_on_1.png);','border-image: url(:/home/tab_on_2.png);'),
							  ('border-image: url(:/home/tab_decoding_1.png);','border-image: url(:/home/tab_decoding_2.png);')]

		self.setupIcon(0)
		## init
		[self.tab_icon_list[n].setStyleSheet(self.tab_icon_path[n][0]) if n == 0 else self.tab_icon_list[n].setStyleSheet(self.tab_icon_path[n][1]) for n in range(5)]


	def camera_scan(self):
		self.inform_window.setText("camera scaning started")
		self.home.statusbar.showMessage("camera scan started", 5000)
		self.prog_bar = QProgressBar()
		self.prog_bar.setMaximum(10)
		self.home.statusbar.addWidget(self.prog_bar)
		self.prog_bar.setValue(1)
		self.inform_window.exec_()

		#max_v = 10
		#self.prog_bar = QProgressDialog("Camera listing...", "cancel", 0, max_v, self)
		#self.prog_bar.setMinimum(0)
		#self.prog_bar.setMaximum(max_v)
		#self.prog_bar.setValue(0)
		#self.prog_bar.setWindowModality(Qt.WindowModal)

		camera_list = self.get_camera_list()
		for index in camera_list: #for index in camera_dict.keys():
			self.home.HomeBehCamList.insertItem(index, str(index)) #camera_dict[index])
			self.home.HomeScopeCamList.insertItem(index, str(index)) #camera_dict[index])
		self.camera_list = camera_list

	def get_camera_list(self):
		index = 0
		camera_list = []

		#pgwin = pgwindow(min_v=0, max_v=10)
		#pgwin.showWin()


		while index < 10:
			cap = cv2.VideoCapture(index)
			self.prog_bar.setValue(index + 1)
			try:
				if cap.getBackendName() == "MSMF":
					camera_list.append(index)
					#camera_list[index] = cap.getBackendName()
			except:
				break
			#if not pgwin.update_value(index+1):
			#	pgwin.cancel_win()

			#self.prog_bar.setValue(index*10)
			cap.release()
			#if self.prog_bar.wasCanceled(): break

			index += 1
		#pgwin.close_win()
		self.home.statusbar.removeWidget(self.prog_bar)
		return camera_list

	def show_options2(self):
		optwin = optwindow()
		optwin.showWin()

	def show_options(self):
		if self.opts == None:
			self.inform_window.setText("Please generate a new project")
			self.inform_window.exec_()
		else:
			system_info = ''
			for d in self.opts.options_list: ## home_optoin
				for k in d.keys():
					system_info += f'{k}: \n'
					#print('k: ', k)
					for prop in d[k].keys():
						system_info += f'\t{prop}: {d[k][prop]}\n'
				system_info += '\n'
			self.home.homePJinfo.setWidget(QLabel(system_info))

	def show_recent_file(self): ## recent file from present path
		searching_path = os.path.join("","*","options.json")
		opts_list = glob(searching_path)
		system_info = ''
		for n, j in enumerate(opts_list):
			d, f = os.path.split(j) #+or open and get name
			system_info += f'{str(n+1)}) {j}\n' #{os.path.basename(d)}\n' ## f'{os.path.basename(d)}: {j}\n'
		self.home.homePJinfo.setWidget(QLabel(system_info))

	def save_project(self):
		if self.opts == None:
			self.inform_window.setText("Please generate a new project")
			self.inform_window.exec_()
		else:
			## self.opts.save_options(self.opts.saving_path, self.opts.options_list)
			if self.opts.save_to_json(self.opts.project_dir):
				self.inform_window.setText(f'Project "{self.opts.project_name}" saved')
				self.inform_window.exec_()

	def LoadVideo(self):
		if self.opts == None:
			self.inform_window.setText("Please generate a new project")
			self.inform_window.exec_()
		else:
			self.load_video_path = QFileDialog.getOpenFileName(self, "Open Video", "", "Videos (*.avi)" )[0]
			if not '' == self.load_video_path:
				system_info = self.system_info
				system_info += f'Loaded video path: {self.load_video_path}\n'
				self.home.homePJinfo.setWidget(QLabel(system_info))
				self.opts.load_video_path = self.load_video_path

	def NewProject(self):
		self.ProjectWin = pjwindow(indep=self.indep)
		self.opts = self.ProjectWin.showWin()  # , triggerself.ProjectWin.showWin() #, trigger
		print(self.opts.project_name)
		self.update_info(
			self.opts.project_name,
			self.opts.saving_location,
			self.opts.video_format,
			self.opts.record_duration)

	def update_info(self, project_name, saving_location, video_format, record_duration): #, trigger ## +edit-each line
		self.home.homePJtitle.setText(project_name)
		video_format_list = ['AVI']
		#system_info += f'project name: {project_name}'
		system_info = f'Saving directory: {saving_location}\n'
		system_info += f'Saving format: {video_format_list[video_format]}\n'
		system_info += f'Recording duration: {record_duration}\n'
		## system_info += f'Trigger option: {trigger}\n'
		sys_info = QLabel(system_info)
		self.home.homePJinfo.setWidget(sys_info)
		self.system_info = system_info


	def setupIcon(self, n):
		c = self.current_tab_num
		self.tab_icon_list[c].setStyleSheet(self.tab_icon_path[c][1])
		self.tab_icon_list[n].setStyleSheet(self.tab_icon_path[n][0])

	def indep_path(self, path_):
		if not self.indep:
			path_ = os.path.join('home', path_)
		return path_

	def setupUi(self, u_path=None, unify=False):
		ui_path = self.indep_path(u_path)
		#ui_path = os.path.join('home', ui_path) #425 #'220322_Home_edited.ui')
		self.home = QUiLoader().load(ui_path) #'210810_Home.ui')

		if unify:
			#self.setupTabs()
			self.setupStack()
			# single_or_multi = self.stabs #self.tabs
		self.setCentralWidget(self.home)


	def hometab(self):
		self.setupIcon(0)
		self.home.stackedWidget.setCurrentIndex(0)
		self.current_tab_num = 0
	def daqtab(self):
		self.setupIcon(1)
		self.home.stackedWidget.setCurrentIndex(1)
		self.current_tab_num = 1
	def offtab(self):
		self.setupIcon(2)
		self.home.stackedWidget.setCurrentIndex(2)
		self.current_tab_num = 2
	def onltab(self):
		self.setupIcon(3)
		self.home.stackedWidget.setCurrentIndex(3)
		self.current_tab_num = 3
	def dectab(self):
		self.setupIcon(4)
		self.home.stackedWidget.setCurrentIndex(4)
		self.current_tab_num = 4

	def change_hh(self):
		hh = self.home.stackedWidget.currentIndex()
		self.home.stackedWidget.setCurrentIndex(hh+1)

	def setupStack(self):
		self.daq = self.daqwindow.daq
		self.offline = self.offwindow.ui
		self.online = self.onwindow.ui
		self.decoding = self.decwindow.decoding

		# self.daq = self.daqwindow.daq
		# self.offline = self.offwindow.offline
		# self.online = self.onwindow.online
		# self.decoding = self.decwindow.decoding

		self.stabs = self.home.stackedWidget
		self.stabs.addWidget(self.daq.Acquisition)
		self.stabs.addWidget(self.offline.Offline)
		self.stabs.addWidget(self.online.Online)
		self.stabs.addWidget(self.decoding.Decoding)

		self.home.daq_button.clicked.connect(self.daqtab) #self.change_hh)
		self.home.home_button.clicked.connect(self.hometab)
		self.home.dec_button.clicked.connect(self.dectab)

		self.home.onl_button.clicked.connect(self.onltab)
		self.home.offl_button.clicked.connect(self.offtab)

	def message_box(self):
		# Message Box
		self.inform_window = QMessageBox()
		self.inform_window.setWindowTitle("notice")
		self.inform_window.setWindowIcon(QtGui.QPixmap("info.png"))
		self.inform_window.setIcon(QMessageBox.Information)


	def xxsetupTabs(self):
		self.daq = self.daqwindow.daq
		#self.offline = self.offwindow.offline
		self.online = self.onwindow.online
		self.decoding = self.decwindow.decoding

		self.tabs = QTabWidget()		
		self.tabs.addTab(self.home.centralwidget, 'Home')
		self.tabs.addTab(self.daq.centralwidget, 'daq')
		#self.tabs.addTab(self.offline.centralwidget, 'offline')
		self.tabs.addTab(self.online.centralwidget, 'online')
		self.tabs.addTab(self.decoding.centralwidget, 'decoding')

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

import iconlist_iconUpdated

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
		self.ui = QUiLoader().load('210810_Home_edited.ui') #'210810_Home.ui')
		self.setCentralWidget(self.ui)
