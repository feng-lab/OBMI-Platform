from PySide2.QtWidgets import QDialog
from PySide2.QtUiTools import QUiLoader
import os

class OptionWindow(QDialog):
    def __init__(self, min_v=0, max_v=100, indep=False):
        super().__init__()
        self.indep = indep
        self.setupUi('220822_option_dialog_ver2.ui')

    def setupUi(self, ui_path):
        ui_path = self.indep_path(ui_path)
        self.opt_ui = QUiLoader().load(ui_path)

    def indep_path(self, path_):
        if not self.indep:
            path_ = os.path.join('home', path_)
        return path_

    def close_win(self):
        self.opt_ui.close()

    def showWin(self):
        self.opt_ui.exec_()

    def default_options(self):

        ## paths
        self.saving_directory = ''
        self.saving_format = 0 ## AVI
        self.loaded_video_path = '' ##XX

        ## data acquisition
        self.behavior_camera_number = 0
        self.behavior_exposure = None
        self.scope_camera_number = 1
        self.scope_LED_power = None
        self.scope_gain = None
        self.scope_exposure = None
        self.scope_FPS = None
        self.record_duration = 0
        self.record_file_format = 0 ## AVI 겹침

        ## data processing
        self.crop_size = 150
        self.gpu_acceleration = False
        self.remove_black_borders = False
        self.neuron_size = None
        self.edge_shape = 0 ## round, freeshape
        self.roi_style = 0 ## round, rectangular, freeshape
        self.roi_size = 10

        ## decoding
        self.decoder_input = 0 ## F
        self.decoder_type = 0 ## Kalman Filter
        self.cross_validation = 0 ## 5
        self.time_after_trail = 3
        self.decoding_on_time = 5
