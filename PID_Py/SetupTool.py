import sys

from PySide6 import QtGui
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QDoubleSpinBox
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFormLayout
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis    
from PySide6.QtCore import QTimer, Qt

import numpy as np

class SetupToolApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        
        self.setWindowTitle("PID_Py : SetupTool")
        self.setMinimumSize(1000, 600)

        # ===== Real-time graph ====
        # TODO: Store data in a list of QPointF, and use replace to update points in the chart
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

        # ===== Parameters =====
        self.parametersWidget = QWidget()
        self.parametersLayout = QFormLayout(self.parametersWidget)

        # Kp, ki and kd
        self.kpSpinBox = QDoubleSpinBox()
        self.kpSpinBox.setEnabled(False)
        self.kpSpinBox.setSingleStep(0.1)
        self.kpSpinBox.setDecimals(2)
        self.kpSpinBox.setMinimum(0.0)
        self.kpSpinBox.setToolTip("Proportionnal gain")
        self.kpSpinBox.setToolTipDuration(5000)

        self.kiSpinBox = QDoubleSpinBox()
        self.kiSpinBox.setEnabled(False)

        self.kdSpinBox = QDoubleSpinBox()
        self.kdSpinBox.setEnabled(False)

        self.parametersLayout.addRow("Kp", self.kpSpinBox)
        self.parametersLayout.addRow("Ki", self.kiSpinBox)
        self.parametersLayout.addRow("Kd", self.kdSpinBox)


        # ===== Central widget =====
        centralWidget = QWidget()
        centralLayout = QHBoxLayout(centralWidget)

        centralLayout.addWidget(self.chartView)
        centralLayout.addWidget(self.parametersWidget)

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