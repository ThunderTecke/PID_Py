import time
from enum import Flag, auto
from threading import Thread
import logging

class HistorianParams(Flag):
    """
    Enumeration to configure historian.
    Use with `or` (|) to sum parameters
        - (HistorianParams.P | HistorianParams.I | HistorianParams.D)
    """
    P = auto()
    I = auto()
    D = auto()
    OUTPUT = auto()
    SETPOINT = auto()
    PROCESS_VALUE = auto()
    ERROR = auto()

class PID:
    """
    PID controller base class.

    Parameters
    ----------
    kp: float
        Proportionnal gain
    
    ki: float
        Integral gain
    
    kd: float
        Derivative gain
    
    indirectAction: bool, default = False
        Invert PID action. Direct action (False) -> error = setpoint - processValue, Indirect action (True) -> error = processValue - setpoint.
        This option implies that when error is increasing the output is decreasing.
    
    proportionnalOnMeasurement: bool
        Activate proportionnal part calculation on processValue, instead of error.
        This avoid output bump when the setpoint change strongly, but increase stabilization time.
        False -> P = kp * error
        True  -> P = -kp * processValue

    integralLimit: float, default = None
        Limit the integral part. When this value is set to None, the integral part is not limited.
        The integral part is clamped between -`integralLimit` and +`integralLimit`.
    
    derivativeOnMeasurement: bool
        Activate derivative part calculation on processValue, instead of error.
        This avoid output bump when the setpoint change strongly, and there is no repercution on the PID behavior.
        If the processValue change strongly, the derivative part will slow down the processValue.s6
        False -> D = kd * ((error - lastError) / dt)
        True  -> D = -kd * ((processValue - lastProcessValue) / dt)
    
    historianParams: HistorianParams, default = None
        Configure historian to record some value of the PID. When at least one value is recorded, time is recorded too.
        Possible value :
            - HistorianParams.P : Proportionnal part
            - HistorianParams.I : Integral part
            - HistorianParams.D : Derivative part
            - HistorianParams.ERROR : PID error
            - HistorianParams.SETPOINT : PID setpoint
            - HistorianParams.PROCESS_VALUE : PID process value
            - HistorianParams.OUTPUT : PID output
    
    historianLenght: int, default = 100000
        The maximum lenght of the historian. When the limit is reached, remove the oldest element.
    
    outputLimits: tuple[float, float], default = (None, None)
        Limit the output between a minimum and a maximum (min, max).
        If a limit is set to None, the limit is deactivated.
        If `outputLimit` is set to None, there is no limits.
    
    logger: logging.Logger or str, default = None
        Logging system. `logging.Logger` instance or logger name (str) can be passed.
        If it's anything else (None or other type), the PID will not send any log.
    
    Attributes
    ----------
    kp: float
        Same as `kp` in parameters section
    
    ki: float
        Same as `ki` in parameters section
    
    kd: float
        Same as `kd` in parameters section
    
    indirectAction: float
        Same as `indirectAction` in parameters section
    
    proportionnalOnMeasurement: bool
        Same as `proportionnalOnMeasurement` in parameters section

    integralLimit: float
        Same as `integralLimit` in parameters section
    
    derivativeOnMeasurement: bool
        Same as `derivativeOnMeasurement` in parameters section
    
    outputLimits: float
        Same as `outputLimits` in parameters section

    historianParams: HistorianParams
        Same as `historianParams` in parameters section
    
    historian: dict[str, list]
        PID value recorded
    
    historianLenght: int
        Same as `historianLenght` in parameters section.
    
    output: float
        PID output
    
    manualMode: bool
        Activate manual mode. In manual mode `output` is directly written by `manualValue` (limitations are always active).
        PID calculation is no longer executed in manual mode.
        Default value : False
    
    manualValue: float
        In manual mode `output` is directly written by `manualValue` (limitations are always active).
    
    bumplessSwitching: bool
        If `bumplessSwitching` is activate, in automatic mode `manualValue` is written by `output` to avoid bump when the manual mode is activated.
        When automatic mode is activated, the PID calculation restart and take setpoint.
        Bump can occur if the setpoint is too far from process value when automatic mode is reactivated.
        Default value : True
    
    logger: logging.Logger
        Contain the `logging.Logger` instance. If it's None or other type, the PID will not send any log.
    
    Methods
    -------
    compute(processValue, setpoint)
        Execution PID calculation. Return `output`.

    __call__(processValue, setpoint)
        call `compute`. Is a code simplification.
    """
    def __init__(self, kp: float, ki: float, kd: float, indirectAction: bool = False, proportionnalOnMeasurement: bool = False, integralLimit: float = None, derivativeOnMeasurment: bool = False, historianParams: HistorianParams = None, historianLenght: int = 100000, outputLimits: tuple[float, float] = (None, None), logger: logging.Logger = None) -> None:
        # PID parameters
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.indirectAction = indirectAction

        self.proportionnalOnMeasurement = proportionnalOnMeasurement
        self.integralLimit = integralLimit
        self.derivativeOnMeasurement = derivativeOnMeasurment

        self.outputLimits = outputLimits

        # Manual mode
        self.manualMode = False
        self.manualValue = 0.0
        self.bumplessSwitching = True

        # Historian setup
        self.historianParams = historianParams
        self.historian = {}

        if (historianLenght <= 0):
            raise ValueError("`historianLenght` can't be 0 or negative!")

        self.historianLenght = historianLenght
        
        if HistorianParams.P in self.historianParams:
            self.historian["P"] = []
        
        if HistorianParams.I in self.historianParams:
            self.historian["I"] = []

        if HistorianParams.D in self.historianParams:
            self.historian["D"] = []
        
        if HistorianParams.OUTPUT in self.historianParams:
            self.historian["OUTPUT"] = []
        
        if HistorianParams.SETPOINT in self.historianParams:
            self.historian["SETPOINT"] = []
        
        if HistorianParams.PROCESS_VALUE in self.historianParams:
            self.historian["PROCESS_VALUE"] = []

        if HistorianParams.ERROR in self.historianParams:
            self.historian["ERROR"] = []

        if (HistorianParams.P in self.historianParams) or (HistorianParams.I in self.historianParams) or (HistorianParams.D in self.historianParams) or (HistorianParams.ERROR in self.historianParams) or (HistorianParams.OUTPUT in self.historianParams) or (HistorianParams.PROCESS_VALUE in self.historianParams) or (HistorianParams.SETPOINT in self.historianParams):
            self.historian["TIME"] = []
        
        # Internal attributes
        self._lastTime = None
        self._lastError = 0.0
        self._lastProcessValue = 0.0
        self._startTime = None

        self._p = 0.0
        self._i = 0.0
        self._d = 0.0

        # Output
        self.output = 0.0

        # Logger
        self.logger = None
        if (isinstance(logger, logging.Logger)):
            self.logger = logger
            self.logger.info("PID object created")
        elif (isinstance(logger, str)):
            self.logger = logging.getLogger(logger)
            self.logger.info("PID object created")

        self.memManualMode = False
        self.integralLimitReached = False
        self.memIntegralLimitReached = False
        self.outputLimitsReached = False
        self.memoutputLimitsReached = False

    def compute(self, processValue: float, setpoint: float) -> float:
        """
        PID calculation execution

        Parameters
        ----------
        processValue: float
            The actual system feedback
        
        setpoint: float
            The target value for the PID
        
        Returns
        -------
        float
            Return the PID output (same as `self.output`)
        """
        # Logging mode switching
        if (self.manualMode and not self.memManualMode and isinstance(self.logger, logging.Logger)):
            self.logger.info("PID switched to manual mode")
        elif (not self.manualMode and self.memManualMode and isinstance(self.logger, logging.Logger)):
            self.logger.info("PID switched to automatic mode")
        
        self.memManualMode = self.manualMode
        
        if self._startTime is not None and self._lastTime is not None:
            actualTime = time.time()

            # ===== Error calculation =====
            if self.indirectAction:
                error = processValue - setpoint
            else:
                error = setpoint - processValue
            
            # ===== Delta time =====
            deltaTime = actualTime - self._lastTime
            
            # ===== Proportionnal part =====
            if (not self.proportionnalOnMeasurement):
                self._p = error * self.kp
            else:
                self._p = -processValue * self.kp

            # ===== Integral part =====
            if (not self.manualMode):
                self._i += ((error + self._lastError) / 2.0) * deltaTime * self.ki

            # Integral part limitation
            self.integralLimitReached = False

            if self.integralLimit is not None:
                if self._i > self.integralLimit:
                    self._i = self.integralLimit

                    self.integralLimitReached = True
                    
                elif self._i < -self.integralLimit:
                    self._i = -self.integralLimit

                    self.integralLimitReached = True
            
            # Integral limit reached warning message
            if (self.integralLimitReached and not self.memIntegralLimitReached and isinstance(self.logger, logging.Logger)):
                self.logger.warning("Integral part has reached the limit (%d, %d)", -self.integralLimit, self.integralLimit)
            
            self.memIntegralLimitReached = self.integralLimitReached
            
            # ===== Derivative part =====
            if (not self.derivativeOnMeasurement):
                self._d = ((error - self._lastError) / deltaTime) * self.kd
            else:
                self._d = -((processValue - self._lastProcessValue) / deltaTime) * self.kd
            
            # ===== Output =====
            if (not self.manualMode):
                _output = self._p + self._i + self._d

                # Bumpless manual value
                if (self.bumplessSwitching):
                    self.manualValue = _output
            else:
                _output = self.manualValue

            # Output limitation
            self.outputLimitsReached = False

            if self.outputLimits is not None:
                if self.outputLimits[0] is not None:
                    if _output < self.outputLimits[0]:
                        _output = self.outputLimits[0]

                        self.outputLimitsReached = True
                if self.outputLimits[1] is not None:
                    if _output > self.outputLimits[1]:
                        _output = self.outputLimits[1]
                        
                        self.outputLimitsReached = True
            
            # Output limit reached warning message
            if (self.outputLimitsReached and not self.memoutputLimitsReached and isinstance(self.logger, logging.Logger)):
                self.logger.warning("Output limits reached (%d, %d)", self.outputLimits[0], self.outputLimits[1])
            
            self.memoutputLimitsReached = self.outputLimitsReached

            # Interal part equal to output in manual mode
            if (self.manualMode):
                self._i = _output - self._p

            # ===== Historian =====
            if HistorianParams.P in self.historianParams:
                self.historian["P"].append(self._p)
                
                if len(self.historian["P"]) > self.historianLenght:
                    del self.historianLenght["P"][0]
            
            if HistorianParams.I in self.historianParams:
                self.historian["I"].append(self._i)
                
                if len(self.historian["I"]) > self.historianLenght:
                    del self.historianLenght["I"][0]

            if HistorianParams.D in self.historianParams:
                self.historian["D"].append(self._d)
                
                if len(self.historian["D"]) > self.historianLenght:
                    del self.historianLenght["D"][0]
            
            if HistorianParams.OUTPUT in self.historianParams:
                self.historian["OUTPUT"].append(_output)
                
                if len(self.historian["OUTPUT"]) > self.historianLenght:
                    del self.historianLenght["OUTPUT"][0]
            
            if HistorianParams.SETPOINT in self.historianParams:
                self.historian["SETPOINT"].append(setpoint)
                
                if len(self.historian["SETPOINT"]) > self.historianLenght:
                    del self.historianLenght["SETPOINT"][0]
            
            if HistorianParams.PROCESS_VALUE in self.historianParams:
                self.historian["PROCESS_VALUE"].append(processValue)
                
                if len(self.historian["PROCESS_VALUE"]) > self.historianLenght:
                    del self.historianLenght["PROCESS_VALUE"][0]

            if HistorianParams.ERROR in self.historianParams:
                self.historian["ERROR"].append(error)
                
                if len(self.historian["ERROR"]) > self.historianLenght:
                    del self.historianLenght["ERROR"][0]

            if (HistorianParams.P in self.historianParams) or (HistorianParams.I in self.historianParams) or (HistorianParams.D in self.historianParams) or (HistorianParams.ERROR in self.historianParams) or (HistorianParams.OUTPUT in self.historianParams) or (HistorianParams.PROCESS_VALUE in self.historianParams) or (HistorianParams.SETPOINT in self.historianParams):
                self.historian["TIME"].append(actualTime - self._startTime)
                
                if len(self.historian["TIME"]) > self.historianLenght:
                    del self.historianLenght["TIME"][0]
            
            # ===== Saving data for next execution =====
            self._lastError = error
            self._lastTime = actualTime
            self._lastProcessValue = processValue

            self.output = _output
            return self.output
        else: # First execution
            self._startTime = time.time()
            self._lastTime = time.time()

            self.output = 0.0
            return 0.0

    def __call__(self, processValue: float, setpoint: float) -> float:
        """
        call `compute`. Is a code simplification.
        
        Parameters
        ----------
        processValue: float
            The actual system feedback
        
        setpoint: float
            The target value for the PID
        
        Returns
        -------
        float
            Return the PID output (same as `self.output`)
        """
        return self.compute(processValue, setpoint)

class ThreadedPID(PID, Thread):
    """
    PID controller in a thread. Inherit from `PID` and `threading.Thread`.
    For more information on `threading.Thread` follow this link https://docs.python.org/3/library/threading.html#thread-objects.

    Parameters
    ----------
    kp: float
        Proportionnal gain
    
    ki: float
        Integral gain
    
    kd: float
        Derivative gain
    
    indirectAction: bool, default = False
        Invert PID action. Direct action (False) -> error = setpoint - processValue, Indirect action (True) -> error = processValue - setpoint.
        This option implies that when error is increasing the output is decreasing.
    
    proportionnalOnMeasurement: bool
        Activate proportionnal part calculation on processValue, instead of error.
        This avoid output bump when the setpoint change strongly, but increase stabilization time.
        False -> P = kp * error
        True  -> P = -kp * processValue

    integralLimit: float, default = None
        Limit the integral part. When this value is set to None, the integral part is not limited.
        The integral part is clamped between -`integralLimit` and +`integralLimit`.
    
    derivativeOnMeasurement: bool
        Activate derivative part calculation on processValue, instead of error.
        This avoid output bump when the setpoint change strongly, and there is no repercution on the PID behavior.
        If the processValue change strongly, the derivative part will slow down the processValue.s6
        False -> D = kd * ((error - lastError) / dt)
        True  -> D = -kd * ((processValue - lastProcessValue) / dt)
    
    historianParams: HistorianParams, default = None
        Configure historian to record some value of the PID. When at least one value is recorded, time is recorded too.
        Possible value :
            - HistorianParams.P : Proportionnal part
            - HistorianParams.I : Integral part
            - HistorianParams.D : Derivative part
            - HistorianParams.ERROR : PID error
            - HistorianParams.SETPOINT : PID setpoint
            - HistorianParams.PROCESS_VALUE : PID process value
            - HistorianParams.OUTPUT : PID output
            
    historianLenght: int, default = 100000
        The maximum lenght of the historian. When the limit is reached, remove the oldest element.
    
    outputLimits: tuple[float, float], default = (None, None)
        Limit the output between a minimum and a maximum (min, max).
        If a limit is set to None, the limit is deactivated.
        If `outputLimit` is set to None, there is no limits.
    
    logger: logging.Logger or str, default = None
        Logging system. `logging.Logger` instance or logger name (str) can be passed.
        If it's anything else (None or other type), the PID will not send any log.
    
    cycleTime: float, default = 0.0
        Define the minimum time between two PID calculations.
        If this time is lower than the real execution time, there is no pause between execution.
        If `cycleTime` is higher than the real execution time, a pause is made to wait `cycleTime` since the start of the previous execution.

    Attributes
    ----------
    setpoint: float
        The current target value used for the PID calculation.
    
    processValue: float
        The current system feedback used for the PID calculation. For a better PID, update it more faster than the PID execution.
    
    cycleTime: float
        Same as `cycleTime` in parameters section.
    
    quit: bool
        When the threaded PID is started, it can be stopped by setting `quit` to `True`. The PID finish the current execution and stop the thread.
    
    Methods
    -------
    start()
        Used to start the thread.
    """
    def __init__(self, kp: float, ki: float, kd: float, indirectAction: bool = False, proportionnalOnMeasurement: bool = False, integralLimit: float = None, derivativeOnMeasurment: bool = False, historianParams: HistorianParams = None, historianLenght: int = 100000, outputLimits: tuple[float, float] = (None, None), logger: logging.Logger = None, cycleTime: float = 0.0) -> None:
        PID.__init__(self, kp, ki, kd, indirectAction, proportionnalOnMeasurement, integralLimit, derivativeOnMeasurment, historianParams, historianLenght, outputLimits, logger)
        Thread.__init__(self)

        self.setpoint = 0.0
        self.processValue = 0.0
        self.cycleTime = cycleTime

        self.quit = False
    
    def start(self) -> None:
        """
        Used to start the threaded PID. Overrided from `threading.Thread`
        See `threading.Thread` documentation for more information.
        """
        # Call PID execution to initialize time memory
        self.compute(self.processValue, self.setpoint)
        self.quit = False
        return Thread.start(self)
    
    def run(self):
        """
        Thread execution. Overrided from `threading.Thread`
        See `threading.Thread` documentation for more information
        """
        while self.quit is False:
            while time.time() < (self._lastTime + self.cycleTime):
                time.sleep(self.cycleTime / 100.0)

            self.compute(self.processValue, self.setpoint)