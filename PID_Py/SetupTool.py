import sys

from PySide6 import QtGui
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QDoubleSpinBox, QLabel, QFrame, QCheckBox, QTimeEdit
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
        self.parametersLayout.addRow(gainLabel)
        self.parametersLayout.addRow("Kp", self.kpSpinBox)
        self.parametersLayout.addRow("Ki", self.kiSpinBox)
        self.parametersLayout.addRow("Kd", self.kdSpinBox)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Raised)
        self.parametersLayout.addRow(separator)

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
        self.parametersLayout.addRow(parametersLabel)
        self.parametersLayout.addRow(self.indirectActionCheckBox)
        self.parametersLayout.addRow(self.proportionnalOnMeasurementCheckBox)
        self.parametersLayout.addRow(self.integralLimitEnableCheckBox, self.integralLimitSpinBox)
        self.parametersLayout.addRow(self.derivativeOnMeasurementCheckBox)
        self.parametersLayout.addRow(self.setpointRampEnableCheckBox, self.setpointRampSpinBox)
        self.parametersLayout.addRow(self.setpointStableLimitEnableCheckBox, self.setpointStableLimitSpinBox)
        self.parametersLayout.addRow("      Setpoint stable time", self.setpointStableTimeTimeEdit)
        self.parametersLayout.addRow(self.deadbandEnableCheckBox, self.deadbandSpinBox)
        self.parametersLayout.addRow("      Deadband activatio time", self.deadbandActivationTimeTimeEdit)
        self.parametersLayout.addRow(self.processValueStableLimitEnableCheckBox, self.processValueStableLimitSpinBox)
        self.parametersLayout.addRow("      Process value stable time", self.processValueStableTimeTimeEdit)

        outputLimitLabel = QLabel("Output limits")
        outputLimitLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        outputLimitLabel.setStyleSheet("font-size: 24px")
        self.parametersLayout.addRow(outputLimitLabel)
        self.parametersLayout.addRow(self.outputLimitMaxEnableCheckBox, self.outputLimitMaxSpinBox)
        self.parametersLayout.addRow(self.outputLimitMinEnableCheckBox, self.outputLimitMinSpinBox)


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