from PySide2.QtWidgets import QDialog
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QFileDialog
from PySide2.QtCore import QTime
import os
import time
## testing 220621
from home.options import OptionFile

class ProjectWindow(QDialog):
    def __init__(self, indep=False):
        self.indep = indep
        print(self.indep)
        super().__init__()
        self.setupUi('220726_New_R.ui') #'220425_Home_New.ui' '220425_New.ui'

        self.opts = OptionFile()
        self.set_default()

        self.pjm_ui.homeDefaultButton.clicked.connect(self.set_default)
        self.pjm_ui.homeSaveButton.clicked.connect(self.save_settings)

        #self.pjm_ui.homeDefaultButton.clicked.connect(self.set_default)
        self.pjm_ui.homeBrowseButton.clicked.connect(self.browse_location)

        self.pjm_ui.homePJnameBox.textEdited.connect(self.update_pjname)


    def get_default(self, opts):
        ## if not None for load

        # project name
        project_name = opts.default_project_name()
        self.pjm_ui.homePJnameBox.setText(project_name)

        #saving location
        saving_location = opts.default_saving_location()
        self.pjm_ui.homePathBox.setText(saving_location)

        #video format
        video_format = opts.default_video_format()
        self.pjm_ui.homeVideoFormat.setCurrentIndex(video_format) #avi

        #record duration
        recording_duration = opts.default_record_duration()
        self.pjm_ui.homeRecordingDuration.setTime(QTime.fromString(recording_duration, "mm:ss"))

        return project_name, saving_location, video_format, recording_duration


    def set_default(self):
        self.project_name, \
        self.saving_location, \
        self.video_format, \
        self.record_duration  \
            = self.get_default(self.opts)


    def update_pjname(self):
        self.project_name = self.pjm_ui.homePJnameBox.text()

    def save_settings(self):

        self.opts.project_name = self.project_name ## + if blank get default
        self.opts.saving_location = self.saving_location
        self.opts.video_format = self.video_format
        self.opts.record_duration = self.record_duration

        self.project_dir = self.make_project_dir()
        self.opts.project_dir = self.project_dir

        self.write_options(self.project_dir)
        self.close_win()


    def write_options(self, saving_path): ## 별도로
        self.opts.save_to_json(saving_path)

    def make_project_dir(self):
        saving_dir = os.path.join(self.saving_location, self.project_name)
        if not os.path.isdir(saving_dir):
            os.makedirs(saving_dir)
        return saving_dir

    def browse_location(self):
        saving_path = str(QFileDialog.getExistingDirectory(self, "select Directory"))
        print(saving_path)
        if not saving_path == '': ## checck call 220621 - present dir
            self.saving_location = saving_path
            self.pjm_ui.homePathBox.setText(self.saving_location)




    def xget_default(self): ## check call 220621
        t = time.localtime()
        project_name = f'{t.tm_year}_{t.tm_mon}_{t.tm_mday}'
        saving_path = ''
        #video_format = 0
        #record_duration = #second?
        #trigger_ext = False
        return project_name, saving_path

    def indep_path(self, path_):
        if not self.indep:
            path_ = os.path.join('home', path_)
        return path_

    def setupUi(self, ui_path):
        ui_path = self.indep_path(ui_path)
        self.pjm_ui = QUiLoader().load(ui_path)

    def close_win(self):
        print('close')
        self.pjm_ui.close()

    def showWin(self):
        self.pjm_ui.exec_()
        return self.opts
        #self.project_name, self.saving_location, self.video_format, self.record_duration #, self.trigger_ext