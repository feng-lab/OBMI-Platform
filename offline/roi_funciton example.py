import sys

import PyQt5
from PyQt5.QtWidgets import QApplication,QWidget
from PyQt5.QtGui import QPainter, QPixmap,QPen

image_path = r"D:\04_OBMI_Development\CalciumImage.jpg"

class Demo(QWidget):
    def __init__(self):
        super().__init__()
        self.image = QPixmap(image_path)

    def paintEvent(self, QPaintEvent):
        # print(self.rect())

        # draw on image
        pen = QPen()

        pen.setWidth(3)

        pen.setColor(PyQt5.QtGui.QColor("#EB5160"))

        # upload image
        painter = QPainter(self)
        painter.drawPixmap(self.rect(),self.image)
        painter.setPen(pen)
        painter.drawEllipse(300, 300, 15, 15)
        painter.drawRect(150, 150, 20, 20)


def main():
    app = QApplication(sys.argv)
    demo = Demo()
    demo.show()


    sys.exit(app.exec_())


main()
