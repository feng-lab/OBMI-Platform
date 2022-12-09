from PySide2.QtWidgets import QDialog
from PySide2.QtUiTools import QUiLoader
import os

class ProgressWindow(QDialog):
    def __init__(self, min_v=0, max_v=100, indep=False):
        super().__init__()
        self.indep = indep
        self.setupUi('220823_progress_win.ui')
        self.pg_ui.cancel_button.clicked.connect(self.cancel_win)
        self.pgbar = self.pg_ui.progressBar
        # self.pgbar.valueChanged.connect(self.xupdate_state_rate)
        self.value = 0

        self.pgbar.setMaximum(max_v)
        self.pgbar.setValue(min_v)
        self.cancel_state = False

    def update_value(self, value):
        print(value)
        self.pgbar.setValue(value)
        return self.cancel_state
    # def xupdate_state_rate(self, value):
    #     print(value)
    #     self.value = value

    def close_win(self):
        self.pg_ui.close()
        return self.value

    def cancel_win(self):
        print(self.value)
        self.cancel_state = True
        return self.close_win()

    def indep_path(self, path_):
        if not self.indep:
            path_ = os.path.join('home', path_)
        return path_

    def setupUi(self, ui_path):
        ui_path = self.indep_path(ui_path)
        self.pg_ui = QUiLoader().load(ui_path)

    def showWin(self):
        self.pg_ui.exec_()
        return True