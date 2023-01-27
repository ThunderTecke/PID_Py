import time
from enum import Flag, auto
from threading import Thread

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
    
    integralLimit: float, default = None
        Limit the integral part. When this value is set to None, the integral part is not limited.
        The integral part is clamped between -`integralLimit` and +`integralLimit`.
    
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
    
    outputLimits: tuple[float, float], default = (None, None)
        Limit the output between a minimum and a maximum (min, max).
        If a limit is set to None, the limit is deactivated.
        If `outputLimit` is set to None, there is no limits.
    
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
    
    integralLimit: float
        Same as `integralLimit` in parameters section
    
    outputLimits: float
        Same as `outputLimits` in parameters section

    historianParams: HistorianParams
        Same as `historianParams` in parameters section
    
    historian: dict[str, list]
        PID value recorded
    
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
    
    Methods
    -------
    compute(processValue, setpoint)
        Execution PID calculation. Return `output`.

    __call__(processValue, setpoint)
        call `compute`. Is a code simplification.
    """
    def __init__(self, kp: float, ki: float, kd: float, indirectAction: bool = False, integralLimit: float = None, historianParams: HistorianParams = None, outputLimits: tuple[float, float] = (None, None)) -> None:
        # PID parameters
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.indirectAction = indirectAction

        self.integralLimit = integralLimit

        self.outputLimits = outputLimits

        # Manual mode
        self.manualMode = False
        self.manualValue = 0.0
        self.bumplessSwitching = True

        # Historian setup
        self.historianParams = historianParams
        self.historian = {}
        
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
        self._startTime = None

        self._p = 0.0
        self._i = 0.0
        self._d = 0.0

        # Output
        self.output = 0.0
    
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
        if self._startTime is not None and self._lastTime is not None:
            actualTime = time.time()

            if (self.manualMode):
                # ========== Manual mode ==========
                _output = self.manualValue
                error = 0.0

                # ========== End of manual mode ==========
            else: 
                # ========== Automatic mode ==========
                # ===== Error calculation =====
                if self.indirectAction:
                    error = processValue - setpoint
                else:
                    error = setpoint - processValue
                
                # ===== Delta time =====
                deltaTime = actualTime - self._lastTime
                
                # ===== Proportionnal part =====
                self._p = error * self.kp

                # ===== Integral part =====
                self._i += ((error + self._lastError) / 2.0) * deltaTime * self.ki

                # Integral part limitation
                if self.integralLimit is not None:
                    if self._i > self.integralLimit:
                        self._i = self.integralLimit
                    elif self._i < -self.integralLimit:
                        self._i = -self.integralLimit
                
                # ===== Derivative part =====
                self._d = ((error - self._lastError) / deltaTime) * self.kd
                
                # ===== Output =====
                _output = self._p + self._i + self._d

                # ===== Bumpless manual value =====
                if (self.bumplessSwitching):
                    self.manualValue = _output

                # ========== End of automatic mode ==========

            # Output limitation
            if self.outputLimits is not None:
                if self.outputLimits[0] is not None:
                    if _output < self.outputLimits[0]:
                        _output = self.outputLimits[0]
                if self.outputLimits[1] is not None:
                    if _output > self.outputLimits[1]:
                        _output = self.outputLimits[1]

            # ===== Historian =====
            if HistorianParams.P in self.historianParams:
                self.historian["P"].append(self._p)
            
            if HistorianParams.I in self.historianParams:
                self.historian["I"].append(self._i)

            if HistorianParams.D in self.historianParams:
                self.historian["D"].append(self._d)
            
            if HistorianParams.OUTPUT in self.historianParams:
                self.historian["OUTPUT"].append(_output)
            
            if HistorianParams.SETPOINT in self.historianParams:
                self.historian["SETPOINT"].append(setpoint)
            
            if HistorianParams.PROCESS_VALUE in self.historianParams:
                self.historian["PROCESS_VALUE"].append(processValue)

            if HistorianParams.ERROR in self.historianParams:
                self.historian["ERROR"].append(error)

            if (HistorianParams.P in self.historianParams) or (HistorianParams.I in self.historianParams) or (HistorianParams.D in self.historianParams) or (HistorianParams.ERROR in self.historianParams) or (HistorianParams.OUTPUT in self.historianParams) or (HistorianParams.PROCESS_VALUE in self.historianParams) or (HistorianParams.SETPOINT in self.historianParams):
                self.historian["TIME"].append(actualTime - self._startTime)
            
            # ===== Saving data for next execution =====
            self._lastError = error
            self._lastTime = actualTime

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
    
    integralLimit: float, default = None
        Limit the integral part. When this value is set to None, the integral part is not limited.
        The integral part is clamped between -`integralLimit` and +`integralLimit`.
    
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
    
    outputLimits: tuple[float, float], default = (None, None)
        Limit the output between a minimum and a maximum (min, max).
        If a limit is set to None, the limit is deactivated.
        If `outputLimit` is set to None, there is no limits.
    
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
    def __init__(self, kp: float, ki: float, kd: float, indirectAction: bool = False, integralLimit: float = None, historianParams: HistorianParams = None, outputLimits: tuple[float, float] = (None, None), cycleTime: float = 0.0) -> None:
        PID.__init__(self, kp, ki, kd, indirectAction, integralLimit, historianParams, outputLimits)
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