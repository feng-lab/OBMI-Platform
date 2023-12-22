import shutil
from datetime import datetime
import os

import json

class ProjectManager():
    def __init__(self, parent, workdir=None):
        self.version = '2.0'
        self.parent = parent
        self.sav_data = {}
        if workdir:
            self.workdir = workdir
        else:
            self.workdir = self.init_workdir()

        if not os.path.exists(self.workdir):
            os.makedirs(self.workdir)

    def init_workdir(self):
        curr_dir = os.getcwd()
        sav_dir = os.path.join(curr_dir, 'sav', datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        return sav_dir

    def sav_data_init(self):
        sav_data = {
            'info': {'version': self.version},
            'acquisition': {},
            'offline': {'hasVideo': False, 'roi_data': []},
            'online': {'roi_data': []},
        }
        return sav_data

    def setWorkDir(self, path):
        self.workdir = path

    def getWorkDir(self):
        return self.workdir

    def get_offDir(self):
        return os.path.join(self.workdir, 'offline')

    def project_save(self, off_video_path=None, roi_table=None, on_roi_table=None):
        self.sav_data = self.sav_data_init()

        self.acq_tab_saving()
        self.offline_tab_saving(off_video_path, roi_table)
        self.online_tab_saving(on_roi_table)

        fn = os.path.join(self.workdir, 'metadata.obmiproject')
        with open(fn, 'w') as f:
            json.dump(self.sav_data, f, indent=2)

        print('Project Saved')


    def acq_tab_saving(self):
        self.sav_data['acquisition']['cam_config'] = self.parent.getAcqCamConfigs()

    def offline_tab_saving(self, off_video_path, roi_table):
        if off_video_path is not None:
            self.sav_data['offline']['hasVideo'] = True

            target_dir = self.get_offDir()
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            target_path = os.path.join(target_dir, 'video.avi')
            if os.path.exists(target_path):
                if not os.path.samefile(off_video_path, target_path):
                    shutil.copy(off_video_path, target_path)
            else:
                shutil.copy(off_video_path, target_path)
            self.sav_data['offline']['video'] = target_path  # can remove

        if roi_table is not None:
            size = roi_table.size()
            if size > 0:
                roi_dict_list = []
                roi_list = roi_table.itemlist
                for roi in roi_list:
                    roi_dict_list.append(roi.to_dict())
                self.sav_data['offline']['roi_data'] = roi_dict_list

    def online_tab_saving(self, on_roi_table):
        if on_roi_table is not None:
            size = on_roi_table.size()
            if size > 0:
                roi_dict_list = []
                roi_list = on_roi_table.itemlist
                for roi in roi_list:
                    roi_dict_list.append(roi.to_dict())
                self.sav_data['online']['roi_data'] = roi_dict_list

        self.sav_data['online']['cam_config'] = self.parent.getOnCamConfigs()

    def project_load(self, f):
        self.acq_tab_loading(f['acquisition'])
        self.offline_tab_loading(f['offline'])
        self.online_tab_loading(f['online'])

        print('Project Loaded')

    def acq_tab_loading(self, js):
        config = js['cam_config']
        self.parent.setAcqCamConfigs(config)

    def offline_tab_loading(self, js):
        if js['hasVideo']:
            if self.parent.player2 is not None:
                self.parent.player2.stop()

            self.parent.open_video_path = js['video']
            self.parent.startPlayer2()

        if len(js['roi_data']) > 0:
            self.parent.deleteRoi(all=True)
            roi_dicts = js['roi_data']
            for roi_dict in roi_dicts:
                self.parent.create_roi_from_dict(roi_dict)

    def online_tab_loading(self, js):
        config = js['cam_config']
        self.parent.setOnCamConfigs(config)

        if len(js['roi_data']) > 0:
            self.parent.deleteOnRoi(all=True)
            roi_dicts = js['roi_data']
            for roi_dict in roi_dicts:
                self.parent.create_on_roi_from_dict(roi_dict)

