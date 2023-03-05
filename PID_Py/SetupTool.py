import sys

from PySide6 import QtGui
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
from PySide6.QtCharts import QChart, QChartView, QLineSeries


import numpy as np

class SetupToolApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        
        self.setWindowTitle("PID_Py : SetupTool")
        self.setFixedSize(1000, 600)

        # ===== Real-time graph ====
        self.serie = QLineSeries()
        x = np.linspace(-np.pi, np.pi, 200)
        self.serie.appendNp(x, np.sin(x))

        self.serie.setName("SIN")

        self.chart = QChart()
        self.chart.addSeries(self.serie)
        self.chart.createDefaultAxes()
        self.chart.setTitle("Title")

        self.chartView = QChartView(self.chart)
        self.chartView.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ===== Central widget =====
        centralWidget = QWidget()
        centralLayout = QVBoxLayout(centralWidget)

        centralLayout.addWidget(self.chartView)

        self.setCentralWidget(centralWidget)

if __name__=="__main__":
    app = QApplication(sys.argv)

    setupToolApp = SetupToolApp()
    setupToolApp.show()

    app.exec()