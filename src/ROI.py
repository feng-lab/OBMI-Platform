from enum import Enum

import cv2
import numpy as np

from PySide2.QtCore import QObject, Signal, QPointF, QRectF
from PySide2.QtGui import QPixmap, Qt, QColor, QPen
from PySide2.QtWidgets import QGraphicsPolygonItem, QGraphicsEllipseItem, QGraphicsItem
from roifile import ImagejRoi
from shapely.geometry import Point, Polygon

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

def readImagejROI_v2(path):
    roi = ImagejRoi.fromfile(path)
    x = roi.left
    y = roi.top
    width = roi.right - roi.left
    height = roi.bottom - roi.top
    rect = [x, y, width, height]

    d = {
        'rect': rect,
        'name': roi.name,
    }
    return d


class ROIconnect(QObject):
    selected = Signal(str)
    moved = Signal(list)
    sizeChange = Signal(int)
    moved_multi = Signal(list, str)


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
        self._rect = None
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self.mask = None
        self.bg_mask = None

    def setId(self, n):
        self.id = n

    def setName(self, str):
        self.name = str

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.signals.selected.emit(self.name)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.signals.moved.emit(self.real_pos())

    # 已知cell_outline， 求得cell_mask
    def generate_cell_mask(self, cell_outline):
        x_min = int(self._rect.left())
        x_max = int(self._rect.right())
        y_min = int(self._rect.top())
        y_max = int(self._rect.bottom())

        # x,y范围+1后mask处于矩阵正中间
        xx, yy = np.meshgrid(np.arange(x_min, x_max + 1), np.arange(y_min, y_max + 1))
        # mask_cell = np.zeros_like(frame[y_min:y_max + 1, x_min:x_max + 1])
        cell_mask = np.zeros((y_max + 1 - y_min, x_max + 1 - x_min))
        cell = Polygon(cell_outline)
        for i in range(cell_mask.shape[0]):
            for j in range(cell_mask.shape[1]):
                if cell.contains(Point(xx[i, j], yy[i, j])):
                    cell_mask[i, j] = 1
        return cell_mask

    # 已知cell的外轮廓/cell_polygon，求得background_mask
    # 只要能提供准确的cell_polygon， 可以直接传入cell_polygon, 不需要cell_outline
    def generate_background_mask(self, cell_outline, expand_pixels=5):
        x_min = int(self._rect.left()) - expand_pixels
        x_max = int(self._rect.right()) + expand_pixels
        y_min = int(self._rect.top()) - expand_pixels
        y_max = int(self._rect.bottom()) + expand_pixels

        xx, yy = np.meshgrid(np.arange(x_min, x_max + 1), np.arange(y_min, y_max + 1))
        bg_mask = np.zeros((y_max + 1 - y_min, x_max + 1 - x_min))

        cell_polygon = Polygon(cell_outline)
        cell_and_bg_polygon = cell_polygon.buffer(expand_pixels)

        for i in range(bg_mask.shape[0]):
            for j in range(bg_mask.shape[1]):
                if not cell_polygon.contains(Point(xx[i, j], yy[i, j])) and cell_and_bg_polygon.contains(
                        Point(xx[i, j], yy[i, j])):
                    bg_mask[i, j] = 1

        return bg_mask

    def move_once(self):
        self.signals.moved_multi.emit(self.real_pos(), self.name)

    def real_pos(self):
        return [self._rect.x() + self.pos().x(), self._rect.y() + self.pos().y()]

    def updateRect(self):
        x = min(self._rect.left(), self._rect.right())
        y = min(self._rect.top(), self._rect.bottom())
        w = abs(self._rect.width())
        h = abs(self._rect.height())
        _rect = QRectF(x, y, w, h)

    def to_dict(self):
        raise NotImplementedError

class RectLabelItem(LabelItem):
    def __init__(self, rect, name, index=None, color=None, width=6.0, parent=None):
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

    @property
    def rect(self):
        return self._rect

    def boundingRect(self):
        return self._rect

    def paint(self, painter, option, widget=None):
        if self._pixel_map.isNull():
            painter.setPen(QPen(self._color, self._width))
            painter.drawRect(self.boundingRect())
        else:
            painter.scale(.2272, 2824)
            painter.drawPixmap(QPointF(self._rect.x(), self._rect.y()), self._pixel_map)

        if self.isSelected():
            pen = QPen(Qt.DashLine)
            pen.setColor(QColor(0, 0, 128))  # 蓝色虚线
            pen.setWidth(2)  # 虚线宽度
            painter.setPen(pen)
            painter.drawRect(self.boundingRect())

    def set_br(self, pos):
        self._rect.setBottomRight(pos)
        self.update()


    def updateMasks(self):
        outlines = self.get_rectangle_points()
        self.mask = self.generate_cell_mask(outlines)
        self.bg_mask = self.generate_background_mask(outlines)

    def get_rectangle_points(self):
        points = []
        width = self._rect.width()
        height = self._rect.height()

        top_left = (self._rect.left(), self._rect.top())

        # 从左上角到右上角
        for x in range(int(top_left[0]), int(top_left[0] + width)):
            points.append((x, int(top_left[1])))
        # 从右上角到右下角
        for y in range(int(top_left[1]), int(top_left[1] + height)):
            points.append((int(top_left[0] + width), y))
        # 从右下角到左下角
        for x in range(int(top_left[0] + width), int(top_left[0]), -1):
            points.append((x, int(top_left[1] + height)))
        # 从左下角到左上角
        for y in range(int(top_left[1] + height), int(top_left[1]), -1):
            points.append((int(top_left[0]), y))
        return points

    def to_dict(self):
        d = {
            'params': [self.real_pos()[0], self.real_pos()[1],self._rect.width(),self._rect.height()],
            'type': self.__class__.__name__,
            'id': self.id,
            'color': self._color.name(),
            'name': self.name
        }
        return d

class EllipseLabelItem(LabelItem):
    def __init__(self, rect, name, index=None, color=None, width=3.0, parent=None):
        super(EllipseLabelItem, self).__init__(parent)
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

    @property
    def rect(self):
        return self._rect

    def boundingRect(self):
        return self._rect

    def paint(self, painter, option, widget=None):
        if self._pixel_map.isNull():
            painter.setPen(QPen(self._color, self._width))
            painter.drawEllipse(self.boundingRect())
        else:
            painter.scale(.2272, 2824)
            painter.drawPixmap(QPointF(self._rect.x(), self._rect.y()), self._pixel_map)

        if self.isSelected():
            pen = QPen(Qt.DashLine)
            pen.setColor(QColor(0, 0, 128))  # 蓝色虚线
            pen.setWidth(2)  # 虚线宽度
            painter.setPen(pen)
            painter.drawEllipse(self.boundingRect())

    def set_br(self, pos):
        self._rect.setBottomRight(pos)
        self.update()

    def updateMasks(self):
        outlines = self.get_ellipse_points()
        self.mask = self.generate_cell_mask(outlines)
        self.bg_mask = self.generate_background_mask(outlines)

    def get_ellipse_points(self):
        points = []
        center_x = self._rect.center().x()
        center_y = self._rect.center().y()
        radius_x = self._rect.width() / 2
        radius_y = self._rect.height() / 2
        for angle in range(0, 360, 5):
            x = center_x + radius_x * np.cos(np.radians(angle))
            y = center_y + radius_y * np.sin(np.radians(angle))
            points.append([x, y])
        return np.array(points)

    def to_dict(self):
        d = {
            'params': [self.real_pos()[0], self.real_pos()[1],self._rect.width(),self._rect.height()],
            'type': self.__class__.__name__,
            'id': self.id,
            'color': self._color.name(),
            'name': self.name
        }
        return d
