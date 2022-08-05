#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Basic demo for the CaImAn Online algorithm (OnACID) using CNMF initialization.
It demonstrates the construction of the params and online_cnmf objects and
the fit function that is used to run the algorithm.
For a more complete demo check the script demo_OnACID_mesoscope.py

@author: jfriedrich & epnev
"""

import logging

import caiman
import numpy as np
import os

import caiman as cm
from caiman.source_extraction import cnmf as cnmf
from caiman.paths import caiman_datadir
from PySide2 import QtCore
from caiman.utils.visualization import get_contours

from src.caiman_online_runner import OnlineRunner


class Caiman_OnACID(QtCore.QThread):
    #%%
    # Set up the logger; change this if you like.
    # You can log to a file using the filename parameter, or make the output more or less
    # verbose by setting level to logging.DEBUG, logging.INFO, logging.WARNING, or logging.ERROR
    roi_pos = QtCore.Signal(list)

    def __init__(self, parent: QtCore.QObject, param_list, path=""):
        super().__init__(parent=parent)
        logging.basicConfig(format=
                            "%(relativeCreated)12d [%(filename)s:%(funcName)20s():%(lineno)s]"\
                            "[%(process)d] %(message)s",
                            level=logging.WARNING)
        # filename="/tmp/caiman.log"
        # %% set up some parameters
        # self.path = path
        # self.fps = fps

        # self.fr = 10  # frame rate (Hz)
        self.fr = param_list[0]
        self.decay_time = param_list[1]  # approximate length of transient event in seconds
        self.gSig = param_list[2]  # expected half size of neurons
        self.p = param_list[3]  # order of AR indicator dynamics
        self.min_SNR = param_list[4]  # minimum SNR for accepting candidate components
        self.thresh_CNN_noisy = param_list[5]  # CNN threshold for candidate components
        self.gnb = param_list[6]  # number of background components
        self.init_method = param_list[7]  # initialization method

        # set up CNMF initialization parameters

        self.init_batch = param_list[8]  # number of frames for initialization
        self.patch_size = param_list[9]  # size of patch
        self.stride = param_list[10]  # amount of overlap between patches
        self.K = param_list[11]  # max number of components in each patch

    def start_pipeline(self, frames):
        pass  # For compatibility between running under Spyder and the CLI
        # fname = [os.path.join(caiman_datadir(), 'example_movies', 'demoMovie.avi')]

        # fr = 30
        # decay_time = .75  # approximate length of transient event in seconds
        # gSig = [6, 6]  # expected half size of neurons
        # p = 1  # order of AR indicator dynamics
        # min_SNR = 1  # minimum SNR for accepting candidate components
        # thresh_CNN_noisy = 0.65  # CNN threshold for candidate components
        # gnb = 2  # number of background components
        # init_method = 'cnmf'  # initialization method
        #
        # # set up CNMF initialization parameters
        #
        # init_batch = 200
        # patch_size = 32  # size of patch
        # stride = 3  # amount of overlap between patches
        # K = 4  # max number of components in each patch

        params_dict = {'fr': self.fr,
                       'decay_time': self.decay_time,
                       'gSig': self.gSig,
                       'p': self.p,
                       'min_SNR': self.min_SNR,
                       'nb': self.gnb,
                       'init_batch': self.init_batch,
                       'init_method': self.init_method,
                       'rf': self.patch_size//2,
                       'stride': self.stride,
                       'sniper_mode': True,
                       'thresh_CNN_noisy': self.thresh_CNN_noisy,
                       'K': self.K}
        opts = cnmf.params.CNMFParams(params_dict=params_dict)
    # %% fit with online object
        cnm = cnmf.online_cnmf.OnACID(params=opts)
        self.online_runner = OnlineRunner(cnm, frames)
        self.online_runner.fit_online()

    #     Cn = cm.load(fname[0], subindices=slice(0,500)).local_correlations(swap_dim=False)
    #     cnm.estimates.plot_contours(img=Cn)
    #
    #
    # # %% pass through the CNN classifier with a low threshold (keeps clearer neuron shapes and excludes processes)
    #     use_CNN = True
    #     if use_CNN:
    #         # threshold for CNN classifier
    #         opts.set('quality', {'min_cnn_thr': 0.05})
    #         cnm.estimates.evaluate_components_CNN(opts)
    #         cnm.estimates.plot_contours(img=Cn, idx=cnm.estimates.idx_components)
    # # %% plot results
    #     cnm.estimates.view_components(img=Cn, idx=cnm.estimates.idx_components)
