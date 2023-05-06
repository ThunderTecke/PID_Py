import sys

from PySide6.QtGui import QPainter, QActionGroup
from PySide6.QtWidgets import QMainWindow, QWidget, QDoubleSpinBox, QLabel, QFrame, QCheckBox, QTimeEdit, QScrollArea, QMenuBar, QMenu, QMessageBox, QPushButton
from PySide6.QtWidgets import QHBoxLayout, QGridLayout
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QTimer, Qt, QTime, QPointF

import logging

from PID_Py.PID import PID

class SetupToolApp(QMainWindow):
    """
    SetupTool application class

    Parameters
    ----------
    pid: PID_Py.PID.PID
        The monitored PID
    """
    def __init__(self, pid: PID) -> None:
        super().__init__()

        self.pid = pid
        self.pid._setuptoolControl = False

        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        logFormat = logging.Formatter('%(name)s [%(levelname)s]: %(message)s')
        handler.setFormatter(logFormat)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(handler)

        self.logger.debug("Logger initialized")
        
        self.setWindowTitle("PID_Py : SetupTool")
        self.setMinimumSize(1000, 300)

        # ===== Menu bar =====
        self.setMenuBar(QMenuBar())

        menuControl = QMenu("Control")

        controlGroup = QActionGroup(self)
        controlGroup.setExclusive(True)
        self.releaseControlAction = controlGroup.addAction("Control released")
        self.releaseControlAction.setCheckable(True)
        self.releaseControlAction.setChecked(True)
        self.releaseControlAction.triggered.connect(self.releaseControl)

        self.takeControlAction = controlGroup.addAction("Control taken")
        self.takeControlAction.setCheckable(True)
        self.takeControlAction.triggered.connect(self.takeControl)

        menuControl.addAction(self.releaseControlAction)
        menuControl.addAction(self.takeControlAction)

        menuParameters = QMenu("Parameters")

        parametersGroup = QActionGroup(self)
        parametersGroup.setExclusive(True)
        self.readAction = parametersGroup.addAction("Read")
        self.readAction.setCheckable(True)
        self.readAction.setChecked(True)
        self.readAction.triggered.connect(self.setReadOnlyMode)

        self.writeAction = parametersGroup.addAction("Write")
        self.writeAction.setCheckable(True)
        self.writeAction.triggered.connect(self.setReadWriteMode)

        menuParameters.addAction(self.readAction)
        menuParameters.addAction(self.writeAction)

        self.menuBar().addMenu(menuControl)
        self.menuBar().addMenu(menuParameters)

        # ===== Status bar =====
        self.readWriteLabel = QLabel("Read-only mode")
        self.controlLabel = QLabel("Control released")
        self.statusBar().addPermanentWidget(self.readWriteLabel)

        statusSeparator = QFrame()
        statusSeparator.setFrameShape(QFrame.Shape.VLine)
        statusSeparator.setFrameShadow(QFrame.Shadow.Raised)
        statusSeparator.setFixedHeight(20)

        self.statusBar().addPermanentWidget(statusSeparator)
        self.statusBar().addPermanentWidget(self.controlLabel)

        # ===== Real-time graph ====
        self.historianMaxNbPoint = 3000

        self.xAxis = QValueAxis()
        self.xAxis.setTitleText("Time (s)")
        self.xAxis.setRange(0, 60)

        self.yAxis = QValueAxis()
        self.yAxis.setRange(0, 10)

        self.chart = QChart()
        self.chart.addAxis(self.xAxis, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.yAxis, Qt.AlignmentFlag.AlignLeft)

        self.chart.setTitle("Historian")

        self.series = {}
        self.seriesData = {}

        for k in self.pid.historian.keys():
            if k != "TIME":
                self.series[k] = QLineSeries()
                self.series[k].setName(k)

                self.chart.addSeries(self.series[k])

                self.series[k].attachAxis(self.xAxis)
                self.series[k].attachAxis(self.yAxis)

                self.seriesData[k] = []

        self.lastTime = None

        self.chartView = QChartView(self.chart)
        self.chartView.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ===== Parameters =====
        self.parametersScrollArea = QScrollArea()
        self.parametersScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.parametersScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.parametersScrollArea.setFixedWidth(370)

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
        self.kpSpinBox.setValue(self.pid.kp)
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
        self.kiSpinBox.setValue(self.pid.ki)
        self.kiLabel = QLabel("Integral")
        self.kiLabel.setEnabled(False)

        self.kiSpinBox.valueChanged.connect(self.kiChanged)

        self.kdSpinBox = QDoubleSpinBox()
        self.kdSpinBox.setEnabled(False)
        self.kdSpinBox.setSingleStep(0.1)
        self.kdSpinBox.setDecimals(3)
        self.kdSpinBox.setMinimum(0.0)
        self.kdSpinBox.setToolTip("Derivative gain")
        self.kdSpinBox.setToolTipDuration(5000)
        self.kdSpinBox.setValue(self.pid.kd)
        self.kdLabel = QLabel("Derivative")
        self.kdLabel.setEnabled(False)

        self.kdSpinBox.valueChanged.connect(self.kdChanged)

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
        self.indirectActionCheckBox.setCheckState(Qt.CheckState.Checked if self.pid.indirectAction else Qt.CheckState.Unchecked)

        self.indirectActionCheckBox.stateChanged.connect(self.indirectActionChanged)

        self.proportionnalOnMeasurementCheckBox = QCheckBox("Proportionnal on measurement")
        self.proportionnalOnMeasurementCheckBox.setEnabled(False)
        self.proportionnalOnMeasurementCheckBox.setToolTip("Calculate the proportionnal term on the process value")
        self.proportionnalOnMeasurementCheckBox.setToolTipDuration(5000)
        self.proportionnalOnMeasurementCheckBox.setCheckState(Qt.CheckState.Checked if self.pid.proportionnalOnMeasurement else Qt.CheckState.Unchecked)

        self.proportionnalOnMeasurementCheckBox.stateChanged.connect(self.proportionnalOnMeasurementChanged)

        self.integralLimitEnableCheckBox = QCheckBox("Integral limit")
        self.integralLimitEnableCheckBox.setEnabled(False)
        self.integralLimitEnableCheckBox.setToolTip("Clamp integral term between [-value, value]")
        self.integralLimitEnableCheckBox.setToolTipDuration(5000)
        self.integralLimitEnableCheckBox.setCheckState(Qt.CheckState.Checked if self.pid.integralLimit is not None else Qt.CheckState.Unchecked)
        self.integralLimitEnableCheckBox.stateChanged.connect(self.integralLimitEnableChanged)

        self.integralLimitSpinBox = QDoubleSpinBox()
        self.integralLimitSpinBox.setEnabled(False)
        self.integralLimitSpinBox.setToolTip("Clamp integral term between [-value, value]")
        self.integralLimitSpinBox.setToolTipDuration(5000)
        self.integralLimitSpinBox.setValue(self.pid.integralLimit if self.pid.integralLimit is not None else 0)
        self.integralLimitSpinBox.valueChanged.connect(self.integralLimitChanged)

        self.derivativeOnMeasurementCheckBox = QCheckBox("Derivative on measurement")
        self.derivativeOnMeasurementCheckBox.setEnabled(False)
        self.derivativeOnMeasurementCheckBox.setToolTip("Calculate the derivative term on the process value")
        self.derivativeOnMeasurementCheckBox.setToolTipDuration(5000)
        self.derivativeOnMeasurementCheckBox.setCheckState(Qt.CheckState.Checked if self.pid.derivativeOnMeasurement else Qt.CheckState.Unchecked)
        self.derivativeOnMeasurementCheckBox.stateChanged.connect(self.derivativeOnMeasurementChanged)

        self.setpointRampEnableCheckBox = QCheckBox("Setpoint ramp")
        self.setpointRampEnableCheckBox.setEnabled(False)
        self.setpointRampEnableCheckBox.setToolTip("Apply a ramp on the setpoint (unit/s)")
        self.setpointRampEnableCheckBox.setToolTipDuration(5000)
        self.setpointRampEnableCheckBox.setCheckState(Qt.CheckState.Checked if self.pid.setpointRamp is not None else Qt.CheckState.Unchecked)
        self.setpointRampEnableCheckBox.stateChanged.connect(self.setpointRampEnableChanged)

        self.setpointRampSpinBox = QDoubleSpinBox()
        self.setpointRampSpinBox.setEnabled(False)
        self.setpointRampSpinBox.setToolTip("Apply a ramp on the setpoint (unit/s)")
        self.setpointRampSpinBox.setToolTipDuration(5000)
        self.setpointRampSpinBox.setValue(self.pid.setpointRamp if self.pid.setpointRamp is not None else 0)
        self.setpointRampSpinBox.valueChanged.connect(self.setpointRampChanged)

        self.setpointStableLimitEnableCheckBox = QCheckBox("Setpoint stable")
        self.setpointStableLimitEnableCheckBox.setEnabled(False)
        self.setpointStableLimitEnableCheckBox.setToolTip("Maximum difference between the setpoint and the process value to be considered reached")
        self.setpointStableLimitEnableCheckBox.setToolTipDuration(5000)
        self.setpointStableLimitEnableCheckBox.setCheckState(Qt.CheckState.Checked if self.pid.setpointStableLimit is not None else Qt.CheckState.Unchecked)
        self.setpointStableLimitEnableCheckBox.stateChanged.connect(self.setpointStableEnableChanged)

        self.setpointStableLimitSpinBox = QDoubleSpinBox()
        self.setpointStableLimitSpinBox.setEnabled(False)
        self.setpointStableLimitSpinBox.setToolTip("Maximum difference between the setpoint and the process value to be considered reached")
        self.setpointStableLimitSpinBox.setToolTipDuration(5000)
        self.setpointStableLimitSpinBox.setValue(self.pid.setpointStableLimit if self.pid.setpointStableLimit is not None else 0)
        self.setpointStableLimitSpinBox.valueChanged.connect(self.setpointStableChanged)

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
        self.setpointStableTimeTimeEdit.setTime(QTime.fromMSecsSinceStartOfDay(int(self.pid.setpointStableTime*1000)))
        self.setpointStableTimeTimeEdit.timeChanged.connect(self.setpointStableTimeChanged)

        self.deadbandEnableCheckBox = QCheckBox("Deadband")
        self.deadbandEnableCheckBox.setEnabled(False)
        self.deadbandEnableCheckBox.setToolTip("The minimum amount of output variation to applied this variation")
        self.deadbandEnableCheckBox.setToolTipDuration(5000)
        self.deadbandEnableCheckBox.setCheckState(Qt.CheckState.Checked if self.pid.deadband is not None else Qt.CheckState.Unchecked)
        self.deadbandEnableCheckBox.stateChanged.connect(self.deadbandEnableChanged)

        self.deadbandSpinBox = QDoubleSpinBox()
        self.deadbandSpinBox.setEnabled(False)
        self.deadbandSpinBox.setToolTip("The minimum amount of output variation to applied this variation")
        self.deadbandSpinBox.setToolTipDuration(5000)
        self.deadbandSpinBox.setValue(self.pid.deadband if self.pid.deadband is not None else 0)
        self.deadbandSpinBox.valueChanged.connect(self.deadbandChanged)

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
        self.deadbandActivationTimeTimeEdit.setTime(QTime.fromMSecsSinceStartOfDay(int(self.pid.deadbandActivationTime*1000)))
        self.deadbandActivationTimeTimeEdit.timeChanged.connect(self.deadbandActivationTimeChanged)

        self.processValueStableLimitEnableCheckBox = QCheckBox("Process value stable")
        self.processValueStableLimitEnableCheckBox.setEnabled(False)
        self.processValueStableLimitEnableCheckBox.setToolTip("The maximum variation of the process value to be considered stable")
        self.processValueStableLimitEnableCheckBox.setToolTipDuration(5000)
        self.processValueStableLimitEnableCheckBox.setCheckState(Qt.CheckState.Checked if self.pid.processValueStableLimit is not None else Qt.CheckState.Unchecked)
        self.processValueStableLimitEnableCheckBox.stateChanged.connect(self.processValueStableLimitEnableChanged)

        self.processValueStableLimitSpinBox = QDoubleSpinBox()
        self.processValueStableLimitSpinBox.setEnabled(False)
        self.processValueStableLimitSpinBox.setToolTip("The maximum variation of the process value to be considered stable")
        self.processValueStableLimitSpinBox.setToolTipDuration(5000)
        self.processValueStableLimitSpinBox.setValue(self.pid.processValueStableLimit if self.pid.processValueStableLimit is not None else 0)
        self.processValueStableLimitSpinBox.valueChanged.connect(self.processValueStableLimitChanged)

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
        self.processValueStableTimeTimeEdit.setTime(QTime.fromMSecsSinceStartOfDay(int(self.pid.processValueStableTime*1000)))
        self.processValueStableTimeTimeEdit.timeChanged.connect(self.processValueStableTimeChanged)


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
        self.outputLimitMaxEnableCheckBox = QCheckBox("Maximum")
        self.outputLimitMaxEnableCheckBox.setEnabled(False)
        self.outputLimitMaxEnableCheckBox.setToolTip("Maximum output")
        self.outputLimitMaxEnableCheckBox.setToolTipDuration(5000)
        
        checked = Qt.CheckState.Unchecked

        if self.pid.outputLimits is not None:
            if self.pid.outputLimits[1] is not None:
                checked = Qt.CheckState.Checked

        self.outputLimitMaxEnableCheckBox.setCheckState(checked)
        self.outputLimitMaxEnableCheckBox.stateChanged.connect(self.maximumLimitEnableChanged)

        self.outputLimitMaxSpinBox = QDoubleSpinBox()
        self.outputLimitMaxSpinBox.setEnabled(False)
        self.outputLimitMaxSpinBox.setToolTip("Maximum output")
        self.outputLimitMaxSpinBox.setToolTipDuration(5000)
        self.outputLimitMaxSpinBox.setRange(0, 999999)
        self.outputLimitMaxSpinBox.setValue(0 if checked == Qt.CheckState.Unchecked else self.pid.outputLimits[1])
        self.outputLimitMaxSpinBox.valueChanged.connect(self.maximumLimitChanged)

        self.outputLimitMinEnableCheckBox = QCheckBox("Minimum")
        self.outputLimitMinEnableCheckBox.setEnabled(False)
        self.outputLimitMinEnableCheckBox.setToolTip("Minimum output")
        self.outputLimitMinEnableCheckBox.setToolTipDuration(5000)

        checked = Qt.CheckState.Unchecked

        if self.pid.outputLimits is not None:
            if self.pid.outputLimits[0] is not None:
                checked = Qt.CheckState.Checked
        
        self.outputLimitMinEnableCheckBox.setCheckState(checked)
        self.outputLimitMinEnableCheckBox.stateChanged.connect(self.minimumLimitEnableChanged)

        self.outputLimitMinSpinBox = QDoubleSpinBox()
        self.outputLimitMinSpinBox.setEnabled(False)
        self.outputLimitMinSpinBox.setToolTip("Minimum output")
        self.outputLimitMinSpinBox.setToolTipDuration(5000)
        self.outputLimitMinSpinBox.setRange(0, 999999)
        self.outputLimitMinSpinBox.setValue(0 if checked == Qt.CheckState.Unchecked else self.pid.outputLimits[0])
        self.outputLimitMinSpinBox.valueChanged.connect(self.minimumLimitChanged)

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

        # Setpoint control
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        separator3.setFrameShadow(QFrame.Shadow.Raised)

        self.parametersLayout.addWidget(separator3, 21, 0, 1, 3)

        setpointControlLabel = QLabel("Setpoint")
        setpointControlLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        setpointControlLabel.setStyleSheet("font-size: 24px")

        self.setpointLabel = QLabel("Setpoint")
        self.setpointLabel.setEnabled(False)

        self.setpointSpinBox = QDoubleSpinBox()
        self.setpointSpinBox.setEnabled(False)
        self.setpointSpinBox.setValue(self.pid._setuptoolSetpoint)

        if self.outputLimitMinEnableCheckBox.checkState() == Qt.CheckState.Checked:
            self.setpointSpinBox.setMinimum(self.outputLimitMinSpinBox.value())
        else:
            self.setpointSpinBox.setMinimum(-10000)

        if self.outputLimitMaxEnableCheckBox.checkState() == Qt.CheckState.Checked:
            self.setpointSpinBox.setMaximum(self.outputLimitMaxSpinBox.value())
        else:
            self.setpointSpinBox.setMaximum(10000)
        
        self.applySetpointPushButton = QPushButton("Apply")
        self.applySetpointPushButton.setEnabled(False)
        self.applySetpointPushButton.pressed.connect(self.applySetpoint)

        self.parametersLayout.addWidget(setpointControlLabel, 22, 0, 1, 3)

        self.parametersLayout.addWidget(self.setpointLabel, 23, 1)
        self.parametersLayout.addWidget(self.setpointSpinBox, 23, 2)
        self.parametersLayout.addWidget(self.applySetpointPushButton, 24, 1, 1, 2)

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
        self.refreshTimer.start(1000)

        self.logger.debug("SetupTool initialized")
    
    def refreshData(self):
        """
        PID data collection

        Parameters
        ----------
            None
        
        Returns
        -------
            None
        """
        if not self.pid._setuptoolControl:
            self.setpointSpinBox.setValue(self.pid._setuptoolSetpoint)

        historian = self.pid.historian
        
        if historian is not None:
            if len(historian["TIME"]) >= 0:

                countToAdd = 0

                if self.lastTime is not None:
                    for t in reversed(historian["TIME"]):
                        if t <= self.lastTime:
                            break;

                        countToAdd += 1
                else:
                    countToAdd = -1

                yMin = None
                yMax = None

                for k, v in historian.items():
                    if k != "TIME":
                        # First iteration, seriesData empty
                        if countToAdd == -1:
                            data = []

                            for t, e in zip(historian["TIME"], v):
                                data.append(QPointF(t, e))
                            
                            self.seriesData[k] = data
                        
                        # seriesData smaller than historiantMaxNbPoint
                        elif len(historian["TIME"]) <= self.historianMaxNbPoint:
                            for t, e in zip(historian["TIME"][-countToAdd:], v[-countToAdd:]):
                                self.seriesData[k].append(QPointF(t, e))
                        
                        # seriesData larger than historianMaxNbPoint. Need to remove older sample to fit
                        else:
                            for t, e in zip(historian["TIME"][-countToAdd:], v[-countToAdd:]):
                                self.seriesData[k].append(QPointF(t, e))
                            
                            countToRemove = len(self.seriesData[k]) - self.historianMaxNbPoint

                            self.seriesData[k] = self.seriesData[k][countToRemove:]

                        # Search extremums
                        if yMin is None:
                            yMin = self.seriesData[k][0].y()
                        
                        if yMax is None:
                            yMax = self.seriesData[k][0].y()

                        for e in self.seriesData[k]:
                            yMin = e.y() if e.y() < yMin else yMin
                            yMax = e.y() if e.y() > yMax else yMax

                        # Update points
                        self.series[k].replace(self.seriesData[k])

                # Save last sample time
                self.lastTime = historian["TIME"][-1]

                # Update axis range

                key = list(self.seriesData.keys())[0]
                self.xAxis.setRange(self.seriesData[key][0].x(), self.seriesData[key][-1].x())

                if yMax - yMin < 1:
                    avg = (yMin + yMax) / 2

                    yMin = avg - 0.5
                    yMax = avg + 0.5

                self.yAxis.setRange(yMin, yMax)
            else:
                self.logger.debug("No samples in historian")
        else:
            self.logger.debug("Historian not configured")

    
    def kpSetEnabled(self, enabled):
        """
        Kp widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.kpLabel.setEnabled(enabled)
        self.kpSpinBox.setEnabled(enabled)
    
    def kiSetEnabled(self, enabled):
        """
        Ki widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.kiLabel.setEnabled(enabled)
        self.kiSpinBox.setEnabled(enabled)
    
    def kdSetEnabled(self, enabled):
        """
        Kd widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.kdLabel.setEnabled(enabled)
        self.kdSpinBox.setEnabled(enabled)
    
    def indirectActionSetEnabled(self, enabled):
        """
        Indirect action widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.indirectActionCheckBox.setEnabled(enabled)
    
    def proportionnalOnMeasurementSetEnabled(self, enabled):
        """
        Proportionnal on measurement widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.proportionnalOnMeasurementCheckBox.setEnabled(enabled)
    
    def integralLimitSetEnabled(self, enabled):
        """
        Integral limit widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.integralLimitEnableCheckBox.setEnabled(enabled)
        self.integralLimitSpinBox.setEnabled(enabled and (self.integralLimitEnableCheckBox.checkState() == Qt.CheckState.Checked))
    
    def derivativeOnMeasurementSetEnabled(self, enabled):
        """
        Derivative on measurement widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.derivativeOnMeasurementCheckBox.setEnabled(enabled)
    
    def setpointRampSetEnabled(self, enabled):
        """
        Setpoint ramp widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.setpointRampEnableCheckBox.setEnabled(enabled)
        self.setpointRampSpinBox.setEnabled(enabled and (self.setpointRampEnableCheckBox.checkState() == Qt.CheckState.Checked))
    
    def setpointStableSetEnabled(self, enabled):
        """
        Setpoint stable widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.setpointStableLimitEnableCheckBox.setEnabled(enabled)
        self.setpointStableLimitSpinBox.setEnabled(enabled and (self.setpointStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked))
        self.setpointStableTimeLabel.setEnabled(enabled and (self.setpointStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked))
        self.setpointStableTimeTimeEdit.setEnabled(enabled and (self.setpointStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked))

    def deadbandSetEnabled(self, enabled):
        """
        Deadband widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.deadbandEnableCheckBox.setEnabled(enabled)
        self.deadbandSpinBox.setEnabled(enabled and (self.deadbandEnableCheckBox.checkState() == Qt.CheckState.Checked))
        self.deadbandActivationTimeLabel.setEnabled(enabled and (self.deadbandEnableCheckBox.checkState() == Qt.CheckState.Checked))
        self.deadbandActivationTimeTimeEdit.setEnabled(enabled and (self.deadbandEnableCheckBox.checkState() == Qt.CheckState.Checked))

    def processValueStableSetEnabled(self, enabled):
        """
        Process value stable widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.processValueStableLimitEnableCheckBox.setEnabled(enabled)
        self.processValueStableLimitSpinBox.setEnabled(enabled and (self.processValueStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked))
        self.processValueStableTimeLabel.setEnabled(enabled and (self.processValueStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked))
        self.processValueStableTimeTimeEdit.setEnabled(enabled and (self.processValueStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked))

    def maximumLimitSetEnabled(self, enabled):
        """
        Maximum output limit widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.outputLimitMaxEnableCheckBox.setEnabled(enabled)
        self.outputLimitMaxSpinBox.setEnabled(enabled and (self.outputLimitMaxEnableCheckBox.checkState() == Qt.CheckState.Checked))
    
    def minimumLimitSetEnabled(self, enabled):
        """
        Minimum output limit widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.outputLimitMinEnableCheckBox.setEnabled(enabled)
        self.outputLimitMinSpinBox.setEnabled(enabled and (self.outputLimitMinEnableCheckBox.checkState() == Qt.CheckState.Checked))
    
    def setpointControlSetEnabled(self, enabled):
        """
        Setpoint control widgets enable

        Parameters
        ----------
        enabled: bool

        Returns
        -------
        None
        """
        self.setpointLabel.setEnabled(enabled)
        self.setpointSpinBox.setEnabled(enabled)
        self.applySetpointPushButton.setEnabled(enabled)
    
    def enableWidgets(self):
        """
        Enable all parameters widgets

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.kpSetEnabled(True)
        self.kiSetEnabled(True)
        self.kdSetEnabled(True)
        self.indirectActionSetEnabled(True)
        self.proportionnalOnMeasurementSetEnabled(True)
        self.integralLimitSetEnabled(True)
        self.derivativeOnMeasurementSetEnabled(True)
        self.setpointRampSetEnabled(True)
        self.setpointStableSetEnabled(True)
        self.deadbandSetEnabled(True)
        self.processValueStableSetEnabled(True)
        self.maximumLimitSetEnabled(True)
        self.minimumLimitSetEnabled(True)

        self.logger.debug("Widgets parameters enabled")

    def disableWidgets(self):
        """
        Disable all parameters widgets

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.kpSetEnabled(False)
        self.kiSetEnabled(False)
        self.kdSetEnabled(False)
        self.indirectActionSetEnabled(False)
        self.proportionnalOnMeasurementSetEnabled(False)
        self.integralLimitSetEnabled(False)
        self.derivativeOnMeasurementSetEnabled(False)
        self.setpointRampSetEnabled(False)
        self.setpointStableSetEnabled(False)
        self.deadbandSetEnabled(False)
        self.processValueStableSetEnabled(False)
        self.maximumLimitSetEnabled(False)
        self.minimumLimitSetEnabled(False)

        self.logger.debug("Widgets parameters disabled")
    
    def kpChanged(self, value):
        """
        Kp changed slot

        Parameters
        ----------
        value: float
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Kp value changed to {value:.2f}")
        self.pid.kp = value
    
    def kiChanged(self, value):
        """
        Ki changed slot

        Parameters
        ----------
        value: float
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Ki value changed to {value:.2f}")
        self.pid.ki = value

    def kdChanged(self, value):
        """
        Kd changed slot

        Parameters
        ----------
        value: float
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Kd value changed to {value:.2f}")
        self.pid.kd = value

    def indirectActionChanged(self, state):
        """
        Indirect action changed slot

        Parameters
        ----------
        state: float
            New state
        
        Returns
        -------
        None
        """
        state = Qt.CheckState(state)
        self.logger.debug(f"Indirect action changed to {state}")
        self.pid.indirectAction = (state == Qt.CheckState.Checked)
    
    def proportionnalOnMeasurementChanged(self, state):
        """
        Proportionnal on measurement changed slot

        Parameters
        ----------
        state: float
            New state
        
        Returns
        -------
        None
        """
        state = Qt.CheckState(state)
        self.logger.debug(f"Proportionnal on measurement changed to {state}")
        self.pid.proportionnalOnMeasurement = (state == Qt.CheckState.Checked)
    
    def integralLimitEnableChanged(self, state):
        """
        Integral limit enable changed slot

        Parameters
        ----------
        state: float
            New state
        
        Returns
        -------
        None
        """
        state = Qt.CheckState(state)
        self.logger.debug(f"Integral limit enable changed to {state}")
        self.integralLimitSetEnabled(True)
        self.pid.integralLimit = self.integralLimitSpinBox.value() if (state == Qt.CheckState.Checked) else None
    
    def integralLimitChanged(self, value):
        """
        Integral limit changed slot

        Parameters
        ----------
        value: float
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Integral limit changed to {value}")
        self.pid.integralLimit = value if (self.integralLimitEnableCheckBox.checkState() == Qt.CheckState.Checked) else None

    def derivativeOnMeasurementChanged(self, state):
        """
        Derivative on measurement enable changed slot

        Parameters
        ----------
        state: float
            New state
        
        Returns
        -------
        None
        """
        state = Qt.CheckState(state)
        self.logger.debug(f"Derivative on measurement changed to {state}")
        self.pid.derivativeOnMeasurement = (state == Qt.CheckState.Checked)

    def setpointRampEnableChanged(self, state):
        """
        Setpoint ramp enable changed slot

        Parameters
        ----------
        state: float
            New state
        
        Returns
        -------
        None
        """
        state = Qt.CheckState(state)
        self.logger.debug(f"Setpoint ramp enable changed to {state}")
        self.setpointRampSetEnabled(True)
        self.pid.setpointRamp = self.setpointRampSpinBox.value() if (state == Qt.CheckState.Checked) else None
    
    def setpointRampChanged(self, value):
        """
        Setpoint ramp changed slot

        Parameters
        ----------
        value: float
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Setpoint ramp changed to {value}")
        self.pid.setpointRamp = value if (self.setpointRampEnableCheckBox.checkState() == Qt.CheckState.Checked) else None
    
    def setpointStableEnableChanged(self, state):
        """
        Setpoint stable enable changed slot

        Parameters
        ----------
        state: float
            New state
        
        Returns
        -------
        None
        """
        state = Qt.CheckState(state)
        self.logger.debug(f"Setpoint stable enable changed to {state}")
        self.setpointStableSetEnabled(True)
        self.pid.setpointStableLimit = self.setpointStableLimitSpinBox.value() if (state == Qt.CheckState.Checked) else None
    
    def setpointStableChanged(self, value):
        """
        Setpoint stable changed slot

        Parameters
        ----------
        value: float
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Setpoint stable changed to {value}")
        self.pid.setpointStableLimit = value if (self.setpointStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked) else None

    def setpointStableTimeChanged(self, time: QTime):
        """
        Setpoint stable time changed slot

        Parameters
        ----------
        time: QTime
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Setpoint stable time changed to {time.toString('hh:mm:ss')}")
        self.pid.setpointStableTime = time.msecsSinceStartOfDay() / 1000
    
    def deadbandEnableChanged(self, state):
        """
        Deadband enable changed slot

        Parameters
        ----------
        state: float
            New state
        
        Returns
        -------
        None
        """
        state = Qt.CheckState(state)
        self.logger.debug(f"Deadband enable changed to {state}")
        self.deadbandSetEnabled(True)
        self.pid.deadband = self.deadbandSpinBox.value() if (state == Qt.CheckState.Checked) else None
    
    def deadbandChanged(self, value):
        """
        Deadband changed slot

        Parameters
        ----------
        value: float
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Deadband changed to {value}")
        self.pid.deadband = value if (self.deadbandEnableCheckBox.checkState() == Qt.CheckState.Checked) else None
    
    def deadbandActivationTimeChanged(self, time: QTime):
        """
        Deadband activation time changed slot

        Parameters
        ----------
        time: QTime
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Deadband activation time changed to {time.toString('hh:mm:ss')}")
        self.pid.deadbandActivationTime = time.msecsSinceStartOfDay() / 1000
    
    def processValueStableLimitEnableChanged(self, state):
        """
        Process value stable limit enable changed slot

        Parameters
        ----------
        state: float
            New state
        
        Returns
        -------
        None
        """
        state = Qt.CheckState(state)
        self.logger.debug(f"Process value stable enable changed to {state}")
        self.processValueStableSetEnabled(True)
        self.pid.processValueStableLimit = self.processValueStableLimitSpinBox.value() if (state == Qt.CheckState.Checked) else None
    
    def processValueStableLimitChanged(self, value):
        """
        Process value stable limit changed slot

        Parameters
        ----------
        value: float
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Process value stable limit changed to {value}")
        self.pid.processValueStableLimit = value if (self.processValueStableLimitEnableCheckBox.checkState() == Qt.CheckState.Checked) else None
    
    def processValueStableTimeChanged(self, time: QTime):
        """
        Process value stable time changed slot

        Parameters
        ----------
        time: QTime
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Process value stable time changed to {time.toString('hh:mm:ss')}")
        self.pid.processValueStableTime = time.msecsSinceStartOfDay() / 1000

    def maximumLimitEnableChanged(self, state):
        """
        Maximum limit enable changed slot

        Parameters
        ----------
        state: float
            New state
        
        Returns
        -------
        None
        """
        state = Qt.CheckState(state)
        self.logger.debug(f"Maximum output limit enable changed to {state}")
        self.maximumLimitSetEnabled(True)
        
        self.pid.outputLimits = (self.outputLimitMinSpinBox.value() if self.outputLimitMinEnableCheckBox.checkState() == Qt.CheckState.Checked else None, 
                                 self.outputLimitMaxSpinBox.value() if self.outputLimitMaxEnableCheckBox.checkState() == Qt.CheckState.Checked else None)
    
    def maximumLimitChanged(self, value):
        """
        Maximum limit changed slot

        Parameters
        ----------
        value: float
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Maximum output limit changed to {value}")

        self.pid.outputLimits = (self.outputLimitMinSpinBox.value() if self.outputLimitMinEnableCheckBox.checkState() == Qt.CheckState.Checked else None, 
                                 self.outputLimitMaxSpinBox.value() if self.outputLimitMaxEnableCheckBox.checkState() == Qt.CheckState.Checked else None)

    def minimumLimitEnableChanged(self, state):
        """
        Minimum limit enable changed slot

        Parameters
        ----------
        state: float
            New state
        
        Returns
        -------
        None
        """
        state = Qt.CheckState(state)
        self.logger.debug(f"Minimum output limit enable changed to {state}")
        self.minimumLimitSetEnabled(True)

        self.pid.outputLimits = (self.outputLimitMinSpinBox.value() if self.outputLimitMinEnableCheckBox.checkState() == Qt.CheckState.Checked else None, 
                                 self.outputLimitMaxSpinBox.value() if self.outputLimitMaxEnableCheckBox.checkState() == Qt.CheckState.Checked else None)
    
    def minimumLimitChanged(self, value):
        """
        Minimum limit changed slot

        Parameters
        ----------
        value: float
            New value
        
        Returns
        -------
        None
        """
        self.logger.debug(f"Minimum output limit changed to {value}")

        self.pid.outputLimits = (self.outputLimitMinSpinBox.value() if self.outputLimitMinEnableCheckBox.checkState() == Qt.CheckState.Checked else None, 
                                 self.outputLimitMaxSpinBox.value() if self.outputLimitMaxEnableCheckBox.checkState() == Qt.CheckState.Checked else None)
    
    def applySetpoint(self):
        """
        Send setpoint to the PID

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.logger.debug(f"{self.setpointSpinBox.value()} applied on PID")
        if (self.pid._setuptoolControl):
            self.pid._setuptoolSetpoint = self.setpointSpinBox.value()
    
    def takeControl(self):
        """
        Take control on the PID's setpoint

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.logger.debug("Control taken")
        self.pid._setuptoolControl = True
        self.setpointControlSetEnabled(True)
        self.controlLabel.setText("Control taken")
        self.statusBar().showMessage("Control on PID taken", 10000)

    def releaseControl(self):
        """
        Release control on the PID's setpoint

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.logger.debug("Control released")
        self.pid._setuptoolControl = False
        self.setpointControlSetEnabled(False)
        self.controlLabel.setText("Control released")
        self.statusBar().showMessage("Control on PID released", 10000)

    def setReadOnlyMode(self):
        """
        Activate read-only mode on the PID's parameters

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.readWriteLabel.setText("Read-only mode")
        self.statusBar().showMessage("Read-only mode activated", 10000)
        self.disableWidgets()

    def setReadWriteMode(self):
        """
        Activate read-write mode on the PID's parameters

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if(QMessageBox.question(self, 'Read/write mode', 'Are you sure to activate read/write mode?') == QMessageBox.StandardButton.Yes):
            self.readWriteLabel.setText("Read/write mode")
            self.statusBar().showMessage("Read/write mode activated", 10000)
            self.enableWidgets()
        else:
            self.statusBar().showMessage("Read/write mode activation cancelled", 10000)
            self.readAction.setChecked(True)