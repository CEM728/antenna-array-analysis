# -*- coding: utf-8 -*-
"""
    Antenna Array Analysis
    Copyright (C) 2019  Zhengyu Peng

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys
import res_rc
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QThread

from linear_array import Linear_Array

import pyqtgraph as pg

# pg.setConfigOption('background', 'w')
# pg.setConfigOption('foreground', 'k')
# pg.setConfigOption('antialias', True)
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

import numpy as np


class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(QtWidgets.QMainWindow, self).__init__()
        self.theta = np.linspace(-90, 90, num=1801, endpoint=True)
        self.window_dict = {
            0: self.disableWinConfig,
            1: self.chebyshev,
            2: self.taylor,
            3: self.disableWinConfig,
            4: self.disableWinConfig
        }
        self.ui = uic.loadUi('ui_array_analysis.ui', self)

        self.pgCanvas = pg.GraphicsLayoutWidget()
        self.figureLayout.addWidget(self.pgCanvas)

        self.plotView = self.pgCanvas.addPlot(row=0, col=0, rowspan=1)
        self.pgFigure = pg.PlotDataItem()
        self.pgFigureHold = pg.PlotDataItem()
        self.plotView.setXRange(-90, 90)
        self.plotView.setYRange(-80, 0)

        self.plotView.addItem(self.pgFigure)
        self.plotView.setLabel(axis='bottom', text='Angle', units='°')
        self.plotView.setLabel(
            axis='left', text='Normalized amplitude', units='dB')
        self.plotView.showGrid(x=True, y=True, alpha=0.5)

        self.penActive = pg.mkPen(color=(244, 143, 177), width=1)
        self.pgFigure.setPen(self.penActive)
        self.penHold = pg.mkPen(color=(158, 158, 158), width=1)
        self.pgFigureHold.setPen(self.penHold)

        self.plotView.setLimits(xMin=-90, xMax=90, yMin=-110, yMax=1, minXRange=0.1, minYRange=0.1)

        self.plotView.sigXRangeChanged.connect(self.plotview_x_range_changed)

        #############
        self.testPlot = self.pgCanvas.addPlot(row=1, col=0, rowspan=2)
        self.testPlot.setAspectLocked()
        self.testPlot.hideAxis('left')
        self.testPlot.hideAxis('bottom')

        # Add polar grid lines
        self.testPlot.addLine(x=0, pen=0.2)
        self.testPlot.addLine(y=0, pen=0.2)
        for r in range(2, 20, 2):
            circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
            circle.setPen(pg.mkPen(0.2))
            self.testPlot.addItem(circle)

        self.pgPolarPlot = pg.PlotDataItem()
        self.testPlot.addItem(self.pgPolarPlot)

        # self.pgCanvas.removeItem(self.testPlot)
        # self.pgCanvas.addItem(self.testPlot)
        ######################

        self.init_ui()

        self.linear_array = Linear_Array()
        self.linear_array_thread = QThread()
        self.linear_array.patternReady.connect(self.updatePattern)
        self.linear_array.patternReady.connect(self.updatePolarPattern)
        self.linear_array_thread.started.connect(
            self.linear_array.calculatePattern)
        self.linear_array.moveToThread(self.linear_array_thread)
        self.linear_array_thread.start()

        self.updateLinearArrayParameter()
        self.ui.show()

    def init_ui(self):
        self.ui.spinBox_SLL.setVisible(False)
        self.ui.label_SLL.setVisible(False)
        self.ui.horizontalSlider_SLL.setVisible(False)
        self.ui.spinBox_nbar.setVisible(False)
        self.ui.label_nbar.setVisible(False)
        self.ui.horizontalSlider_nbar.setVisible(False)
        self.ui.clearButton.setEnabled(False)

        self.ui.comboBox_Window.addItems(
            ['Square', 'Chebyshev', 'Taylor', 'Hamming', 'Hann'])

        self.ui.spinBox_ArraySize.valueChanged.connect(
            self.updateLinearArrayParameter)

        self.ui.doubleSpinBox_Spacing.valueChanged.connect(
            self.updateLinearArrayParameter)

        self.ui.doubleSpinBox_SteeringAngle.valueChanged.connect(
            self.steering_angle_value_changed)
        self.ui.horizontalSlider_SteeringAngle.valueChanged.connect(
            self.steering_angle_slider_moved)

        self.ui.comboBox_Window.currentIndexChanged.connect(
            self.window_combobox_changed)

        self.ui.spinBox_SLL.valueChanged.connect(self.sll_value_change)
        self.ui.horizontalSlider_SLL.valueChanged.connect(self.sllSliderMoved)

        self.ui.spinBox_nbar.valueChanged.connect(self.nbarValueChange)
        self.ui.horizontalSlider_nbar.valueChanged.connect(
            self.nbarSliderMoved)

        self.ui.holdButton.clicked.connect(self.holdFigure)
        self.ui.clearButton.clicked.connect(self.clearFigure)

    def steering_angle_value_changed(self, value):
        self.ui.horizontalSlider_SteeringAngle.setValue(
            self.ui.doubleSpinBox_SteeringAngle.value() * 10)
        self.updateLinearArrayParameter()

    def steering_angle_slider_moved(self, value):
        self.ui.doubleSpinBox_SteeringAngle.setValue(value / 10)
        self.updateLinearArrayParameter()

    def window_combobox_changed(self, value):
        self.window_dict[value]()
        self.updateLinearArrayParameter()

    def sll_value_change(self, value):
        self.ui.horizontalSlider_SLL.setValue(self.ui.spinBox_SLL.value())
        self.updateLinearArrayParameter()

    def sllSliderMoved(self, value):
        self.ui.spinBox_SLL.setValue(value)
        self.updateLinearArrayParameter()

    def nbarValueChange(self, value):
        self.ui.horizontalSlider_nbar.setValue(self.ui.spinBox_nbar.value())
        self.updateLinearArrayParameter()

    def nbarSliderMoved(self, value):
        self.ui.spinBox_nbar.setValue(value)
        self.updateLinearArrayParameter()

    def updateLinearArrayParameter(self):
        self.array_size = self.ui.spinBox_ArraySize.value()
        self.spacing = self.ui.doubleSpinBox_Spacing.value()
        self.beam_loc = self.ui.doubleSpinBox_SteeringAngle.value()
        self.window_type = self.ui.comboBox_Window.currentIndex()
        self.window_sll = self.ui.spinBox_SLL.value()
        self.window_nbar = self.ui.spinBox_nbar.value()

        self.linear_array.updateData(
            self.array_size, self.spacing, self.beam_loc, self.theta,
            self.window_type, self.window_sll, self.window_nbar)

    def updatePattern(self, angle, pattern):
        self.pgFigure.setData(angle, pattern)
        self.angle = angle
        self.pattern = pattern

    def updatePolarPattern(self, angle, pattern):
        pattern = pattern + 60
        pattern[np.where(pattern < 0)] = 0
        x = pattern * np.sin(angle / 180 * np.pi)
        y = pattern * np.cos(angle / 180 * np.pi)
        # self.testPlot.plot(x, y)
        self.pgPolarPlot.setData(x, y)

    def holdFigure(self):
        self.pgFigureHold.setData(self.angle, self.pattern)
        self.plotView.addItem(self.pgFigureHold)
        self.ui.clearButton.setEnabled(True)

    def clearFigure(self):
        self.plotView.removeItem(self.pgFigureHold)
        self.ui.clearButton.setEnabled(False)

    def disableWinConfig(self):
        self.ui.spinBox_SLL.setVisible(False)
        self.ui.label_SLL.setVisible(False)
        self.ui.horizontalSlider_SLL.setVisible(False)
        self.ui.spinBox_nbar.setVisible(False)
        self.ui.label_nbar.setVisible(False)
        self.ui.horizontalSlider_nbar.setVisible(False)

    def chebyshev(self):
        self.ui.spinBox_SLL.setVisible(True)
        self.ui.label_SLL.setVisible(True)
        self.ui.horizontalSlider_SLL.setVisible(True)
        self.ui.spinBox_nbar.setVisible(False)
        self.ui.label_nbar.setVisible(False)
        self.ui.horizontalSlider_nbar.setVisible(False)

    def taylor(self):
        self.ui.spinBox_SLL.setVisible(True)
        self.ui.label_SLL.setVisible(True)
        self.ui.horizontalSlider_SLL.setVisible(True)
        self.ui.spinBox_nbar.setVisible(True)
        self.ui.label_nbar.setVisible(True)
        self.ui.horizontalSlider_nbar.setVisible(True)

    def plotview_x_range_changed(self, item):
        self.theta = np.linspace(item.viewRange()[0][0], item.viewRange()[0][1], num=1801, endpoint=True)
        self.updateLinearArrayParameter()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
