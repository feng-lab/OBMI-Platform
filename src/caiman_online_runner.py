import datetime
import logging
from datetime import time
import time
from multiprocessing import cpu_count

import caiman
import cv2
import numpy as np
from PySide2 import QtCore
from PySide2.QtCore import QThread, QObject
from caiman import mmapping
from caiman.motion_correction import sliding_window
from caiman.source_extraction import cnmf as cnmf

## Helper class for running online CNMF pipeline
from caiman.source_extraction.cnmf import CNMF
from caiman.source_extraction.cnmf.online_cnmf import bare_initialization, seeded_initialization
from caiman.source_extraction.cnmf.pre_processing import get_noise_fft
from caiman.source_extraction.cnmf.utilities import get_file_size
from caiman.utils.visualization import get_contours
from numpy import hstack
from typing import List, Tuple
from scipy.sparse import csc_matrix, coo_matrix

import os

class CaimanLauncher(QObject):
    def __init__(self, param_list=None, open_video_path="", mainwin=None):
        super(CaimanLauncher, self).__init__()
        # TODO: implement caiman
        self.param_list = param_list
        self.open_video_path = open_video_path
        from caiman_OnACID_batch import Caiman_OnACID_batch
        self.cm = Caiman_OnACID_batch(self, self.param_list, self.open_video_path)
        self.cm.roi_pos.connect(mainwin.addAutoOnRoi)
        print('caiman init')

    def online_batch(self):
        print('caiman start')
        self.cm.start_pipeline()

class CaimanThread(QThread):
    def __init__(self, main_thread, cnmf=None, Y=None):
        super(CaimanThread, self).__init__()
        self.caiman = CaimanFrameProcess(cnmf=cnmf, Y=Y, main_thread = main_thread)
        self.main_thread = main_thread
        self.caiman.fit_online()
        self.caiman.roi_pos.connect(main_thread.addAutoOnRoi)

    def run(self):
        self.caiman.moveToThread(self)
        self.main_thread.on_scope.frameG.connect(self.caiman.frame_input)
        self.caiman.frame_process()

class CaimanFrameProcess(QObject):
    roi_pos = QtCore.Signal(list)

    def __init__(self, cnmf=None, Y=None, main_thread=None):
        super(CaimanFrameProcess, self).__init__()
        self.cnmf = cnmf
        self.Y = Y
        self.model_LN = None
        self.epochs = 1
        self.t = 0
        self.l = []
        self.frame_count = 0
        self.frame_list = []
        self.capacity = 0
        self.frame_read_cnt = 1   # 间隔多少帧读一帧数据进行ROI处理
        self.main_thread = main_thread
        self.N = 0

    def frame_input(self, frame):
        self.frame_list.append(frame)
        self.capacity += 1

    def frame_process(self):
        while True:
            if self.capacity < self.frame_read_cnt:
                time.sleep(0.01)
                continue

            for i in range(self.frame_read_cnt):
                frame = self.frame_list.pop(0)
                self.capacity -= 1

            # Iterate through the epochs
            epochs = self.epochs
            model_LN = self.model_LN

            logging.info(f"Searching for new components set to: {self.cnmf.params.get('online', 'update_num_comps')}")

            if model_LN is not None:
                if self.cnmf.params.get('ring_CNN', 'remove_activity'):
                    activity = self.cnmf.estimates.Ab[:, :self.cnmf.N].dot(
                        self.cnmf.estimates.C_on[:self.cnmf.N, self.t - 1]).reshape(
                        self.cnmf.params.get('data', 'dims'),
                        order='F')
                    if self.cnmf.params.get('online', 'normalize'):
                        activity *= self.cnmf.img_norm
                else:
                    activity = 0.
                #                                frame = frame.astype(np.float32) - activity
                frame = frame - np.squeeze(model_LN.predict(
                    np.expand_dims(np.expand_dims(frame.astype(np.float32) - activity, 0), -1)))
                frame = np.maximum(frame, 0)

            if np.isnan(np.sum(frame)):
                raise Exception('Frame ' + ' contains NaN')

            # Downsample and normalize
            frame_ = frame.copy().astype(np.float32)
            if self.cnmf.params.get('online', 'ds_factor') > 1:
                frame_ = cv2.resize(frame_, self.cnmf.img_norm.shape[::-1])

            if self.cnmf.params.get('online', 'normalize'):
                frame_ -= self.cnmf.img_min  # make data non-negative

            # Motion Correction
            # t_mot = time()
            # if self.cnmf.params.get('online', 'motion_correct'):  # motion correct
            #     frame_cor = self.cnmf.mc_next(t, frame_)
            # else:
            #     templ = None
            #     frame_cor = frame_
            # self.cnmf.t_motion.append(time() - t_mot)

            frame_cor = frame
            if self.cnmf.params.get('online', 'normalize'):
                frame_cor = frame_cor / self.cnmf.img_norm
            # Fit next frame
            self.cnmf.fit_next(self.t, frame_cor.reshape(-1, order='F'))

            self.t += 1
            self.cnmf.Ab_epoch.append(self.cnmf.estimates.Ab.copy())
            print('success, number of ROI: ', self.cnmf.N)

            if self.cnmf.params.get('online', 'normalize'):
                Ab = csc_matrix(self.cnmf.estimates.Ab.multiply(
                    self.cnmf.img_norm.reshape(-1, order='F')[:, np.newaxis]))
            else:
                Ab = self.cnmf.estimates.Ab
            self.cnmf.estimates.A, _ = Ab[:, self.cnmf.params.get('init', 'nb'):], Ab[:, :self.cnmf.params.get('init',
                                                                                                               'nb')].toarray()
            if self.cnmf.params.get('online', 'ds_factor') > 1:
                dims = frame.shape
                self.cnmf.estimates.A = hstack(
                    [coo_matrix(
                        cv2.resize(self.cnmf.estimates.A[:, i].reshape(self.cnmf.estimates.dims, order='F').toarray(),
                                   dims[::-1]).reshape(-1, order='F')[:, None]) for i in range(self.cnmf.N)],
                    format='csc')

            if self.cnmf.N > self.N:
                dims = frame.shape
                mat = self.cnmf.estimates.A[:, self.N:]
                self.N = self.cnmf.N
                comps = get_contours(mat, dims)
                self.roi_pos.emit(comps)

    # replace original fit_online in online_cnmf.py
    def fit_online(self, **kwargs):

        init_batch = self.cnmf.params.get('online', 'init_batch')
        self.t = init_batch
        if self.cnmf.params.get('online', 'ring_CNN'):
            logging.info('Using Ring CNN model')
            from caiman.utils.nn_models import (fit_NL_model, create_LN_model, quantile_loss, rate_scheduler)
            gSig = self.cnmf.params.get('init', 'gSig')[0]
            width = self.cnmf.params.get('ring_CNN', 'width')
            nch = self.cnmf.params.get('ring_CNN', 'n_channels')
            if self.cnmf.params.get('ring_CNN', 'loss_fn') == 'pct':
                loss_fn = quantile_loss(self.cnmf.params.get('ring_CNN', 'pct'))
            else:
                loss_fn = self.cnmf.params.get('ring_CNN', 'loss_fn')
            if self.cnmf.params.get('ring_CNN', 'lr_scheduler') is None:
                sch = None
            else:
                sch = rate_scheduler(*self.cnmf.params.get('ring_CNN', 'lr_scheduler'))

            # Y = caiman.base.movies.load(fls[0], subindices=slice(init_batch),
            #                             var_name_hdf5=self.cnmf.params.get('data', 'var_name_hdf5'))
            Y = self.Y

            shape = Y.shape[1:] + (1,)
            logging.info('Starting background model training.')
            model_LN = create_LN_model(Y, shape=shape, n_channels=nch,
                                       lr=self.cnmf.params.get('ring_CNN', 'lr'), gSig=gSig,
                                       loss=loss_fn, width=width,
                                       use_add=self.cnmf.params.get('ring_CNN', 'use_add'),
                                       use_bias=self.cnmf.params.get('ring_CNN', 'use_bias'))
            if self.cnmf.params.get('ring_CNN', 'reuse_model'):
                logging.info('Using existing model from {}'.format(self.cnmf.params.get('ring_CNN', 'path_to_model')))
                model_LN.load_weights(self.cnmf.params.get('ring_CNN', 'path_to_model'))
            else:
                logging.info('Estimating model from scratch, starting training.')
                model_LN, history, path_to_model = fit_NL_model(model_LN, Y,
                                                                epochs=self.cnmf.params.get('ring_CNN', 'max_epochs'),
                                                                patience=self.cnmf.params.get('ring_CNN', 'patience'),
                                                                schedule=sch)
                logging.info('Training complete. Model saved in {}.'.format(path_to_model))
                self.cnmf.params.set('ring_CNN', {'path_to_model': path_to_model})
        else:
            model_LN = None
        self.model_LN = model_LN
        self.epochs = self.cnmf.params.get('online', 'epochs')
        self.initialize_online(model_LN=model_LN)
        self.cnmf.Ab_epoch: List = []



        # t = self.t
        # epochs = 1
        # if self.cnmf.params.get('online', 'normalize'):
        #     self.cnmf.estimates.Ab = csc_matrix(self.cnmf.estimates.Ab.multiply(
        #         self.cnmf.img_norm.reshape(-1, order='F')[:, np.newaxis]))
        # self.cnmf.estimates.A, self.cnmf.estimates.b = self.cnmf.estimates.Ab[:, self.cnmf.params.get('init', 'nb'):], self.cnmf.estimates.Ab[:,
        #                                                                                            :self.cnmf.params.get(
        #                                                                                                'init',
        #                                                                                                'nb')].toarray()
        # self.cnmf.estimates.C, self.cnmf.estimates.f = self.cnmf.estimates.C_on[self.cnmf.params.get('init', 'nb'):self.cnmf.M, t - t //
        #                                                                                                epochs:t], self.cnmf.estimates.C_on[
        #                                                                                                           :self.cnmf.params.get(
        #                                                                                                               'init',
        #                                                                                                               'nb'),
        #                                                                                                           t - t // epochs:t]
        # noisyC = self.cnmf.estimates.noisyC[self.cnmf.params.get('init', 'nb'):self.cnmf.M, t - t // epochs:t]
        # self.cnmf.estimates.YrA = noisyC - self.cnmf.estimates.C
        # if self.cnmf.estimates.OASISinstances is not None:
        #     self.cnmf.estimates.bl = [osi.b for osi in self.cnmf.estimates.OASISinstances]
        #     self.cnmf.estimates.S = np.stack([osi.s for osi in self.cnmf.estimates.OASISinstances])
        #     self.cnmf.estimates.S = self.cnmf.estimates.S[:, t - t // epochs:t]
        # else:
        #     self.cnmf.estimates.bl = [0] * self.cnmf.estimates.C.shape[0]
        #     self.cnmf.estimates.S = np.zeros_like(self.cnmf.estimates.C)
        # if self.cnmf.params.get('online', 'ds_factor') > 1:
        #     dims = Y.shape[1:]
        #     self.cnmf.estimates.A = hstack(
        #         [coo_matrix(cv2.resize(self.cnmf.estimates.A[:, i].reshape(self.cnmf.estimates.dims, order='F').toarray(),
        #                                dims[::-1]).reshape(-1, order='F')[:, None]) for i in range(self.cnmf.N)],
        #         format='csc')
        #     if self.cnmf.estimates.b.shape[-1] > 0:
        #         self.cnmf.estimates.b = np.concatenate(
        #             [cv2.resize(self.cnmf.estimates.b[:, i].reshape(self.cnmf.estimates.dims, order='F'),
        #                         dims[::-1]).reshape(-1, order='F')[:, None] for i in
        #              range(self.cnmf.params.get('init', 'nb'))], axis=1)
        #     else:
        #         self.cnmf.estimates.b = np.resize(self.cnmf.estimates.b, (self.cnmf.estimates.A.shape[0], 0))
        #     if self.cnmf.estimates.b0 is not None:
        #         b0 = self.cnmf.estimates.b0.reshape(self.cnmf.estimates.dims, order='F')
        #         b0 = cv2.resize(b0, dims[::-1])
        #         self.cnmf.estimates.b0 = b0.reshape((-1, 1), order='F')
        #     self.cnmf.params.set('data', {'dims': dims})
        #     self.cnmf.estimates.dims = dims
        #
        # self.cnmf.estimates.C_on = self.cnmf.estimates.C_on[:self.cnmf.M]
        # self.cnmf.estimates.noisyC = self.cnmf.estimates.noisyC[:self.cnmf.M]

        return self

    def initialize_online(self, model_LN=None, T=None):

        opts = self.cnmf.params.get_group('online')
        Y = caiman.movie(self.Y.astype(np.float32))

        if model_LN is not None:
            Y = Y - caiman.movie(np.squeeze(model_LN.predict(np.expand_dims(Y, -1))))
            Y = np.maximum(Y, 0)
        # Downsample if needed
        ds_factor = np.maximum(opts['ds_factor'], 1)
        if ds_factor > 1:
            Y = Y.resize(1./ds_factor, 1./ds_factor)
        self.cnmf.estimates.shifts = []  # store motion shifts here
        self.cnmf.estimates.time_new_comp = []
        img_min = Y.min()

        if self.cnmf.params.get('online', 'normalize'):
            Y -= img_min
        img_norm = np.std(Y, axis=0)
        img_norm += np.median(img_norm)  # normalize data to equalize the FOV
        logging.info('Frame size:' + str(img_norm.shape))
        if self.cnmf.params.get('online', 'normalize'):
            Y = Y/img_norm[None, :, :]
        if opts['show_movie']:
            self.cnmf.bnd_Y = np.percentile(Y,(0.001,100-0.001))
        _, d1, d2 = Y.shape
        Yr = Y.to_2D().T        # convert data into 2D array
        self.cnmf.img_min = img_min
        self.cnmf.img_norm = img_norm
        if self.cnmf.params.get('online', 'init_method') == 'bare':
            init = self.cnmf.params.get_group('init').copy()
            is1p = (init['method_init'] == 'corr_pnr' and  init['ring_size_factor'] is not None)
            if is1p:
                self.cnmf.estimates.sn, psx = get_noise_fft(
                    Yr, noise_range=self.cnmf.params.get('preprocess', 'noise_range'),
                    noise_method=self.cnmf.params.get('preprocess', 'noise_method'),
                    max_num_samples_fft=self.cnmf.params.get('preprocess', 'max_num_samples_fft'))
            for key in ('K', 'nb', 'gSig', 'method_init'):
                init.pop(key, None)
            tmp = bare_initialization(
                Y.transpose(1, 2, 0), init_batch=self.cnmf.params.get('online', 'init_batch'),
                k=self.cnmf.params.get('init', 'K'), gnb=self.cnmf.params.get('init', 'nb'),
                method_init=self.cnmf.params.get('init', 'method_init'), sn=self.cnmf.estimates.sn,
                gSig=self.cnmf.params.get('init', 'gSig'), return_object=False,
                options_total=self.cnmf.params.to_dict(), **init)
            if is1p:
                (self.cnmf.estimates.A, self.cnmf.estimates.b, self.cnmf.estimates.C, self.cnmf.estimates.f,
                 self.cnmf.estimates.YrA, self.cnmf.estimates.W, self.cnmf.estimates.b0) = tmp
            else:
                (self.cnmf.estimates.A, self.cnmf.estimates.b, self.cnmf.estimates.C, self.cnmf.estimates.f,
                 self.cnmf.estimates.YrA) = tmp
            self.cnmf.estimates.S = np.zeros_like(self.cnmf.estimates.C)
            nr = self.cnmf.estimates.C.shape[0]
            self.cnmf.estimates.g = np.array([-np.poly([0.9] * max(self.cnmf.params.get('preprocess', 'p'), 1))[1:]
                               for gg in np.ones(nr)])
            self.cnmf.estimates.bl = np.zeros(nr)
            self.cnmf.estimates.c1 = np.zeros(nr)
            self.cnmf.estimates.neurons_sn = np.std(self.cnmf.estimates.YrA, axis=-1)
            self.cnmf.estimates.lam = np.zeros(nr)
        elif self.cnmf.params.get('online', 'init_method') == 'cnmf':
            n_processes = cpu_count() - 1 or 1
            cnm = CNMF(n_processes=n_processes, params=self.cnmf.params, dview=self.cnmf.dview)
            cnm.estimates.shifts = self.cnmf.estimates.shifts
            if self.cnmf.params.get('patch', 'rf') is None:
                cnm.dview = None
                cnm.fit(np.array(Y))
                self.cnmf.estimates = cnm.estimates

            else:
                Y.save(caiman.paths.fn_relocated('init_file.hdf5'))
                f_new = mmapping.save_memmap(['init_file.hdf5'], base_name='Yr', order='C',
                                             slices=[slice(0, opts['init_batch']), None, None])

                Yrm, dims_, T_ = mmapping.load_memmap(f_new)
                Y = np.reshape(Yrm.T, [T_] + list(dims_), order='F')
                cnm.fit(Y)
                self.cnmf.estimates = cnm.estimates
                if self.cnmf.params.get('online', 'normalize'):
                    self.cnmf.estimates.A /= self.cnmf.img_norm.reshape(-1, order='F')[:, np.newaxis]
                    self.cnmf.estimates.b /= self.cnmf.img_norm.reshape(-1, order='F')[:, np.newaxis]
                    self.cnmf.estimates.A = csc_matrix(self.cnmf.estimates.A)

        elif self.cnmf.params.get('online', 'init_method') == 'seeded':
            self.cnmf.estimates.A, self.cnmf.estimates.b, self.cnmf.estimates.C, self.cnmf.estimates.f, self.cnmf.estimates.YrA = seeded_initialization(
                    Y.transpose(1, 2, 0), self.cnmf.estimates.A, gnb=self.cnmf.params.get('init', 'nb'), k=self.cnmf.params.get('init', 'K'),
                    gSig=self.cnmf.params.get('init', 'gSig'), return_object=False)
            self.cnmf.estimates.S = np.zeros_like(self.cnmf.estimates.C)
            nr = self.cnmf.estimates.C.shape[0]
            self.cnmf.estimates.g = np.array([-np.poly([0.9] * max(self.cnmf.params.get('preprocess', 'p'), 1))[1:]
                               for gg in np.ones(nr)])
            self.cnmf.estimates.bl = np.zeros(nr)
            self.cnmf.estimates.c1 = np.zeros(nr)
            self.cnmf.estimates.neurons_sn = np.std(self.cnmf.estimates.YrA, axis=-1)
            self.cnmf.estimates.lam = np.zeros(nr)
        else:
            raise Exception('Unknown initialization method!')
        dims = Y.shape[1:]
        self.cnmf.params.set('data', {'dims': dims})
        # Todo: frame size: 200000, enlarge it when needed
        T1 = 200000 * self.cnmf.params.get('online', 'epochs') if T is None else T
        self.cnmf._prepare_object(Yr, T1)

        return self

class OnlineRunner():
    def __init__(self, cnmf=None, Y=None, parent=None, param_list=None):
        self.cnmf = cnmf
        self.Y = Y
        self.model_LN = None
        self.epochs = 1
        self.t = 0
        self.l = []
        self.parent = parent
        self.frame_count = 0
        self.file_size = 0
        self.param_list = param_list

    def tempFile(self, fps, width, height, size):
        self.path = os.path.abspath('.') + '\\' + 'temp.avi'
        self.file = cv2.VideoWriter(self.path, cv2.VideoWriter_fourcc('M','J','P','G'), fps, (width, height), True)
        self.file_size = size
        self.parent.on_scope.frameG.connect(self.frame_to_file)


    def frame_to_file(self, frame):
        print('get frame: ', self.frame_count)
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        self.file.write(frame)
        self.frame_count += 1
        if self.file_size == self.frame_count:
            self.parent.on_scope.frameG.disconnect(self.frame_to_file)
            self.file.release()
            print('saved file: ', self.path)
            self.thread = QThread()
            self.launcher = CaimanLauncher(self.param_list, self.path, self.parent)
            self.launcher.moveToThread(self.thread)
            self.thread.started.connect(self.launcher.online_batch)
            self.thread.start()
            self.parent.online_scope()
            return

    def frame_process(self, frame):
        # Iterate through the epochs
        epochs = self.epochs
        model_LN = self.model_LN

        logging.info(f"Searching for new components set to: {self.cnmf.params.get('online', 'update_num_comps')}")

        if model_LN is not None:
            if self.cnmf.params.get('ring_CNN', 'remove_activity'):
                activity = self.cnmf.estimates.Ab[:, :self.cnmf.N].dot(
                    self.cnmf.estimates.C_on[:self.cnmf.N, self.t - 1]).reshape(self.cnmf.params.get('data', 'dims'),
                                                                 order='F')
                if self.cnmf.params.get('online', 'normalize'):
                    activity *= self.cnmf.img_norm
            else:
                activity = 0.
            #                                frame = frame.astype(np.float32) - activity
            frame = frame - np.squeeze(model_LN.predict(
                np.expand_dims(np.expand_dims(frame.astype(np.float32) - activity, 0), -1)))
            frame = np.maximum(frame, 0)

        if np.isnan(np.sum(frame)):
            raise Exception('Frame '+' contains NaN')

        # Downsample and normalize
        frame_ = frame.copy().astype(np.float32)
        if self.cnmf.params.get('online', 'ds_factor') > 1:
            frame_ = cv2.resize(frame_, self.cnmf.img_norm.shape[::-1])

        if self.cnmf.params.get('online', 'normalize'):
            frame_ -= self.cnmf.img_min  # make data non-negative

        # Motion Correction
        # t_mot = time()
        # if self.cnmf.params.get('online', 'motion_correct'):  # motion correct
        #     frame_cor = self.cnmf.mc_next(t, frame_)
        # else:
        #     templ = None
        #     frame_cor = frame_
        # self.cnmf.t_motion.append(time() - t_mot)

        frame_cor = frame
        if self.cnmf.params.get('online', 'normalize'):
            frame_cor = frame_cor / self.cnmf.img_norm
        # Fit next frame
        self.cnmf.fit_next(self.t, frame_cor.reshape(-1, order='F'))

        self.t += 1
        self.cnmf.Ab_epoch.append(self.cnmf.estimates.Ab.copy())
        print('success, number of ROI: ', self.cnmf.N)

        if self.cnmf.params.get('online', 'normalize'):
            Ab = csc_matrix(self.cnmf.estimates.Ab.multiply(
                self.cnmf.img_norm.reshape(-1, order='F')[:, np.newaxis]))
        else:
            Ab = self.cnmf.estimates.Ab
        self.cnmf.estimates.A, _ = Ab[:, self.cnmf.params.get('init', 'nb'):], Ab[:, :self.cnmf.params.get('init', 'nb')].toarray()
        if self.cnmf.params.get('online', 'ds_factor') > 1:
            dims = frame.shape
            self.cnmf.estimates.A = hstack(
                [coo_matrix(cv2.resize(self.cnmf.estimates.A[:, i].reshape(self.cnmf.estimates.dims, order='F').toarray(),
                                       dims[::-1]).reshape(-1, order='F')[:, None]) for i in range(self.cnmf.N)],
                format='csc')


    # replace original fit_online in online_cnmf.py
    def fit_online(self, **kwargs):

        init_batch = self.cnmf.params.get('online', 'init_batch')
        self.t = init_batch
        if self.cnmf.params.get('online', 'ring_CNN'):
            logging.info('Using Ring CNN model')
            from caiman.utils.nn_models import (fit_NL_model, create_LN_model, quantile_loss, rate_scheduler)
            gSig = self.cnmf.params.get('init', 'gSig')[0]
            width = self.cnmf.params.get('ring_CNN', 'width')
            nch = self.cnmf.params.get('ring_CNN', 'n_channels')
            if self.cnmf.params.get('ring_CNN', 'loss_fn') == 'pct':
                loss_fn = quantile_loss(self.cnmf.params.get('ring_CNN', 'pct'))
            else:
                loss_fn = self.cnmf.params.get('ring_CNN', 'loss_fn')
            if self.cnmf.params.get('ring_CNN', 'lr_scheduler') is None:
                sch = None
            else:
                sch = rate_scheduler(*self.cnmf.params.get('ring_CNN', 'lr_scheduler'))

            # Y = caiman.base.movies.load(fls[0], subindices=slice(init_batch),
            #                             var_name_hdf5=self.cnmf.params.get('data', 'var_name_hdf5'))
            Y = self.Y

            shape = Y.shape[1:] + (1,)
            logging.info('Starting background model training.')
            model_LN = create_LN_model(Y, shape=shape, n_channels=nch,
                                       lr=self.cnmf.params.get('ring_CNN', 'lr'), gSig=gSig,
                                       loss=loss_fn, width=width,
                                       use_add=self.cnmf.params.get('ring_CNN', 'use_add'),
                                       use_bias=self.cnmf.params.get('ring_CNN', 'use_bias'))
            if self.cnmf.params.get('ring_CNN', 'reuse_model'):
                logging.info('Using existing model from {}'.format(self.cnmf.params.get('ring_CNN', 'path_to_model')))
                model_LN.load_weights(self.cnmf.params.get('ring_CNN', 'path_to_model'))
            else:
                logging.info('Estimating model from scratch, starting training.')
                model_LN, history, path_to_model = fit_NL_model(model_LN, Y,
                                                                epochs=self.cnmf.params.get('ring_CNN', 'max_epochs'),
                                                                patience=self.cnmf.params.get('ring_CNN', 'patience'),
                                                                schedule=sch)
                logging.info('Training complete. Model saved in {}.'.format(path_to_model))
                self.cnmf.params.set('ring_CNN', {'path_to_model': path_to_model})
        else:
            model_LN = None
        self.model_LN = model_LN
        self.epochs = self.cnmf.params.get('online', 'epochs')
        self.initialize_online(model_LN=model_LN)
        self.cnmf.Ab_epoch: List = []



        # t = self.t
        # epochs = 1
        # if self.cnmf.params.get('online', 'normalize'):
        #     self.cnmf.estimates.Ab = csc_matrix(self.cnmf.estimates.Ab.multiply(
        #         self.cnmf.img_norm.reshape(-1, order='F')[:, np.newaxis]))
        # self.cnmf.estimates.A, self.cnmf.estimates.b = self.cnmf.estimates.Ab[:, self.cnmf.params.get('init', 'nb'):], self.cnmf.estimates.Ab[:,
        #                                                                                            :self.cnmf.params.get(
        #                                                                                                'init',
        #                                                                                                'nb')].toarray()
        # self.cnmf.estimates.C, self.cnmf.estimates.f = self.cnmf.estimates.C_on[self.cnmf.params.get('init', 'nb'):self.cnmf.M, t - t //
        #                                                                                                epochs:t], self.cnmf.estimates.C_on[
        #                                                                                                           :self.cnmf.params.get(
        #                                                                                                               'init',
        #                                                                                                               'nb'),
        #                                                                                                           t - t // epochs:t]
        # noisyC = self.cnmf.estimates.noisyC[self.cnmf.params.get('init', 'nb'):self.cnmf.M, t - t // epochs:t]
        # self.cnmf.estimates.YrA = noisyC - self.cnmf.estimates.C
        # if self.cnmf.estimates.OASISinstances is not None:
        #     self.cnmf.estimates.bl = [osi.b for osi in self.cnmf.estimates.OASISinstances]
        #     self.cnmf.estimates.S = np.stack([osi.s for osi in self.cnmf.estimates.OASISinstances])
        #     self.cnmf.estimates.S = self.cnmf.estimates.S[:, t - t // epochs:t]
        # else:
        #     self.cnmf.estimates.bl = [0] * self.cnmf.estimates.C.shape[0]
        #     self.cnmf.estimates.S = np.zeros_like(self.cnmf.estimates.C)
        # if self.cnmf.params.get('online', 'ds_factor') > 1:
        #     dims = Y.shape[1:]
        #     self.cnmf.estimates.A = hstack(
        #         [coo_matrix(cv2.resize(self.cnmf.estimates.A[:, i].reshape(self.cnmf.estimates.dims, order='F').toarray(),
        #                                dims[::-1]).reshape(-1, order='F')[:, None]) for i in range(self.cnmf.N)],
        #         format='csc')
        #     if self.cnmf.estimates.b.shape[-1] > 0:
        #         self.cnmf.estimates.b = np.concatenate(
        #             [cv2.resize(self.cnmf.estimates.b[:, i].reshape(self.cnmf.estimates.dims, order='F'),
        #                         dims[::-1]).reshape(-1, order='F')[:, None] for i in
        #              range(self.cnmf.params.get('init', 'nb'))], axis=1)
        #     else:
        #         self.cnmf.estimates.b = np.resize(self.cnmf.estimates.b, (self.cnmf.estimates.A.shape[0], 0))
        #     if self.cnmf.estimates.b0 is not None:
        #         b0 = self.cnmf.estimates.b0.reshape(self.cnmf.estimates.dims, order='F')
        #         b0 = cv2.resize(b0, dims[::-1])
        #         self.cnmf.estimates.b0 = b0.reshape((-1, 1), order='F')
        #     self.cnmf.params.set('data', {'dims': dims})
        #     self.cnmf.estimates.dims = dims
        #
        # self.cnmf.estimates.C_on = self.cnmf.estimates.C_on[:self.cnmf.M]
        # self.cnmf.estimates.noisyC = self.cnmf.estimates.noisyC[:self.cnmf.M]

        return self

    def initialize_online(self, model_LN=None, T=None):

        opts = self.cnmf.params.get_group('online')
        Y = caiman.movie(self.Y.astype(np.float32))

        if model_LN is not None:
            Y = Y - caiman.movie(np.squeeze(model_LN.predict(np.expand_dims(Y, -1))))
            Y = np.maximum(Y, 0)
        # Downsample if needed
        ds_factor = np.maximum(opts['ds_factor'], 1)
        if ds_factor > 1:
            Y = Y.resize(1./ds_factor, 1./ds_factor)
        self.cnmf.estimates.shifts = []  # store motion shifts here
        self.cnmf.estimates.time_new_comp = []
        img_min = Y.min()

        if self.cnmf.params.get('online', 'normalize'):
            Y -= img_min
        img_norm = np.std(Y, axis=0)
        img_norm += np.median(img_norm)  # normalize data to equalize the FOV
        logging.info('Frame size:' + str(img_norm.shape))
        if self.cnmf.params.get('online', 'normalize'):
            Y = Y/img_norm[None, :, :]
        if opts['show_movie']:
            self.cnmf.bnd_Y = np.percentile(Y,(0.001,100-0.001))
        _, d1, d2 = Y.shape
        Yr = Y.to_2D().T        # convert data into 2D array
        self.cnmf.img_min = img_min
        self.cnmf.img_norm = img_norm
        if self.cnmf.params.get('online', 'init_method') == 'bare':
            init = self.cnmf.params.get_group('init').copy()
            is1p = (init['method_init'] == 'corr_pnr' and  init['ring_size_factor'] is not None)
            if is1p:
                self.cnmf.estimates.sn, psx = get_noise_fft(
                    Yr, noise_range=self.cnmf.params.get('preprocess', 'noise_range'),
                    noise_method=self.cnmf.params.get('preprocess', 'noise_method'),
                    max_num_samples_fft=self.cnmf.params.get('preprocess', 'max_num_samples_fft'))
            for key in ('K', 'nb', 'gSig', 'method_init'):
                init.pop(key, None)
            tmp = bare_initialization(
                Y.transpose(1, 2, 0), init_batch=self.cnmf.params.get('online', 'init_batch'),
                k=self.cnmf.params.get('init', 'K'), gnb=self.cnmf.params.get('init', 'nb'),
                method_init=self.cnmf.params.get('init', 'method_init'), sn=self.cnmf.estimates.sn,
                gSig=self.cnmf.params.get('init', 'gSig'), return_object=False,
                options_total=self.cnmf.params.to_dict(), **init)
            if is1p:
                (self.cnmf.estimates.A, self.cnmf.estimates.b, self.cnmf.estimates.C, self.cnmf.estimates.f,
                 self.cnmf.estimates.YrA, self.cnmf.estimates.W, self.cnmf.estimates.b0) = tmp
            else:
                (self.cnmf.estimates.A, self.cnmf.estimates.b, self.cnmf.estimates.C, self.cnmf.estimates.f,
                 self.cnmf.estimates.YrA) = tmp
            self.cnmf.estimates.S = np.zeros_like(self.cnmf.estimates.C)
            nr = self.cnmf.estimates.C.shape[0]
            self.cnmf.estimates.g = np.array([-np.poly([0.9] * max(self.cnmf.params.get('preprocess', 'p'), 1))[1:]
                               for gg in np.ones(nr)])
            self.cnmf.estimates.bl = np.zeros(nr)
            self.cnmf.estimates.c1 = np.zeros(nr)
            self.cnmf.estimates.neurons_sn = np.std(self.cnmf.estimates.YrA, axis=-1)
            self.cnmf.estimates.lam = np.zeros(nr)
        elif self.cnmf.params.get('online', 'init_method') == 'cnmf':
            n_processes = cpu_count() - 1 or 1
            cnm = CNMF(n_processes=n_processes, params=self.cnmf.params, dview=self.cnmf.dview)
            cnm.estimates.shifts = self.cnmf.estimates.shifts
            if self.cnmf.params.get('patch', 'rf') is None:
                cnm.dview = None
                cnm.fit(np.array(Y))
                self.cnmf.estimates = cnm.estimates

            else:
                Y.save(caiman.paths.fn_relocated('init_file.hdf5'))
                f_new = mmapping.save_memmap(['init_file.hdf5'], base_name='Yr', order='C',
                                             slices=[slice(0, opts['init_batch']), None, None])

                Yrm, dims_, T_ = mmapping.load_memmap(f_new)
                Y = np.reshape(Yrm.T, [T_] + list(dims_), order='F')
                cnm.fit(Y)
                self.cnmf.estimates = cnm.estimates
                if self.cnmf.params.get('online', 'normalize'):
                    self.cnmf.estimates.A /= self.cnmf.img_norm.reshape(-1, order='F')[:, np.newaxis]
                    self.cnmf.estimates.b /= self.cnmf.img_norm.reshape(-1, order='F')[:, np.newaxis]
                    self.cnmf.estimates.A = csc_matrix(self.cnmf.estimates.A)

        elif self.cnmf.params.get('online', 'init_method') == 'seeded':
            self.cnmf.estimates.A, self.cnmf.estimates.b, self.cnmf.estimates.C, self.cnmf.estimates.f, self.cnmf.estimates.YrA = seeded_initialization(
                    Y.transpose(1, 2, 0), self.cnmf.estimates.A, gnb=self.cnmf.params.get('init', 'nb'), k=self.cnmf.params.get('init', 'K'),
                    gSig=self.cnmf.params.get('init', 'gSig'), return_object=False)
            self.cnmf.estimates.S = np.zeros_like(self.cnmf.estimates.C)
            nr = self.cnmf.estimates.C.shape[0]
            self.cnmf.estimates.g = np.array([-np.poly([0.9] * max(self.cnmf.params.get('preprocess', 'p'), 1))[1:]
                               for gg in np.ones(nr)])
            self.cnmf.estimates.bl = np.zeros(nr)
            self.cnmf.estimates.c1 = np.zeros(nr)
            self.cnmf.estimates.neurons_sn = np.std(self.cnmf.estimates.YrA, axis=-1)
            self.cnmf.estimates.lam = np.zeros(nr)
        else:
            raise Exception('Unknown initialization method!')
        dims = Y.shape[1:]
        self.cnmf.params.set('data', {'dims': dims})
        # Todo: frame size: 200000, enlarge it when needed
        T1 = 200000 * self.cnmf.params.get('online', 'epochs') if T is None else T
        self.cnmf._prepare_object(Yr, T1)

        return self