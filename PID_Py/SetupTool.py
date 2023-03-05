import sys

from PySide6 import QtGui
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis    
from PySide6.QtCore import QTimer, Qt

import numpy as np

class SetupToolApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        
        self.setWindowTitle("PID_Py : SetupTool")
        self.setFixedSize(1000, 600)

        # ===== Real-time graph ====
        self.xAxis = QValueAxis()
        self.xAxis.setTitleText("Time (s)")
        self.xAxis.setRange(0, 2*np.pi)

        self.yAxis = QValueAxis()
        self.yAxis.setTitleText("Sin")
        self.yAxis.setRange(-1, 1)

        self.chart = QChart()
        self.chart.addAxis(self.xAxis, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.yAxis, Qt.AlignmentFlag.AlignLeft)

        self.chart.setTitle("Title")
        
        self.serie = QLineSeries()
        self.serie.setName("SIN")

        self.alpha = 0

        self.chart.addSeries(self.serie)
        self.serie.attachAxis(self.xAxis)
        self.serie.attachAxis(self.yAxis)

        self.chartView = QChartView(self.chart)
        self.chartView.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ===== Central widget =====
        centralWidget = QWidget()
        centralLayout = QVBoxLayout(centralWidget)

        centralLayout.addWidget(self.chartView)

        self.setCentralWidget(centralWidget)

        # ===== Refreshing timer =====
        self.refreshTimer = QTimer(self)
        self.refreshTimer.timeout.connect(self.refreshData)
        self.refreshTimer.start(25)
    
    def refreshData(self):
        if (self.alpha < 2*np.pi):
            self.xAxis.setRange(0, 2*np.pi)

            self.serie.append(self.alpha, np.sin(self.alpha))
        else:
            self.xAxis.setRange(self.alpha - 2*np.pi, self.alpha)

            self.serie.replace(self.serie.pointsVector()[1:])
            self.serie.append(self.alpha, np.sin(self.alpha))
        
        self.alpha += 0.03

if __name__=="__main__":
    app = QApplication(sys.argv)

    setupToolApp = SetupToolApp()
    setupToolApp.show()

    app.exec()