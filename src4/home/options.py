

import os
import time
import json

class OptionFile():
    def __init__(self):

        # home
        self.project_name = None
        self.saving_location = None
        self.video_format = None
        self.record_duration = None

        self.project_dir = None

        self.load_video_path = None
        #self.trigger_ext = False
        ## self.filename = None
        self.options_list = []

    def default_project_name(self): #update to default
        t = time.localtime()
        self.project_name = f'{t.tm_year}_{t.tm_mon}_{t.tm_mday}'
        return self.project_name

    def default_saving_location(self):
        self.saving_location = ''
        return self.saving_location

    def default_video_format(self):
        self.video_format = 0 #'.avi'
        return self.video_format

    def default_record_duration(self):
        self.record_duration = "00:00"
        return self.record_duration

    def save_options(self, saving_path, options_list):  ## save updated options
        ## +load & update
        ## file rename .. X / project name based
            #file_name = 'options.json'
            #if os.path.isfile(os.path.join(saving_path, file_name)):
            #    file_name = file_name.replace('.json', '(1).json')
        with open(os.path.join(saving_path, 'options.json'), 'w') as outfile:
            json.dump(options_list, outfile)

    def save_to_json(self, saving_path): ## initial

        options_list = [] ## templace
        ##+use template file
        home_option = {'home_options': []}
        daq_option = {'daq_options': []}
        offl_option = {'offl_options': []}
        onl_option = {'onl_options': []}
        dec_option = {'dec_options': []}

        home_options = {
            'project_name': self.project_name,
            'project_dir': self.project_dir,
            'saving_location': self.saving_location,
            'video_format': self.video_format,
            'record_duration': self.record_duration,
            'load_video_path': self.load_video_path
        }

        home_option['home_options'] = home_options
        options_list.append(home_option)
        self.save_options(saving_path, options_list)
        self.options_list = options_list


        return True

        '''
        for opt_id, opt_props in opt_dict['Home'].items():
            if opt_id not in opt_id_set:
                continue
            if opt_props['ProjectName'] in opt_dict['Home']:
                options_data.append({
                    'project_name': self.project_name,
                    'saving_location': self.saving_location,
                    'video_format': self.video_format,
                    'record_duration': self.record_duration
                })
            else: ## temp
                options_data.append({
                    'project_name': self.project_name,
                    'saving_location': self.saving_location,
                    'video_format': self.video_format,
                    'record_duration': self.record_duration
                })
        '''