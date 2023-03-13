import sys

from PySide6 import QtGui
from PySide6.QtGui import QPainter, QActionGroup
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QDoubleSpinBox, QLabel, QFrame, QCheckBox, QTimeEdit, QScrollArea, QMenuBar, QMenu
from PySide6.QtWidgets import QHBoxLayout, QGridLayout
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis    
from PySide6.QtCore import QTimer, Qt

import logging

import numpy as np

class SetupToolApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)

        logFormat = logging.Formatter('%(levelname)s [%(name)s]: %(message)s')
        handler.setFormatter(logFormat)

        self.logger.addHandler(handler)
        
        self.setWindowTitle("PID_Py : SetupTool")
        self.setMinimumSize(1000, 300)

        # ===== Menu bar =====
        self.setMenuBar(QMenuBar())

        menuReadWrite = QMenu("Read/Write")

        readWriteGroup = QActionGroup(self)
        readWriteGroup.setExclusive(True)
        readAction = readWriteGroup.addAction("Read")
        readAction.setCheckable(True)
        readAction.setChecked(True)
        readAction.triggered.connect(self.setReadOnlyMode)

        writeAction = readWriteGroup.addAction("Write")
        writeAction.setCheckable(True)
        writeAction.triggered.connect(self.setReadWriteMode)

        menuReadWrite.addAction(readAction)
        menuReadWrite.addAction(writeAction)

        self.menuBar().addMenu(menuReadWrite)

        # ===== Status bar =====
        self.readWriteLabel = QLabel("Read-only mode")
        self.statusBar().addPermanentWidget(self.readWriteLabel)

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
        self.parametersScrollArea = QScrollArea()
        self.parametersScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.parametersScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.parametersScrollArea.setMinimumWidth(350)

        self.parametersWidget = QWidget()

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
        self.kpLabel = QLabel("Proportionnal")
        self.kpLabel.setEnabled(False)

        self.kpSpinBox.valueChanged.connect(self.kpChanged)

        self.kiSpinBox = QDoubleSpinBox()
        self.kiSpinBox.setEnabled(False)
        self.kiSpinBox.setSingleStep(0.1)
        self.kiSpinBox.setDecimals(3)
        self.kiSpinBox.setMinimum(0.0)
        self.kiSpinBox.setToolTip("Integral gain")
        self.kiSpinBox.setToolTipDuration(5000)
        self.kiLabel = QLabel("Integral")
        self.kiLabel.setEnabled(False)

        self.kdSpinBox = QDoubleSpinBox()
        self.kdSpinBox.setEnabled(False)
        self.kdSpinBox.setSingleStep(0.1)
        self.kdSpinBox.setDecimals(3)
        self.kdSpinBox.setMinimum(0.0)
        self.kdSpinBox.setToolTip("Derivative gain")
        self.kdSpinBox.setToolTipDuration(5000)
        self.kdLabel = QLabel("Derivative")
        self.kdLabel.setEnabled(False)

        gainLabel = QLabel("Gains")
        gainLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        gainLabel.setStyleSheet("font-size: 24px")

        self.parametersLayout.addWidget(gainLabel, 0, 0, 1, 3)

        self.parametersLayout.addWidget(self.kpLabel, 1, 1)
        self.parametersLayout.addWidget(self.kpSpinBox, 1, 2)

        self.parametersLayout.addWidget(self.kiLabel, 2, 1)
        self.parametersLayout.addWidget(self.kiSpinBox, 2, 2)

        self.parametersLayout.addWidget(self.kdLabel, 3, 1)
        self.parametersLayout.addWidget(self.kdSpinBox, 3, 2)
        
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setFrameShadow(QFrame.Shadow.Raised)

        self.parametersLayout.addWidget(separator1, 4, 0, 1, 3)

        # Parameters
        self.indirectActionCheckBox = QCheckBox("Indirect action")
        self.indirectActionCheckBox.setEnabled(False)
        self.indirectActionCheckBox.setToolTip("Invert PID action")
        self.indirectActionCheckBox.setToolTipDuration(5000)

        self.proportionnalOnMeasurementCheckBox = QCheckBox("Proportionnal on measurement")
        self.proportionnalOnMeasurementCheckBox.setEnabled(False)
        self.proportionnalOnMeasurementCheckBox.setToolTip("Calculate the proportionnal term on the process value")
        self.proportionnalOnMeasurementCheckBox.setToolTipDuration(5000)

        self.integralLimitEnableCheckBox = QCheckBox("Integral limit")
        self.integralLimitEnableCheckBox.setEnabled(False)
        self.integralLimitEnableCheckBox.setToolTip("Clamp integral term between [-value, value]")
        self.integralLimitEnableCheckBox.setToolTipDuration(5000)
        self.integralLimitSpinBox = QDoubleSpinBox()
        self.integralLimitSpinBox.setEnabled(False)
        self.integralLimitSpinBox.setToolTip("Clamp integral term between [-value, value]")
        self.integralLimitSpinBox.setToolTipDuration(5000)

        self.derivativeOnMeasurementCheckBox = QCheckBox("Derivative on measurement")
        self.derivativeOnMeasurementCheckBox.setEnabled(False)
        self.derivativeOnMeasurementCheckBox.setToolTip("Calculate the derivative term on the process value")
        self.derivativeOnMeasurementCheckBox.setToolTipDuration(5000)

        self.setpointRampEnableCheckBox = QCheckBox("Setpoint ramp")
        self.setpointRampEnableCheckBox.setEnabled(False)
        self.setpointRampEnableCheckBox.setToolTip("Apply a ramp on the setpoint (unit/s)")
        self.setpointRampEnableCheckBox.setToolTipDuration(5000)
        self.setpointRampSpinBox = QDoubleSpinBox()
        self.setpointRampSpinBox.setEnabled(False)
        self.setpointRampSpinBox.setToolTip("Apply a ramp on the setpoint (unit/s)")
        self.setpointRampSpinBox.setToolTipDuration(5000)

        self.setpointStableLimitEnableCheckBox = QCheckBox("Setpoint stable")
        self.setpointStableLimitEnableCheckBox.setEnabled(False)
        self.setpointStableLimitEnableCheckBox.setToolTip("Maximum difference between the setpoint and the process value to be considered reached")
        self.setpointStableLimitEnableCheckBox.setToolTipDuration(5000)
        self.setpointStableLimitSpinBox = QDoubleSpinBox()
        self.setpointStableLimitSpinBox.setEnabled(False)
        self.setpointStableLimitSpinBox.setToolTip("Maximum difference between the setpoint and the process value to be considered reached")
        self.setpointStableLimitSpinBox.setToolTipDuration(5000)

        self.setpointStableTimeLabel = QLabel("Setpoint stable time")
        self.setpointStableTimeLabel.setEnabled(False)
        self.setpointStableTimeLabel.setToolTip("Maximum difference between the setpoint and the process value to be considered reached")
        self.setpointStableTimeLabel.setToolTipDuration(5000)
        self.setpointStableTimeTimeEdit = QTimeEdit()
        self.setpointStableTimeTimeEdit.setEnabled(False)
        self.setpointStableTimeTimeEdit.setToolTip("Maximum difference between the setpoint and the process value to be considered reached")
        self.setpointStableTimeTimeEdit.setToolTipDuration(5000)
        self.setpointStableTimeTimeEdit.setDisplayFormat("hh:mm:ss")
        self.setpointStableTimeTimeEdit.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)

        self.deadbandEnableCheckBox = QCheckBox("Deadband")
        self.deadbandEnableCheckBox.setEnabled(False)
        self.deadbandEnableCheckBox.setToolTip("The minimum amount of output variation to applied this variation")
        self.deadbandEnableCheckBox.setToolTipDuration(5000)
        self.deadbandSpinBox = QDoubleSpinBox()
        self.deadbandSpinBox.setEnabled(False)
        self.deadbandSpinBox.setToolTip("The minimum amount of output variation to applied this variation")
        self.deadbandSpinBox.setToolTipDuration(5000)

        self.deadbandActivationTimeLabel = QLabel("Deadband activation time")
        self.deadbandActivationTimeLabel.setEnabled(False)
        self.deadbandActivationTimeLabel.setToolTip("The minimum amount of output variation to applied this variation")
        self.deadbandActivationTimeLabel.setToolTipDuration(5000)
        self.deadbandActivationTimeTimeEdit = QTimeEdit()
        self.deadbandActivationTimeTimeEdit.setEnabled(False)
        self.deadbandActivationTimeTimeEdit.setToolTip("The minimum amount of output variation to applied this variation")
        self.deadbandActivationTimeTimeEdit.setToolTipDuration(5000)
        self.deadbandActivationTimeTimeEdit.setDisplayFormat("hh:mm:ss")
        self.deadbandActivationTimeTimeEdit.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)

        self.processValueStableLimitEnableCheckBox = QCheckBox("Process value stable")
        self.processValueStableLimitEnableCheckBox.setEnabled(False)
        self.processValueStableLimitEnableCheckBox.setToolTip("The maximum variation of the process value to be considered stable")
        self.processValueStableLimitEnableCheckBox.setToolTipDuration(5000)
        self.processValueStableLimitSpinBox = QDoubleSpinBox()
        self.processValueStableLimitSpinBox.setEnabled(False)
        self.processValueStableLimitSpinBox.setToolTip("The maximum variation of the process value to be considered stable")
        self.processValueStableLimitSpinBox.setToolTipDuration(5000)

        self.processValueStableTimeLabel = QLabel("Process value stable time")
        self.processValueStableTimeLabel.setEnabled(False)
        self.processValueStableTimeLabel.setToolTip("The maximum variation of the process value to be considered stable")
        self.processValueStableTimeLabel.setToolTipDuration(5000)
        self.processValueStableTimeTimeEdit = QTimeEdit()
        self.processValueStableTimeTimeEdit.setEnabled(False)
        self.processValueStableTimeTimeEdit.setToolTip("The maximum variation of the process value to be considered stable")
        self.processValueStableTimeTimeEdit.setToolTipDuration(5000)
        self.processValueStableTimeTimeEdit.setDisplayFormat("hh:mm:ss")
        self.processValueStableTimeTimeEdit.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)

        self.outputLimitMaxEnableCheckBox = QCheckBox("Maximum")
        self.outputLimitMaxEnableCheckBox.setEnabled(False)
        self.outputLimitMaxEnableCheckBox.setToolTip("Maximum output")
        self.outputLimitMaxEnableCheckBox.setToolTipDuration(5000)
        self.outputLimitMaxSpinBox = QDoubleSpinBox()
        self.outputLimitMaxSpinBox.setEnabled(False)
        self.outputLimitMaxSpinBox.setToolTip("Maximum output")
        self.outputLimitMaxSpinBox.setToolTipDuration(5000)

        self.outputLimitMinEnableCheckBox = QCheckBox("Minimum")
        self.outputLimitMinEnableCheckBox.setEnabled(False)
        self.outputLimitMinEnableCheckBox.setToolTip("Minimum output")
        self.outputLimitMinEnableCheckBox.setToolTipDuration(5000)
        self.outputLimitMinSpinBox = QDoubleSpinBox()
        self.outputLimitMinSpinBox.setEnabled(False)
        self.outputLimitMinSpinBox.setToolTip("Minimum output")
        self.outputLimitMinSpinBox.setToolTipDuration(5000)

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
        self.parametersLayout.addWidget(self.setpointStableTimeLabel, 12, 1)
        self.parametersLayout.addWidget(self.setpointStableTimeTimeEdit, 12, 2)

        self.parametersLayout.addWidget(self.deadbandEnableCheckBox, 13, 0, 1, 2)
        self.parametersLayout.addWidget(self.deadbandSpinBox, 13, 2)
        self.parametersLayout.addWidget(self.deadbandActivationTimeLabel, 14, 1)
        self.parametersLayout.addWidget(self.deadbandActivationTimeTimeEdit, 14, 2)

        self.parametersLayout.addWidget(self.processValueStableLimitEnableCheckBox, 15, 0, 1, 2)
        self.parametersLayout.addWidget(self.processValueStableLimitSpinBox, 15, 2)
        self.parametersLayout.addWidget(self.processValueStableTimeLabel, 16, 1)
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

        # ===== Central widget =====
        centralWidget = QWidget()
        centralLayout = QHBoxLayout(centralWidget)

        centralLayout.addWidget(self.chartView)

        self.parametersScrollArea.setWidget(self.parametersWidget)
        centralLayout.addWidget(self.parametersScrollArea)

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
    
    def enableWidgets(self):
        self.kpLabel.setEnabled(True)
        self.kpSpinBox.setEnabled(True)

        self.kiLabel.setEnabled(True)
        self.kiSpinBox.setEnabled(True)

        self.kdLabel.setEnabled(True)
        self.kdSpinBox.setEnabled(True)

        self.indirectActionCheckBox.setEnabled(True)

        self.proportionnalOnMeasurementCheckBox.setEnabled(True)

        self.integralLimitEnableCheckBox.setEnabled(True)
        self.integralLimitSpinBox.setEnabled(self.integralLimitEnableCheckBox.checkState() == Qt.CheckState.Checked)

        self.derivativeOnMeasurementCheckBox.setEnabled(True)

        self.setpointRampEnableCheckBox.setEnabled(True)
        self.setpointRampSpinBox.setEnabled(self.setpointRampEnableCheckBox.checkState == Qt.CheckState.Checked)

        self.setpointStableLimitEnableCheckBox.setEnabled(True)
        self.setpointStableLimitSpinBox.setEnabled(self.setpointStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked)
        self.setpointStableTimeLabel.setEnabled(self.setpointStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked)
        self.setpointStableTimeTimeEdit.setEnabled(self.setpointStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked)

        self.deadbandEnableCheckBox.setEnabled(True)
        self.deadbandSpinBox.setEnabled(self.deadbandEnableCheckBox.checkState() == Qt.CheckState.Checked)
        self.deadbandActivationTimeLabel.setEnabled(self.deadbandEnableCheckBox.checkState() == Qt.CheckState.Checked)
        self.deadbandActivationTimeTimeEdit.setEnabled(self.deadbandEnableCheckBox.checkState() == Qt.CheckState.Checked)

        self.processValueStableLimitEnableCheckBox.setEnabled(True)
        self.processValueStableLimitSpinBox.setEnabled(self.processValueStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked)
        self.processValueStableTimeLabel.setEnabled(self.processValueStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked)
        self.processValueStableTimeTimeEdit.setEnabled(self.processValueStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked)

        self.outputLimitMaxEnableCheckBox.setEnabled(True)
        self.outputLimitMaxSpinBox.setEnabled(self.outputLimitMaxEnableCheckBox.checkState() == Qt.CheckState.Checked)
        self.outputLimitMinEnableCheckBox.setEnabled(True)
        self.outputLimitMinSpinBox.setEnabled(self.outputLimitMinEnableCheckBox.checkState() == Qt.CheckState.Checked)

    def disableWidgets(self):
        self.kpLabel.setEnabled(False)
        self.kpSpinBox.setEnabled(False)

        self.kiLabel.setEnabled(False)
        self.kiSpinBox.setEnabled(False)

        self.kdLabel.setEnabled(False)
        self.kdSpinBox.setEnabled(False)

        self.indirectActionCheckBox.setEnabled(False)

        self.proportionnalOnMeasurementCheckBox.setEnabled(False)

        self.integralLimitEnableCheckBox.setEnabled(False)
        self.integralLimitSpinBox.setEnabled(False)

        self.derivativeOnMeasurementCheckBox.setEnabled(False)

        self.setpointRampEnableCheckBox.setEnabled(False)
        self.setpointRampSpinBox.setEnabled(False)

        self.setpointStableLimitEnableCheckBox.setEnabled(False)
        self.setpointStableLimitSpinBox.setEnabled(False)
        self.setpointStableTimeLabel.setEnabled(False)
        self.setpointStableTimeTimeEdit.setEnabled(False)

        self.deadbandEnableCheckBox.setEnabled(False)
        self.deadbandSpinBox.setEnabled(False)
        self.deadbandActivationTimeLabel.setEnabled(False)
        self.deadbandActivationTimeTimeEdit.setEnabled(False)

        self.processValueStableLimitEnableCheckBox.setEnabled(False)
        self.processValueStableLimitSpinBox.setEnabled(False)
        self.processValueStableTimeLabel.setEnabled(False)
        self.processValueStableTimeTimeEdit.setEnabled(False)

        self.outputLimitMaxEnableCheckBox.setEnabled(False)
        self.outputLimitMaxSpinBox.setEnabled(False)
        self.outputLimitMinEnableCheckBox.setEnabled(False)
        self.outputLimitMinSpinBox.setEnabled(False)
    
    def kpChanged(self, value):
        self.logger.info("Kp value changed")
        print("msg")

    def setReadOnlyMode(self):
        self.readWriteLabel.setText("Read-only mode")
        self.disableWidgets()

        for w in self.widgets:
            w.setEnabled(False)

    def setReadWriteMode(self):
        self.readWriteLabel.setText("Read/write mode")
        self.enableWidgets()

        for w in self.widgets:
            w.setEnabled(False)

if __name__=="__main__":
    app = QApplication(sys.argv)

    setupToolApp = SetupToolApp()
    setupToolApp.show()

    app.exec()