from PySide2.QtWidgets import QMainWindow
from PySide2.QtUiTools import QUiLoader
import iconlist_iconUpdated
from PySide2.QtWidgets import QApplication, QWidget
import os

class MainWindow(QMainWindow):
	def __init__(self, indep=False):
		super().__init__()
		self.indep = indep
		ui_path = '220929_Decoding_layoutUpdated.ui' #'220517_Decoding_edited.ui' #'220425_Decoding_edited.ui'
		self.setupUi(ui_path)

	def indep_path(self, ui_path):
		if not self.indep:
			ui_path = os.path.join('decoding', ui_path)  # '220216_Decoding_edited.ui')
		return ui_path


	def setupUi(self, ui_path):
		ui_path = self.indep_path(ui_path)
		self.decoding = QUiLoader().load(ui_path)
		self.setCentralWidget(self.decoding)
		
		#rw = resizing_window()
		#rw._init_ui_size(self.decoding)

class resizing_window():

	def __init__(self):
		self.app = QApplication.instance()
		screen_resolution = self.app.desktop().screenGeometry()

		print(screen_resolution)
		self.hw_ratio = 1080 / 1920
		self.ratio_wid = screen_resolution.width() / 1920

		if self.ratio_wid < 1:
			self.ratio_wid = 1
		self.ratio_height = screen_resolution.height() / 1080
		if self.ratio_height < 1:
			self.ratio_height = 1
	
	def _init_ui_size(self, ui):
		self._resize_with_ratio(ui)
		for q_widget in ui.findChildren(QWidget):
			self._resize_with_ratio(q_widget)
			self._move_with_ratio(q_widget)

	def _resize_with_ratio(self, input_ui):
		input_ui.resize(input_ui.width()* self.ratio_wid, input_ui.height() * self.ratio_height)
		
	def _move_with_ratio(self, input_ui):
		input_ui.move(input_ui.x() * self.ratio_wid, input_ui.y() * self.ratio_height)

