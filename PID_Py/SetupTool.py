import sys

from PySide6 import QtGui
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QDoubleSpinBox, QLabel, QFrame, QCheckBox, QTimeEdit, QScrollArea
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis    
from PySide6.QtCore import QTimer, Qt

import numpy as np

class SetupToolApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        
        self.setWindowTitle("PID_Py : SetupTool")
        self.setMinimumSize(1000, 300)

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
        self.parametersWidget = QScrollArea()
        self.parametersWidget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.parametersWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.parametersWidget.setMinimumWidth(340)

        self.parametersLayout = QGridLayout(self.parametersWidget)
        self.parametersLayout.setColumnStretch(0, 0)
        self.parametersLayout.setColumnMinimumWidth(0, 13)
        self.parametersLayout.setColumnStretch(1, 3)
        self.parametersLayout.setColumnStretch(2, 1)

        # Gains (Kp, ki and kd)
        self.kpSpinBox = QDoubleSpinBox()
        self.kpSpinBox.setEnabled(False)
        self.kpSpinBox.setSingleStep(0.1)
        self.kpSpinBox.setDecimals(3)
        self.kpSpinBox.setMinimum(0.0)
        self.kpSpinBox.setToolTip("Proportionnal gain")
        self.kpSpinBox.setToolTipDuration(5000)

        self.kiSpinBox = QDoubleSpinBox()
        self.kiSpinBox.setEnabled(False)
        self.kiSpinBox.setSingleStep(0.1)
        self.kiSpinBox.setDecimals(3)
        self.kiSpinBox.setMinimum(0.0)
        self.kiSpinBox.setToolTip("Integral gain")
        self.kiSpinBox.setToolTipDuration(5000)

        self.kdSpinBox = QDoubleSpinBox()
        self.kdSpinBox.setEnabled(False)
        self.kdSpinBox.setSingleStep(0.1)
        self.kdSpinBox.setDecimals(3)
        self.kdSpinBox.setMinimum(0.0)
        self.kdSpinBox.setToolTip("Derivative gain")
        self.kdSpinBox.setToolTipDuration(5000)

        gainLabel = QLabel("Gains")
        gainLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        gainLabel.setStyleSheet("font-size: 24px")

        self.parametersLayout.addWidget(gainLabel, 0, 0, 1, 3)

        self.parametersLayout.addWidget(QLabel("Proportionnal"), 1, 1)
        self.parametersLayout.addWidget(self.kpSpinBox, 1, 2)

        self.parametersLayout.addWidget(QLabel("Integral"), 2, 1)
        self.parametersLayout.addWidget(self.kiSpinBox, 2, 2)

        self.parametersLayout.addWidget(QLabel("Derivative"), 3, 1)
        self.parametersLayout.addWidget(self.kdSpinBox, 3, 2)
        
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setFrameShadow(QFrame.Shadow.Raised)

        self.parametersLayout.addWidget(separator1, 4, 0, 1, 3)

        # Parameters
        self.indirectActionCheckBox = QCheckBox("Indirect action")

        self.proportionnalOnMeasurementCheckBox = QCheckBox("Proportionnal on measurement")

        self.integralLimitEnableCheckBox = QCheckBox("Integral limit")
        self.integralLimitSpinBox = QDoubleSpinBox()

        self.derivativeOnMeasurementCheckBox = QCheckBox("Derivative on measurement")

        self.setpointRampEnableCheckBox = QCheckBox("Setpoint ramp")
        self.setpointRampSpinBox = QDoubleSpinBox()

        self.setpointStableLimitEnableCheckBox = QCheckBox("Setpoint stable")
        self.setpointStableLimitSpinBox = QDoubleSpinBox()
        self.setpointStableTimeTimeEdit = QTimeEdit()

        self.deadbandEnableCheckBox = QCheckBox("Deadband")
        self.deadbandSpinBox = QDoubleSpinBox()
        self.deadbandActivationTimeTimeEdit = QTimeEdit()

        self.processValueStableLimitEnableCheckBox = QCheckBox("Process value stable")
        self.processValueStableLimitSpinBox = QDoubleSpinBox()
        self.processValueStableTimeTimeEdit = QTimeEdit()

        self.outputLimitMaxEnableCheckBox = QCheckBox("Maximum")
        self.outputLimitMaxSpinBox = QDoubleSpinBox()

        self.outputLimitMinEnableCheckBox = QCheckBox("Minimum")
        self.outputLimitMinSpinBox = QDoubleSpinBox()

        parametersLabel = QLabel("Parameters")
        parametersLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        parametersLabel.setStyleSheet("font-size: 24px")

        self.parametersLayout.addWidget(parametersLabel, 5, 0, 1 ,3)

        self.parametersLayout.addWidget(self.indirectActionCheckBox, 6, 0, 1, 2)

        self.parametersLayout.addWidget(self.proportionnalOnMeasurementCheckBox, 7, 0, 1, 2)

        self.parametersLayout.addWidget(self.integralLimitEnableCheckBox, 8, 0, 1, 2)
        self.parametersLayout.addWidget(self.integralLimitSpinBox, 8, 2)

        self.parametersLayout.addWidget(self.derivativeOnMeasurementCheckBox, 9, 0, 1, 2)

        self.parametersLayout.addWidget(self.setpointRampEnableCheckBox, 10, 0, 1, 2)
        self.parametersLayout.addWidget(self.setpointRampSpinBox, 10, 2)

        self.parametersLayout.addWidget(self.setpointStableLimitEnableCheckBox, 11, 0, 1, 2)
        self.parametersLayout.addWidget(self.setpointStableLimitSpinBox, 11, 2)
        self.parametersLayout.addWidget(QLabel("Setpoint stable time"), 12, 1)
        self.parametersLayout.addWidget(self.setpointStableTimeTimeEdit, 12, 2)

        self.parametersLayout.addWidget(self.deadbandEnableCheckBox, 13, 0, 1, 2)
        self.parametersLayout.addWidget(self.deadbandSpinBox, 13, 2)
        self.parametersLayout.addWidget(QLabel("Deadband activation time"), 14, 1)
        self.parametersLayout.addWidget(self.deadbandActivationTimeTimeEdit, 14, 2)

        self.parametersLayout.addWidget(self.processValueStableLimitEnableCheckBox, 15, 0, 1, 2)
        self.parametersLayout.addWidget(self.processValueStableLimitSpinBox, 15, 2)
        self.parametersLayout.addWidget(QLabel("Process value stable time"), 16, 1)
        self.parametersLayout.addWidget(self.processValueStableTimeTimeEdit, 16, 2)

        # Output limits
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Raised)

        self.parametersLayout.addWidget(separator2, 17, 0, 1, 3)

        outputLimitLabel = QLabel("Output limits")
        outputLimitLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        outputLimitLabel.setStyleSheet("font-size: 24px")

        self.parametersLayout.addWidget(outputLimitLabel, 18, 0, 1, 3)

        self.parametersLayout.addWidget(self.outputLimitMaxEnableCheckBox, 19, 0, 1, 2)
        self.parametersLayout.addWidget(self.outputLimitMaxSpinBox, 19, 2)

        self.parametersLayout.addWidget(self.outputLimitMinEnableCheckBox, 20, 0, 1, 2)
        self.parametersLayout.addWidget(self.outputLimitMinSpinBox, 20, 2)

        self.parametersLayout.setRowStretch(21, 1)

        # ===== Central widget =====
        centralWidget = QWidget()
        centralLayout = QHBoxLayout(centralWidget)

        centralLayout.addWidget(self.chartView)
        centralLayout.addWidget(self.parametersWidget)
        centralLayout.setStretch(0, 3)
        centralLayout.setStretch(1, 1)

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