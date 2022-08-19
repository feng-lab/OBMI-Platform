#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Complete pipeline for online processing using CaImAn Online (OnACID).
The demo demonstates the analysis of a sequence of files using the CaImAn online
algorithm. The steps include i) motion correction, ii) tracking current 
components, iii) detecting new components, iv) updating of spatial footprints.
The script demonstrates how to construct and use the params and online_cnmf
objects required for the analysis, and presents the various parameters that
can be passed as options. A plot of the processing time for the various steps
of the algorithm is also included.
@author: Eftychios Pnevmatikakis @epnev
Special thanks to Andreas Tolias and his lab at Baylor College of Medicine
for sharing the data used in this demo.
"""

import glob
import numpy as np
import os
import logging
import matplotlib.pyplot as plt
import cv2

import caiman as cm
from caiman.paths import caiman_datadir
from caiman.source_extraction import cnmf as cnmf
from caiman.utils.utils import download_demo
from PySide2 import QtCore
from caiman.utils.visualization import get_contours

from src.caiman_online_runner import OnlineRunner


class Caiman_OnACID_batch(QtCore.QThread):
    roi_pos = QtCore.Signal(list)

    def __init__(self, parent: QtCore.QObject, param_list, path=""):
        super().__init__(parent=parent)
        logging.basicConfig(format=
                            "%(relativeCreated)12d [%(filename)s:%(funcName)20s():%(lineno)s]" \
                            "[%(process)d] %(message)s",
                            level=logging.INFO)
        self.path = path
        self.fr = param_list[0]  # frame rate (Hz)
        self.decay_time = param_list[1]  # approximate length of transient event in seconds
        self.gSig = param_list[2]  # expected half size of neurons
        self.p = param_list[3]  # order of AR indicator dynamics
        self.min_SNR = param_list[4]  # minimum SNR for accepting new components
        self.ds_factor = param_list[5]  # spatial downsampling factor (increases speed but may lose some fine structure)
        self.gnb = param_list[6]  # number of background components
        self.gSig = tuple(np.ceil(np.array(self.gSig)/self.ds_factor).astype('int'))  # recompute gSig if downsampling is involved
        self.mot_corr = param_list[7]  # flag for online motion correction
        self.pw_rigid = param_list[8]  # flag for pw-rigid motion correction (slower but potentially more accurate)
        self.max_shifts_online = np.ceil(10.).astype('int')  # maximum allowed shift during motion correction
        self.sniper_mode = param_list[9]  # use a CNN to detect new neurons (o/w space correlation)
        self.rval_thr = param_list[10]  # soace correlation threshold for candidate components
        # set up some additional supporting parameters needed for the algorithm
        # (these are default values but can change depending on dataset properties)
        self.init_batch = param_list[11]  # number of frames for initialization (presumably from the first file)
        self.K = param_list[12]  # initial number of components
        self.epochs = param_list[13]  # number of passes over the data
        self.show_movie = param_list[14]  # show the movie as the data gets processed

        self.online_runner = None

    def start_pipeline(self):
        pass # For compatibility between running under Spyder and the CLI

        # fnames = [os.path.join(caiman_datadir(), 'example_movies', 'demoMovie.avi')]
        # fnames = [os.path.join(caiman_datadir(), 'example_movies', 'msCam1.avi')]
        # fnames = [os.path.join(caiman_datadir(), 'example_movies', 'CaImAn_demo.mp4')]
        # fnames = [os.path.join(caiman_datadir(), 'example_movies', 'data_endoscope.avi')]



        # your list of files should look something like this
        #logging.info(fnames)

        # %%   Set up some parameters
        # fr = 15  # frame rate (Hz)
        # decay_time = 0.5  # approximate length of transient event in seconds
        # gSig = (3, 3)  # expected half size of neurons
        # p = 1  # order of AR indicator dynamics
        # min_SNR = 1  # minimum SNR for accepting new components
        # ds_factor = 1  # spatial downsampling factor (increases speed but may lose some fine structure)
        # gnb = 2  # number of background components
        # gSig = tuple(np.ceil(np.array(gSig) / ds_factor).astype('int'))  # recompute gSig if downsampling is involved
        # mot_corr = True  # flag for online motion correction
        # pw_rigid = False  # flag for pw-rigid motion correction (slower but potentially more accurate)
        # max_shifts_online = np.ceil(10.).astype('int')  # maximum allowed shift during motion correction
        # sniper_mode = True  # use a CNN to detect new neurons (o/w space correlation)
        # rval_thr = 0.9  # soace correlation threshold for candidate components
        # # set up some additional supporting parameters needed for the algorithm
        # # (these are default values but can change depending on dataset properties)
        # init_batch = 200  # number of frames for initialization (presumably from the first file)
        # K = 2  # initial number of components
        # epochs = 1  # number of passes over the data
        # show_movie = False  # show the movie as the data gets processed

        # params_dict = {
        #                'fr': self.fr,
        #                'decay_time': self.decay_time,
        #                'gSig': self.gSig,
        #                'p': self.p,
        #                'min_SNR': self.min_SNR,
        #                'rval_thr': self.rval_thr,
        #                'ds_factor': self.ds_factor,
        #                'nb': self.gnb,
        #                'motion_correct': self.mot_corr,
        #                'init_batch': self.init_batch,
        #                'init_method': 'bare',
        #                'normalize': True,
        #                'sniper_mode': False,
        #                'K': self.K,
        #                'epochs': self.epochs,
        #                'max_shifts_online': self.max_shifts_online,
        #                'pw_rigid': self.pw_rigid,
        #                'dist_shape_update': True,
        #                'min_num_trial': 10,
        #                'show_movie': self.show_movie,
        #                 'border_pix': 50}
        # opts = cnmf.params.CNMFParams(params_dict=params_dict)

        # *************************************direct-avi-from-scope, still-need-mmap***********************************
        # fnames = [self.path]
        # init_batch = 500
        # fr = 30
        # *************************************direct-avi-from-scope***********************************


        #************************************avi-to-mmap************************************
        # def get_iterator(device=0, fr=None):
        #     """
        #     device: device number (int) or filename (string) for reading from camera or file respectively
        #     fr: frame rate
        #     """
        #     if isinstance(device, int):  # capture from camera
        #         def capture_iter(device=device, fr=fr):
        #             cap = cv2.VideoCapture(device)
        #             if fr is not None:  # set frame rate
        #                 cap.set(cv2.CAP_PROP_FPS, fr)
        #             while True:
        #                 yield cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2GRAY)
        #
        #         iterator = capture_iter(device, fr)
        #     else:  # read frame by frame from file
        #         iterator = cm.base.movies.load_iter(device, var_name_hdf5='Y')
        #     return iterator
        #
        # # fnames = "C:\\Users\zhuqin\caiman_data\example_movies\data_endoscope.avi"
        # # fnames = "C:\\Users\zhuqin\caiman_data\example_movies\CaImAn_demo.avi"
        # # fnames = "C:\\Users\zhuqin\caiman_data\example_movies\\CaImAn_demo_out.avi"
        # iterator = get_iterator(fnames)
        #
        # init_batch = 500  # number of frames to use for initialization
        # fr = 30  # frame rate (Hz)
        # T = 6000
        #
        # m = cm.movie(np.array([next(iterator) for t in range(T)], dtype='float32'))
        # fnames = m.save('init.mmap', order='C')
        # print(fnames)
        # ************************************avi-to-mmap************************************

        # *************************************direct-mmap***********************************
        init_batch = 500  # number of frames to use for initialization
        fr = 10  # frame rate (Hz)
        T = 6000
        # 视频和分割的数据都转置了，为了匹配论文图片方向
        fnames = "C:\\Users\zhuqin\caiman_data\example_movies\\blood_vessel_10Hz-mat-mmap-T\init_d1_256_d2_256_d3_1_order_C_frames_6000_.mmap"
        print(fnames)
        # *************************************direct-mmap***********************************

        params_dict = {'fnames': fnames,
                       'fr': fr,
                       'method_init': 'corr_pnr',
                       'K': 500,
                       'gSig': (3, 3),
                       'gSiz': (13, 13),
                       'merge_thr': .65,
                       'p': 1,
                       'tsub': 1,
                       'ssub': 1,
                       'only_init': True,
                       'nb': 0,
                       'min_corr': .65,
                       'min_pnr': 6,
                       'normalize_init': False,
                       'ring_size_factor': 1.4,
                       'center_psf': True,
                       'ssub_B': 2,
                       'init_iter': 1,
                       's_min': -10,
                       'init_batch': init_batch,
                       'init_method': 'cnmf',
                       'batch_update_suff_stat': True,
                       'update_freq': 200,
                       'expected_comps': 600,
                       'update_num_comps': True,
                       'rval_thr': .55,
                       'thresh_fitness_raw': -130,
                       'thresh_fitness_delta': -20,
                       'min_SNR': 2.5,
                       'min_num_trial': 5,
                       'max_num_added': 5,
                       'use_corr_img': False,
                       'use_dense': False,
                       'motion_correct': True,  # flag for performing motion correction
                       'gSig_filt': (3, 3),  # size of high pass spatial filtering, used in 1p data
                       'use_cnn': False}

        opts = cnmf.params.CNMFParams(params_dict=params_dict)


        # del iterator
        c, dview, n_processes = cm.cluster.setup_cluster(backend='local', n_processes=24, single_thread=False)

        # load memory mappable file
        # fnames_mmap = "C:\\Users\zhuqin\caiman_data\example_movies\\blood_vessel_10Hz-mat-mmap\init_d1_256_d2_256_d3_1_order_C_frames_6000_.mmap"
        Yr, dims, T = cm.load_memmap(fnames)


        print('fit online')
        # %% fit online
        cnm = cnmf.online_cnmf.OnACID(dview=None, params=opts)

        # self.online_runner = OnlineRunner(cnm, frames)
        # self.online_runner.fit_online()

        #
        cnm.fit_online()
        print('process done')


        # ************************************test final result***************************************
        images = Yr.T.reshape((T,) + dims, order='F')
        cnm2 = cnm
        cnm2.estimates.A = cnm2.estimates.Ab
        cnm2.estimates.C = cnm2.estimates.C_on[:cnm2.N]
        cnm2.estimates.YrA = cnm2.estimates.noisyC[:cnm2.N] - cnm2.estimates.C

        print('cnm2.estimates.A.shape: ', cnm2.estimates.A.shape)
        print('cnm2.N:', cnm2.N)

        # %% plot contours
        cn, pnr = cm.summary_images.correlation_pnr(images[::1], gSig=3, swap_dim=False)
        cnm2.estimates.coordinates = None
        cnm2.estimates.plot_contours(img=cn, thr=.6)

        # %% view components

        min_SNR = 2  # adaptive way to set threshold on the transient size
        r_values_min = 0.85  # threshold on space consistency (if you lower more components
        #                        will be accepted, potentially with worst quality)
        cnm2.params.set('quality', {'min_SNR': min_SNR,
                                    'rval_thr': r_values_min,
                                    'use_cnn': False})
        cnm2.estimates.evaluate_components(images, cnm2.params, dview=dview)

        # use_CNN = True
        # if use_CNN:
        #     # threshold for CNN classifier
        #     opts.set('quality', {'min_cnn_thr': 0.05})
        #     cnm2.estimates.evaluate_components_CNN(opts)
        #     cnm2.estimates.plot_contours(img=cn, idx=cnm2.estimates.idx_components)

        # %% plot results
        cnm2.estimates.view_components(img=cn, idx=cnm2.estimates.idx_components)

        print(' ***** ')
        print('Number of total components: ', len(cnm2.estimates.C))
        print('Number of accepted components: ', len(cnm2.estimates.idx_components))
        print('len of idx_components:', len(cnm2.estimates.idx_components))
        cnm2.estimates.plot_contours(img=cn, idx=cnm2.estimates.idx_components)
        # ************************************test final result***************************************

        comps = get_contours(cnm.estimates.A, dims)
        cm.stop_server(dview=dview)
        self.roi_pos.emit(comps)

    # # %% plot contours (this may take time)
    #     logging.info('Number of components: ' + str(cnm.estimates.A.shape[-1]))
    #     images = cm.load(fnames)
    #     Cn = images.local_correlations(swap_dim=False, frames_per_chunk=500)
    #     # cnm.estimates.plot_contours(img=Cn, display_numbers=False)
    #
    # # %% view components
    # #     cnm.estimates.view_components(img=Cn)
    #
    # # %% plot timing performance (if a movie is generated during processing, timing
    # # will be severely over-estimated)
    #
    #     # T_motion = 1e3*np.array(cnm.t_motion)
    #     # T_detect = 1e3*np.array(cnm.t_detect)
    #     # T_shapes = 1e3*np.array(cnm.t_shapes)
    #     # T_track = 1e3*np.array(cnm.t_online) - T_motion - T_detect - T_shapes
    #     # plt.figure()
    #     # plt.stackplot(np.arange(len(T_motion)), T_motion, T_track, T_detect, T_shapes)
    #     # plt.legend(labels=['motion', 'tracking', 'detect', 'shapes'], loc=2)
    #     # plt.title('Processing time allocation')
    #     # plt.xlabel('Frame #')
    #     # plt.ylabel('Processing time [ms]')
    # #%% RUN IF YOU WANT TO VISUALIZE THE RESULTS (might take time)
    #     c, dview, n_processes = \
    #         cm.cluster.setup_cluster(backend='local', n_processes=None,
    #                                  single_thread=False)
    #     if opts.online['motion_correct']:
    #         shifts = cnm.estimates.shifts[-cnm.estimates.C.shape[-1]:]
    #         if not opts.motion['pw_rigid']:
    #             memmap_file = cm.motion_correction.apply_shift_online(images, shifts,
    #                                                         save_base_name='MC')
    #         else:
    #             mc = cm.motion_correction.MotionCorrect(fnames, dview=dview,
    #                                                     **opts.get_group('motion'))
    #
    #             mc.y_shifts_els = [[sx[0] for sx in sh] for sh in shifts]
    #             mc.x_shifts_els = [[sx[1] for sx in sh] for sh in shifts]
    #             memmap_file = mc.apply_shifts_movie(fnames, rigid_shifts=False,
    #                                                 save_memmap=True,
    #                                                 save_base_name='MC')
    #     else:  # To do: apply non-rigid shifts on the fly
    #         memmap_file = images.save(fnames[0][:-4] + 'mmap')
    #     cnm.mmap_file = memmap_file
    #     Yr, dims, T = cm.load_memmap(memmap_file)
    #
    #     images = np.reshape(Yr.T, [T] + list(dims), order='F')
    #     min_SNR = 2  # peak SNR for accepted components (if above this, acept)
    #     rval_thr = 0.85  # space correlation threshold (if above this, accept)
    #     use_cnn = True  # use the CNN classifier
    #     min_cnn_thr = 0.99  # if cnn classifier predicts below this value, reject
    #     cnn_lowest = 0.1  # neurons with cnn probability lower than this value are rejected
    #
    #     cnm.params.set('quality',   {'min_SNR': min_SNR,
    #                                 'rval_thr': rval_thr,
    #                                 'use_cnn': use_cnn,
    #                                 'min_cnn_thr': min_cnn_thr,
    #                                 'cnn_lowest': cnn_lowest})
    #
    #     cnm.estimates.evaluate_components(images, cnm.params, dview=dview)
    #     cnm.estimates.Cn = Cn
    #     # cnm.save(os.path.splitext(fnames[0])[0]+'_results.hdf5')
    #
    #     dview.terminate()
    #
    #     print(' ***** ')
    #     print('Number of total components: ', len(cnm.estimates.C))
    #     print('Number of accepted components: ', len(cnm.estimates.idx_components))


    #
    #     cnm.dims = dims
    #     display_images = True  # Set to true to show movies and images
    #     if display_images:
    #         cnm.estimates.plot_contours(img=Cn, display_numbers=False)
    #         cnm.estimates.view_components(img=Cn)
    #
    #     # print('Auto ROI processing time: ', time.time() - start_time)
    #     for i in range(len(cnm.estimates.idx_components_bad) - 1, -1, -1):
    #         comps.pop(cnm.estimates.idx_components_bad[i])
