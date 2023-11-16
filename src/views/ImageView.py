from PySide2 import QtGui, QtWidgets
from PySide2.QtCore import Qt, QRectF, Signal, QPointF, QLineF
from PySide2.QtGui import QKeySequence
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene

from src.ROI import RectLabelItem, EllipseLabelItem


class QtImageViewer(QGraphicsView):
    """
    PyQt image viewer widget for a QPixmap in a QGraphicsView scene with mouse zooming and panning.
    Displays a QImage or QPixmap (QImage is internally converted to a QPixmap).
    To display any other image format, you must first convert it to a QImage or QPixmap.

    Some useful image format conversion utilities:
        qimage2ndarray: NumPy ndarray <==> QImage    (https://github.com/hmeine/qimage2ndarray)
        ImageQt: PIL Image <==> QImage  (https://github.com/python-pillow/Pillow/blob/master/PIL/ImageQt.py)

    Mouse interaction:
        Left mouse button drag: Pan image.
        Right mouse button drag: Zoom box.
        Right mouse button doubleclick: Zoom to show entire image.

    """

    # Mouse button signals emit image scene (x, y) coordinates.
    # !!! For image (row, column) matrix indexing, row = y and column = x.
    refresh = Signal()
    selectReleased = Signal()
    cycleReleased = Signal(object)
    rectReleased = Signal(object)
    polyReleased = Signal(list)
    doneReleased = Signal(int)
    mouseScrollUp = Signal(bool)
    roiSelect = Signal(list)
    roiDelete = Signal()

    def __init__(self, parent):
        super(QtImageViewer, self).__init__(parent)
        # Image is displayed as a QPixmap in a QGraphicsScene attached to this QGraphicsView.
        self._draw_mode = 'cursor'
        self.setAcceptDrops(False)
        self.clipboard = None
        self.item_list = {
            'Annotation': [],
            'Segmentation': []
        }
        # Store a local handle to the scene's current image pixel map.
        self._pixel_handle = None
        self._current_item = None
        self._action_index = 0
        self._line_color = "#ff0000"
        self._polygon_color = "#00FFFF"
        self._marker_size = 4.0
        self._marker_color = "#ff0000"
        self.marker = None
        # Image aspect ratio mode.
        # !!! ONLY applies to full image. Aspect ratio is always ignored when zooming.
        #   Qt.IgnoreAspectRatio: Scale image to fit viewport.
        #   Qt.KeepAspectRatio: Scale image to fit inside viewport, preserving aspect ratio.
        #   Qt.KeepAspectRatioByExpanding: Scale image to fill the viewport, preserving aspect ratio.
        self.aspectRatioMode = Qt.KeepAspectRatio
        self.setMouseTracking(True)

        # Stack of QRectF zoom boxes in scene coordinates.
        self._draw_line = None
        self._draw_polygon = False
        self._pressed_pos = None
        self.polygon_list = []

        # Flags for enabling/disabling mouse interaction.
        self.canZoom = True
        self.canPan = False

        self.shortcut_delete = QtWidgets.QShortcut(QKeySequence(Qt.Key_Delete), self)
        self.shortcut_delete.activated.connect(self.delete_selected_roi)

    def randcolr(self):
        import numpy as np
        r, g, b = tuple(np.random.randint(256, size=3))
        color = QtGui.QColor(r, g, b)
        return color

    def resizeEvent(self, event):
        """ Maintain current zoom on resize.
        """
        pass

    def mousePressEvent(self, event):
        """ Start mouse pan or zoom mode.
        """
        super().mousePressEvent(event)

        scene_pos = self.mapToScene(event.pos())
        if event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.NoDrag)
            self._pressed_pos = scene_pos
            if self.marker in ['cursor']:
                if len(self.scene.selectedItems()) == 0:
                    self._current_item = self.scene.mouseGrabberItem()
                for item in self.scene.items():
                    if item.contains(scene_pos):
                        item.setSelected(True)
            if self.marker in ['zoom']:
                self.scene.clearSelection()
                self.setDragMode(QGraphicsView.ScrollHandDrag)
                super().mousePressEvent(event)
            if self.marker in ['rectangle', 'cycle']:

                rect = QRectF(self._pressed_pos.x(), self._pressed_pos.y(),
                              scene_pos.x() - self._pressed_pos.x(),
                              scene_pos.y() - self._pressed_pos.y())
                if self.marker == 'rectangle':
                    self._current_item = RectLabelItem(rect, name='rec',
                                                       index=len(self.scene.items()),
                                                       color=self.randcolr(),
                                                       width=self._marker_size / 4)
                if self.marker == 'cycle':
                    self._current_item = EllipseLabelItem(rect, name='cycle',
                                                          index=len(self.scene.items()),
                                                          color=self.randcolr(),
                                                          width=self._marker_size / 4)
                self.scene.addItem(self._current_item)
            if self.marker in ['select']:
                self.setDragMode(QGraphicsView.RubberBandDrag)
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super(QtImageViewer, self).mouseMoveEvent(event)
        scene_pos = self.mapToScene(event.pos())
        if self._pressed_pos is not None:
            if self.marker in ['rectangle', 'cycle']:
                self.scene.update()
                self._current_item.set_br(scene_pos)

        # self.refresh.emit()

    def mouseReleaseEvent(self, event):
        """ Stop mouse pan or zoom mode (apply zoom if valid).
        """
        super(QtImageViewer, self).mouseReleaseEvent(event)
        scene_pos = self.mapToScene(event.pos())
        selected_items = self.scene.selectedItems()
        if self.marker in ['zoom']:
            self.scene.clearSelection()
            # self.setDragMode(QGraphicsView.ScrollHandDrag)
        if self.marker in ['rectangle']:
            self._current_item.set_br(scene_pos)
            self.rectReleased.emit(self._current_item)
        if self.marker in ['cycle']:
            self._current_item.set_br(scene_pos)
            self.cycleReleased.emit(self._current_item)
        roi_names = []
        for r in selected_items:
            roi_names.append(r.name)
        self.roiSelect.emit(roi_names)
        if len(selected_items) > 0:
            for r in selected_items:
                r.move_once()
        # update pos
        self._pressed_pos = None

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        if self.marker in ['cursor', 'zoom', 'rectangle', 'cycle']:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            zoomInFactor = 1.25
            zoomOutFactor = 1 / zoomInFactor

            # Save the scene pos
            oldPos = self.mapToScene(event.pos())

            # Zoom
            if event.angleDelta().y() > 0:
                zoomFactor = zoomInFactor
            else:
                zoomFactor = zoomOutFactor
            self.scale(zoomFactor, zoomFactor)

            # Get the new position
            newPos = self.mapToScene(event.pos())

            # Move scene to old position
            delta = newPos - oldPos
            self.translate(delta.x(), delta.y())
        else:
            if event.angleDelta().y() > 0:
                self.mouseScrollUp.emit(True)
            else:
                self.mouseScrollUp.emit(False)

    def setScene(self, scene) -> None:
        self.scene = scene
        super().setScene(scene)

    def clear_scene_items(self):
        for item in self.scene.items():
            if isinstance(item, RectLabelItem) or isinstance(item, EllipseLabelItem):
                self.scene.removeItem(item)

    def delete_selected_roi(self):
        self.roiDelete.emit()

    def select_items(self, roi_list):
        self.scene.clearSelection()
        for r in roi_list:
            r.setSelected(True)