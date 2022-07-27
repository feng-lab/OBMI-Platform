from enum import Enum

import cv2
import numpy as np
from PyQt5.uic.Compiler.qtproxies import QtWidgets, QtGui
from PySide2.QtCore import QObject, Signal
from PySide2.QtWidgets import QGraphicsPolygonItem, QGraphicsEllipseItem


class ROIconnect(QObject):
    selected = Signal(str)
    moved = Signal(list)
    sizeChange = Signal(int)


class ROIType(Enum):
    CIRCLE = 1
    POLYGON = 2

    # Not callable error if no __call__ function
    def __call__(self, *args, **kwargs):
        return 0

class ROI(QGraphicsPolygonItem):

    def __init__(self, type, size=-1, shape=[]):
        super().__init__()

        self.type = type
        self.signals = ROIconnect()
        self.id = 0
        self.name = None
        self.noise = None
        self.size = size

        if self.type == ROIType.CIRCLE: # circle type ROI
            circle = QGraphicsEllipseItem(0,0,size,size)
            self.setPolygon(circle.shape().toFillPolygon())
        elif self.type == ROIType.POLYGON: # Polygon type ROI
            self.setPolygon(shape)
        else: # pending for other type
            print('not here')
            pass

        self.mat = self.matUpdate()

    def setName(self, str):
        self.name = str

    def setId(self, n):
        self.id = n

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.signals.selected.emit(self.name)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        x = self.pos().x()
        y = self.pos().y()
        self.signals.moved.emit([x, y])

    def wheelEvent(self, event):
        super().wheelEvent(event)
        if self.type == ROIType.CIRCLE:
            size = int(self.rect().width())
            if event.delta() > 0:
                size += 1
            else:
                size -= 1

            self.circleSizeChange(size)
            self.signals.sizeChange.emit(size)
            self.mat = self.matUpdate()

    def circleSizeChange(self, size):
        circle = QGraphicsEllipseItem(0, 0, size, size)
        self.setPolygon(circle.shape().toFillPolygon())

    # 获取轮廓
    def getContuor(self):
        l = self.polygon().toList()
        pts = [[int(p.x()),int(p.y())] for p in l]
        ret = np.array(pts).flatten()

        return ret

    # 更新矩阵
    def matUpdate(self):
        contour = self.getContuor()
        contour = contour.reshape(int(len(contour) / 2), 2)
        height = self.boundingRect().height()
        width = self.boundingRect().width()

        new_mat = np.zeros((int(width), int(height)))
        cv2.drawContours(new_mat, [contour], 0, 1, cv2.FILLED)
        mat = np.array(new_mat, np.uint8).T
        self.noise = -(mat.copy() - 1)
        print(mat.shape, self.noise.shape)
        return mat