import random

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QGridLayout, 
        QPushButton, QAbstractItemView, QCheckBox, QTableWidgetItem, QColorDialog)
import numpy as np
from PySide2 import QtGui, QtCore
import re

class Table(QWidget):
    def __init__(self, type, parent=None):
        super().__init__(parent)

        self.table = QTableWidget(parent)
        self._mainwin = parent

        self.__make_layout()
        self.__make_table()

        self.table.cellClicked.connect(self.check_crd)
        self.itemlist = []
        self.namelist = []

        self.color_row = 3 ## 추후에
        self.itemCount = 1

        # locks for value change
        self.addlock = False
        self.editlock = False
        self.table.itemChanged.connect(self.value_changed)

        if type == 0: # type0 for offline tab, type1 for online tab
            self.spinboxX = self._mainwin.ui.OffROILocationXValue
            self.spinboxY = self._mainwin.ui.OffROILocationYValue
            self.spinboxSize = self._mainwin.ui.OffROISizeValue
        else:
            self.spinboxX = self._mainwin.ui.OnROILocationXValue_5
            self.spinboxY = self._mainwin.ui.OnROILocationYValue_5
            self.spinboxSize = self._mainwin.ui.OnROISizeValue_5

        self.spinboxX.valueChanged.connect(self.spinBox_x)
        self.spinboxY.valueChanged.connect(self.spinBox_y)
        self.spinboxSize.valueChanged.connect(self.spinBox_size)


    def spinBox_x(self, value):
        if self.editlock:
            return

        row = self.table.currentRow()
        pos = self.itemlist[row].pos()
        self.itemlist[row].setPos(float(value), pos.y())
        posstr = f'({int(value)},{int(pos.y())})'
        self.table.item(row, 2).setText(posstr)

    def spinBox_y(self, value):
        if self.editlock:
            return

        row = self.table.currentRow()
        pos = self.itemlist[row].pos()
        self.itemlist[row].setPos(pos.x(), float(value))
        posstr = f'({int(pos.x())},{int(value)})'
        self.table.item(row, 2).setText(posstr)

    def spinBox_size(self, value):
        if self.editlock:
            return

        row = self.table.currentRow()
        self.itemlist[row].setRect(0, 0, int(value), int(value))


    def value_changed(self, item):
        if self.addlock or self.editlock:
            return

        column = item.column()
        row = item.row()

        if row < len(self.itemlist):
            if column == 1:
                namestr = item.text()
                self.namelist[row] = namestr
                self.itemlist[row].setName(namestr)
                if self._mainwin.trace_viewer:
                    self._mainwin.trace_viewer.chartlist[row].chart().setTitle(namestr)
            if column == 2:
                posstr = item.text()
                match = re.search(r'^\s*\(\d+\.?\d*,\s*\d+\.?\d*\)\s*$', posstr)
                if match:
                    pos = re.findall(r'\d+\.?\d*', match.group())
                    self.itemlist[row].setPos(float(pos[0]), float(pos[1]))
                    self.editlock = True
                    self.spinboxX.setValue(int(pos[0]))
                    self.spinboxY.setValue(int(pos[1]))
                    self.editlock = False
                else:
                    pos = self.itemlist[row].pos()
                    posstr = f'({int(pos.x())},{int(pos.y())})'
                    item.setText(posstr)
            if column == 3:
                col = item.backgroundColor()
                self.itemlist[row].setPen(QtGui.QPen(QtGui.QColor(col), 2, Qt.SolidLine))


    def __make_table(self):
        ##self.table.setSelectionMode(QAbstractItemView.SelectRows) ##
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # default

        self.table.setColumnCount(4)
        self.table.setRowCount(0)

        self.table.setHorizontalHeaderLabels(['V','name', 'xy','C'])
        self.table.horizontalHeaderItem(0).setToolTip('set visible/hide...')         

        self.table.setColumnWidth(0, 20) # v
        self.table.setColumnWidth(1, 50) # name
        self.table.setColumnWidth(2, 65) # xy
        self.table.setColumnWidth(3, 20) # c

    ###Hide3##    self.add_table_form(0,(255,0,255))
    ###Hide3##    self.add_table_form(1,(0,255,255))
    ###Hide3##    self.add_table_form(2,(0,0,255))
        
        #header_item = QTableWidgetItem('')

    def __make_layout(self): ## widget안에서
        vbox = QVBoxLayout()
        vbox.addWidget(self.table)

        grid = QGridLayout()
        vbox.addLayout(grid)

        self.setLayout(vbox)
        ##self.setGeometry(200,200,400,500)
        self.setGeometry(0,0,0,0)
        self.setWindowTitle('ROI list')

        self.btn1 = QPushButton("add")
        grid.addWidget(self.btn1, 0, 0)
        #btn1.clicked.connect(self.__btn1_clicked)
        #self.btn1.clicked(self.randomAdd(200))

    def randomAdd(self):
        for i in range(200):
            x = random.randint(30, 600)
            y = random.randint(30, 420)
            self._mainwin.addOnR(QtCore.QPointF(x, y))

    def __btn1_clicked(self):
        self.add_to_table()

    def check_crd(self, row, column):
        item = self.itemlist[row]
        pos = item.pos()
        self.editlock = True
        self.spinboxX.setValue(int(pos.x()))
        self.spinboxY.setValue(int(pos.y()))
        self.spinboxSize.setValue(int(item.rect().width()))
        self.editlock = False
        print(pos)

        print(row, column)
        if column == self.color_row:
            print('color button')
            self.color_button_click(row, column)
        if column == 2:
            print('2clicked')

    def add_to_table(self, roi_circle, colr):
        self.addlock = True
        ## num 을 받든지, 여기서 get 하던지 
        if True: #선택 안되어있으면. :
            new_row_num = self.table.rowCount() + 1
            self.table.setRowCount(new_row_num)
            print(new_row_num)
            #colr = self.randcolr()
            self.add_table_form(new_row_num-1, colr, roi_circle)
        else: 
            self.table.insertRow(num)

        self.addlock = False



    def randcolr(self):
        return tuple(np.random.randint(256, size=3))

    def color_button_click(self, row, column):
        colr = self.table.item(row, column).backgroundColor()
        col = QColorDialog.getColor(colr, self)
        if col.isValid():
            #rgb = (col.red(), col.green(), col.blue())
            rgb = col.rgb()
            self.color_update(row, column, rgb) ## 바로넘기면 안되나?
            return rgb


    def color_update(self, row, column, rgb):
        self.table.item(row, column).setBackgroundColor(rgb)
        ##  원 색등도 바꾸어야 하니까. 

    def color_dial(self, colr):
        col = QColorDialog.getColor(colr, self)
        if col.isValid():
            rgb = (col.red(), col.green(), col.blue())
            print(rgb)  ## color를 다시 받아올 방법   

    def add_table_form(self, num, colr, roi_circle):
        self.itemlist.append(roi_circle)
        roi_circle.setId(self.itemCount)
        roi_circle.signals.selected.connect(self.circle_click)
        roi_circle.signals.moved.connect(self.circle_release)
        roi_circle.signals.sizeChange.connect(self.circle_size)

        chkbox = QCheckBox()
        chkbox.setChecked(True)
        chkbox.stateChanged.connect(lambda: self.check_state(chkbox, roi_circle))

        ## color button
        brushbtn = QPushButton()###
        print(f'background-color:rgb{colr}')
        brushbtn.setStyleSheet(f'background-color:rgb{colr}')
        brushbtn.setFixedWidth(20)

        namestr = 'ROI_' + str(self.itemCount)
        self.namelist.append(namestr)
        roi_circle.setName(namestr)

        pos = roi_circle.pos()
        posstr = f'({int(pos.x())},{int(pos.y())})'

        self.table.setCellWidget(num, 0, chkbox)
        self.table.setItem(num, 1, QTableWidgetItem(namestr)) # name ## default name
        self.table.setItem(num, 2, QTableWidgetItem(posstr)) # location ## get geom
        ## self.table.setCellWidget(num, 3, brushbtn)
        self.table.setItem(num, 3, QTableWidgetItem())
        
        self.table.item(num, 3).setBackgroundColor(QtGui.QColor(colr[0], colr[1], colr[2]))

        self.itemCount += 1


       # self.table. setItem(num,3).clicked.connect(self, color_dial(QtGui.QColor(colr[0], colr[1], colr[2])))

        ## class 만들게 되면,. item = QTableWidgetItem()
        ## self.table.setItem(, , item)

        #rgb = 
        ## brushbtn.clicked.connect(self.color_dial(QtGui.QColor(colr[0], colr[1], colr[2])))
#        def color_dial2(colr):
#            col = QColorDialog.getColor(colr)    
#        brushbtn.clicked.connect(color_dial2(QtGui.QColor(colr[0], colr[1], colr[2])))
        
        
        #print(rgb)
    def circle_click(self, name):
        num = self.namelist.index(name)
        self.table.selectRow(num)
        self.check_crd(num, 1)

    def circle_release(self, pos):
        num = self.table.currentRow()
        posstr = f'({int(pos[0])},{int(pos[1])})'
        print(pos[0], pos[1])
        print(f'num:{num}')
        self.editlock = True
        self.spinboxX.setValue(int(pos[0]))
        self.spinboxY.setValue(int(pos[1]))
        self.table.item(num, 2).setText(posstr)
        self.editlock = False

    def circle_size(self, size):
        self.spinboxSize.setValue(size)

    # remove ROI circle from table
    def deleteRoi(self):
        row = self.table.currentRow()
        roi_circle = self.itemlist.pop(row)
        self.namelist.pop(row)
        self.table.removeRow(row)
        return roi_circle

    # show/hide function for ROI circle
    def check_state(self, checkbox, roi_circle):
        if checkbox.isChecked():
            roi_circle.setVisible(True)
        else:
            roi_circle.setVisible(False)