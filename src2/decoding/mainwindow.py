from PySide2.QtWidgets import QMainWindow
from PySide2.QtUiTools import QUiLoader

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setupUi()


	def setupUi(self):
		self.decoding = QUiLoader().load('210802_Decoding.ui')
		self.setCentralWidget(self.decoding)



