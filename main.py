#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.Qt import QThread
from PyQt5.QtCore import QTimer
import design
from time import sleep, time
from gs_lps import us_nav
import pyqtgraph as pg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.pyplot import subplots, tight_layout, colorbar


class DataHandler(QtCore.QObject):
    update_info = QtCore.pyqtSignal(list, list, list)

    def __init__(self):
        super().__init__()
        self.nav = us_nav("/dev/serial0", debug=True)
        self.nav.start()

    def run(self):
        while True:
            pos = self.nav.get_position()
            angles = self.nav.get_angles()
            strengths = self.nav.get_strength()
            if pos is not None and angles is not None and strengths is not None:
                self.update_info.emit(pos, angles, strengths)
            QThread.msleep(100)

    def kill(self):
        self.nav.stop()


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig, ((self.ax2, self.ax3), (self.ax1, self.ax4)) = subplots(nrows=2, ncols=2)
        tight_layout()
        super(MplCanvas, self).__init__(self.fig)


class Core(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.f = open('pos_log%d.txt' % (int(time())), 'w')

        self.locus_thread = QThread()
        self.dataHandler = DataHandler()
        self.dataHandler.moveToThread(self.locus_thread)
        self.dataHandler.update_info.connect(self.update_data)
        self.locus_thread.started.connect(self.dataHandler.run)
        self.locus_thread.start()

        self.plot1 = self.create_plot()
        self.plot2 = self.create_plot()
        self.plot3 = self.create_plot()
        self.plot4 = self.create_plot()

        self.plotLayout.addWidget(self.plot1)
        self.plotLayout.addWidget(self.plot2)
        self.plotLayout.addWidget(self.plot3)
        self.plotLayout.addWidget(self.plot4)

        self.current_time = time()
        self.zero_time = self.current_time
        self.time_data = [0]

        self.plot1_data = [1000]
        self.plot2_data = [1000]
        self.plot3_data = [1000]
        self.plot4_data = [1000]

        self.update_count = 0
        self.update_count_mpl = 0

        self.sensors_plot = MplCanvas(self, width=10, height=10, dpi=100)
        self.MPLLayout.addWidget(self.sensors_plot, 1, 0)

        self.strength1_plot_data = [0, 1000]
        self.strength2_plot_data = [0, 1000]
        self.strength3_plot_data = [0, 1000]
        self.strength4_plot_data = [0, 1000]
        self.strength_x_data = [0, 10.5]
        self.strength_y_data = [0, 10.5]

        self.update_mpl_timer = QTimer()
        self.update_mpl_timer.timeout.connect(self.mpl_redraw)
        self.update_mpl_timer.setInterval(2500)
        self.update_mpl_timer.start()
        self._first_render = True

    @staticmethod
    def create_plot():
        plot = pg.PlotWidget()
        plot.setBackground('w')
        plot.showGrid(x=True, y=True)
        plot.setXRange(0, 30, 0)
        plot.setYRange(-50, 1100, 0)
        plot.setMouseEnabled(x=False, y=False)
        return plot

    @QtCore.pyqtSlot(list, list, list)
    def update_data(self, pos, angles, strengths):
        x, y, z = None, None, None
        roll, pitch, yaw = None, None, None
        beacon1, beacon2, beacon3, beacon4 = None, None, None, None
        if pos is not None:
            x = pos[0]
            y = pos[1]
            z = pos[2]

            beacon1 = (pos[3] & 0b00001)
            beacon2 = (pos[3] & 0b0010) >> 1
            beacon3 = (pos[3] & 0b0100) >> 2
            beacon4 = (pos[3] & 0b1000) >> 3

            self.xVal.setText("%.3f" % x)
            self.yVal.setText("%.3f" % y)
            self.zVal.setText("%.3f" % z)

            if beacon1:  # 1 beacon is alive
                self.sens1.setText("1")
            else:
                self.sens1.setText("")

            if beacon2:  # 2 beacon is alive
                self.sens2.setText("2")
            else:
                self.sens2.setText("")

            if beacon3:  # 3 beacon is alive
                self.sens3.setText("3")
            else:
                self.sens3.setText("")

            if beacon4:  # 4 beacon is alive
                self.sens4.setText("4")
            else:
                self.sens4.setText("")
        else:
            self.xVal.setText("None")
            self.yVal.setText("None")
            self.zVal.setText("None")

            self.sens1.setText("-")
            self.sens2.setText("-")
            self.sens3.setText("-")
            self.sens4.setText("-")

        if angles is not None:
            roll = angles[0]
            pitch = angles[1]
            yaw = angles[2]

            self.rollVal.setText("%.1f" % roll)
            self.pitchVal.setText("%.1f" % pitch)
            self.yawVal.setText("%.1f" % yaw)

        if strengths is not None:
            self.strength1.setText("%d" % strengths[0])
            self.strength2.setText("%d" % strengths[1])
            self.strength3.setText("%d" % strengths[2])
            self.strength4.setText("%d" % strengths[3])

            if strengths[0] > max(self.plot1_data):
                self.plot1.setYRange(-50, strengths[0] + 100, 0)
            if strengths[1] > max(self.plot2_data):
                self.plot2.setYRange(-50, strengths[1] + 100, 0)
            if strengths[2] > max(self.plot3_data):
                self.plot3.setYRange(-50, strengths[2] + 100, 0)
            if strengths[3] > max(self.plot4_data):
                self.plot4.setYRange(-50, strengths[3] + 100, 0)

            self.plot1_data.append(strengths[0])
            self.plot2_data.append(strengths[1])
            self.plot3_data.append(strengths[2])
            self.plot4_data.append(strengths[3])

            self.current_time = time()
            self.time_data.append(self.current_time - self.zero_time)
            max_range = 30
            if (self.current_time - self.zero_time) // max_range > self.update_count:
                self.update_count += 1
                self.plot1.setXRange(self.current_time - self.zero_time,
                                     self.current_time - self.zero_time + max_range, 0)
                self.plot2.setXRange(self.current_time - self.zero_time,
                                     self.current_time - self.zero_time + max_range, 0)
                self.plot3.setXRange(self.current_time - self.zero_time,
                                     self.current_time - self.zero_time + max_range, 0)
                self.plot4.setXRange(self.current_time - self.zero_time,
                                     self.current_time - self.zero_time + max_range, 0)

            pen = pg.mkPen(color=(255, 0, 0))
            self.plot1.plot(self.time_data, self.plot1_data, pen=pen)
            self.plot2.plot(self.time_data, self.plot2_data, pen=pen)
            self.plot3.plot(self.time_data, self.plot3_data, pen=pen)
            self.plot4.plot(self.time_data, self.plot4_data, pen=pen)

            if pos is not None and (self.current_time - self.zero_time) // 240 < self.update_count_mpl:
                # if we're working more than 4 mins clear our plots
                self.strength_x_data.append(pos[0])
                self.strength_y_data.append(pos[1])
                max_value_amp = 1000
                self.strength1_plot_data.append(min(strengths[0], max_value_amp))
                self.strength2_plot_data.append(min(strengths[1], max_value_amp))
                self.strength3_plot_data.append(min(strengths[2], max_value_amp))
                self.strength4_plot_data.append(min(strengths[3], max_value_amp))
            else:
                if pos is not None:
                    self.update_count_mpl += 1
                    self.strength1_plot_data = [0, 1000]
                    self.strength2_plot_data = [0, 1000]
                    self.strength3_plot_data = [0, 1000]
                    self.strength4_plot_data = [0, 1000]
                    self.strength_x_data = [0, 10.5]
                    self.strength_y_data = [0, 10.5]

        if pos is not None and angles is not None and strengths is not None:
            log = '%.3f %.3f %.3f %.3f %.3f %.3f %d %d %d %d %d %d %d %d' % (x, y, z,
                                                                             roll, pitch, yaw,
                                                                             beacon1, beacon2, beacon3, beacon4,
                                                                             strengths[0], strengths[1],
                                                                             strengths[2], strengths[3])
            # print(log)
            self.f.write(log)

    def mpl_redraw(self):
        self.sensors_plot.ax1.cla()
        self.sensors_plot.ax2.cla()
        self.sensors_plot.ax3.cla()
        self.sensors_plot.ax4.cla()
        im1 = self.sensors_plot.ax1.scatter(self.strength_x_data, self.strength_y_data, c=self.strength1_plot_data,
                                            cmap="viridis")
        im2 = self.sensors_plot.ax2.scatter(self.strength_x_data, self.strength_y_data, c=self.strength2_plot_data,
                                            cmap="viridis")
        im3 = self.sensors_plot.ax3.scatter(self.strength_x_data, self.strength_y_data, c=self.strength3_plot_data,
                                            cmap="viridis")
        im4 = self.sensors_plot.ax4.scatter(self.strength_x_data, self.strength_y_data, c=self.strength4_plot_data,
                                            cmap="viridis")
        if self._first_render:
            self.sensors_plot.fig.colorbar(im1, ax=self.sensors_plot.ax1)
            self.sensors_plot.fig.colorbar(im2, ax=self.sensors_plot.ax2)
            self.sensors_plot.fig.colorbar(im3, ax=self.sensors_plot.ax3)
            self.sensors_plot.fig.colorbar(im4, ax=self.sensors_plot.ax4)
        self.sensors_plot.draw()
        self._first_render = False

    def closeEvent(self, e):
        print('closing')
        self.locus_thread.terminate()
        self.dataHandler.kill()
        self.f.close()
        self.update_mpl_timer.stop()
        sys.exit(0)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Core()
    window.show()
    app.exec_()
