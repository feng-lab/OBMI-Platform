import time

from PySide2 import QtCore, QtGui
from multiprocessing import Queue


class UIUpdater(QtCore.QThread):
    frameI = QtCore.Signal(QtGui.QPixmap)

    def __init__(self, parent: QtCore.QObject):
        super().__init__(parent=parent)
        self.frame_queue = None
        self.trace_queue = None
        self.trace_count = 0
        self.fps = 60
        self.wtime = 1 / self.fps
        #todo: save data

    def set_frame_queue(self, queue: Queue):
        self.frame_queue = queue

    def set_trace_queue(self, queue: Queue):
        self.trace_queue = queue
        self.trace_count = 0

    def set_trace_viewer(self, viewer):
        self.trace_viewer = viewer

    def run(self):
        while not self.isInterruptionRequested():
            st = time.perf_counter()
            if self.frame_queue is not None and self.frame_queue.qsize() > 0:
                frame = self.frame_queue.get()
                height, width, dim = frame.shape
                bytesPerLine = dim * width
                image = QtGui.QImage(frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
                self.frameI.emit(QtGui.QPixmap.fromImage(image))

            if self.trace_queue is not None and self.trace_queue.qsize() > 0:
                traces = self.trace_queue.get()
                self.trace_viewer.full_trace_update(traces, self.trace_count)
                self.trace_count += 1

            dur = time.perf_counter() - st
            if dur < self.wtime:
                self.msleep((self.wtime-dur)*1000)