import time
from enum import Flag, auto

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
    
    Methods
    -------
    __call__(processValue, setpoint)
        Execution PID calculation. Return `output`
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

        self._i = 0.0

        # Output
        self.output = 0.0
    
    def __call__(self, processValue: float, setpoint: float) -> float:
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
                p = 0.0

                if (self.bumplessSwitching):
                    self._i = 0.0

                d = 0.0
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
                p = error * self.kp

                # ===== Integral part =====
                self._i += ((error + self._lastError) / 2.0) * deltaTime * self.ki

                # Integral part limitation
                if self.integralLimit is not None:
                    if self._i > self.integralLimit:
                        self._i = self.integralLimit
                    elif self._i < -self.integralLimit:
                        self._i = -self.integralLimit
                
                # ===== Derivative part =====
                d = ((error - self._lastError) / deltaTime) * self.kd
                
                # ===== Output =====
                _output = p + self._i + d

                # ===== Bumpless manual value =====
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
                self.historian["P"].append(p)
            
            if HistorianParams.I in self.historianParams:
                self.historian["I"].append(self._i)

            if HistorianParams.D in self.historianParams:
                self.historian["D"].append(d)
            
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