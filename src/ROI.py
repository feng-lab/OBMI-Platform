from enum import Enum

import cv2
import numpy as np

from PySide2.QtCore import QObject, Signal, QPointF
from PySide2.QtGui import QPixmap, Qt, QColor, QPen
from PySide2.QtWidgets import QGraphicsPolygonItem, QGraphicsEllipseItem, QGraphicsItem
from roifile import ImagejRoi


def readImagejROI(path):
    roi = ImagejRoi.fromfile(path)
    contour = roi.coordinates()
    x = roi.left
    y = roi.top
    contour = contour - [x, y]
    contour = [QPointF(c[0], c[1]) for c in contour]

    d = {
        'name': roi.name,
        'x': roi.left,
        'y': roi.top,
        'contour': contour,
    }
    return d


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
        self.c_size = 0

        if self.type == ROIType.CIRCLE:  # circle type ROI
            circle = QGraphicsEllipseItem(0, 0, size, size)
            self.setPolygon(circle.shape().toFillPolygon())
        elif self.type == ROIType.POLYGON:  # Polygon type ROI
            self.setPolygon(shape)
        else:  # pending for other type
            print('not here')
            pass

        self.contours = self.contourUpdate()
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
            size = int(self.boundingRect().width()) - 1
            if event.delta() > 0:
                size += 1
            else:
                if size > 1:
                    size -= 1

            self.circleSizeChange(size)
            self.signals.sizeChange.emit(size)

    def circleSizeChange(self, size):
        circle = QGraphicsEllipseItem(0, 0, size, size)
        self.setPolygon(circle.shape().toFillPolygon())
        self.contours = self.contourUpdate()
        self.mat = self.matUpdate()

    # contour update
    def contourUpdate(self):
        l = self.polygon().toList()
        pts = [[p.x(), p.y()] for p in l]
        ret = np.array(pts).flatten()
        self.c_size = len(ret)
        return ret

    # update mapping matrix
    def matUpdate(self):
        contour = self.contours.astype(int)
        contour = contour.reshape(int(self.c_size / 2), 2)
        height = self.boundingRect().height()
        width = self.boundingRect().width()

        new_mat = np.zeros((int(width), int(height)))
        cv2.drawContours(new_mat, [contour], 0, 1, cv2.FILLED)
        mat = np.array(new_mat, np.uint8).T
        self.noise = -(mat.copy() - 1).flatten()
        return mat.flatten()

    def get_contour_dict(self):
        d = {
            'x': self.pos().x(),
            'y': self.pos().y(),
            'contours': self.contours
        }
        return d


class LabelItem(QGraphicsItem):
    def __init__(self, parent=None):
        super(LabelItem, self).__init__(parent)
        self.signals = ROIconnect()
        self._color = QColor('#00ff00')
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)

    def setId(self, n):
        self.id = n

    def setName(self, str):
        self.name = str

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.signals.selected.emit(self.name)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        x = self.pos().x()
        y = self.pos().y()
        self.signals.moved.emit([x, y])


class RectLabelItem(LabelItem):
    def __init__(self, rect, name, index=None, color=None, width=3.0, parent=None):
        super(RectLabelItem, self).__init__(parent)
        self.signals = ROIconnect()
        self.name = name
        self._pixel_map = QPixmap()
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self._rect = rect
        self.id = index
        if color is not None:
            self._color = QColor(color)
        else:
            self._color = QColor("#ff0000")
        self._width = width

    def boundingRect(self):
        return self._rect

    def paint(self, painter, option, widget=None):
        if self._pixel_map.isNull():
            painter.setPen(QPen(self._color, self._width))
            painter.drawRect(self.boundingRect())
        else:
            painter.scale(.2272, 2824)
            painter.drawPixmap(QPointF(self._rect.x(), self._rect.y()), self._pixel_map)

    def set_br(self, pos):
        self._rect.setBottomRight(pos)
        self.update()


class EllipseLabelItem(LabelItem):
    def __init__(self, rect, name, index=None, color=None, width=3.0, parent=None):
        super(EllipseLabelItem, self).__init__(parent)
        self.signals = ROIconnect()
        self.name = name
        self._pixel_map = QPixmap()
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setToolTip(str(self.name))
        self.id = index
        self._rect = rect
        if color is not None:
            self._color = QColor(color)
        else:
            self._color = QColor("#ff0000")
        self._width = width

    def boundingRect(self):
        return self._rect

    def paint(self, painter, option, widget=None):
        if self._pixel_map.isNull():
            painter.setPen(QPen(self._color, self._width))
            painter.drawEllipse(self.boundingRect())  # Use drawEllipse instead of drawRect
        else:
            painter.scale(.2272, 2824)
            painter.drawPixmap(QPointF(self._rect.x(), self._rect.y()), self._pixel_map)

    def set_br(self, pos):
        self._rect.setBottomRight(pos)
        self.update()
