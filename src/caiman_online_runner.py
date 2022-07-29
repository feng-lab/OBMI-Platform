import logging
from datetime import time

import caiman
import cv2
import numpy as np
from caiman.source_extraction import cnmf as cnmf

## Helper class for running online CNMF pipeline
from numpy import hstack
from typing import List, Tuple
from scipy.sparse import csc_matrix, coo_matrix


class OnlineRunner():
    def __init__(self, cnmf):
        self.cnmf = cnmf
        self.model_LN = None
        self.epochs = 1
        self.t = 0

    def frame_process(self, frame):
        # Iterate through the epochs
        epochs = self.epochs
        model_LN = self.model_LN

        logging.info(f"Searching for new components set to: {self.cnmf.params.get('online', 'update_num_comps')}")

        old_comps = self.cnmf.N  # number of existing components
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

    # replace original fit_online in online_cnmf.py
    def fit_online(self, **kwargs):

        fls = self.cnmf.params.get('data', 'fnames')
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

            ## TODO: 替换
            Y = caiman.base.movies.load(fls[0], subindices=slice(init_batch),
                                        var_name_hdf5=self.cnmf.params.get('data', 'var_name_hdf5'))
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
        self.cnmf.initialize_online(model_LN=model_LN)




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
        #     dims = frame.shape
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
        # self.cnmf.t_online = t_online
        # self.cnmf.estimates.C_on = self.cnmf.estimates.C_on[:self.cnmf.M]
        # self.cnmf.estimates.noisyC = self.cnmf.estimates.noisyC[:self.cnmf.M]

        return self
