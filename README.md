[![GitHub](https://img.shields.io/github/license/ThunderTecke/PID_Py)](https://github.com/ThunderTecke/PID_Py/blob/develop/LICENSE)
[![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/ThunderTecke/PID_Py)](https://github.com/ThunderTecke/PID_Py/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/ThunderTecke/PID_Py)](https://github.com/ThunderTecke/PID_Py/releases)
[![GitHub last commit](https://img.shields.io/github/last-commit/ThunderTecke/PID_Py)](https://github.com/ThunderTecke/PID_Py/commits)
[![GitHub issues](https://img.shields.io/github/issues/ThunderTecke/PID_Py)](https://github.com/ThunderTecke/PID_Py/issues)
![Python version](https://img.shields.io/badge/Python-v3.10-blue)

# PID_Py
`PID_Py` provide a PID controller wrote in Python. This PID controller is simple to use, but it's complete.

## :bangbang: Non-responsability :bangbang:
***<span style="color:red">I am not responsible for any material or personal damages in case of failure. Use at your own risk.</span>***

## Installation
```
python3 -m pip install PID_Py
```

## Usage
### Minimum usage 
```Python
from PID_Py.PID import PID

# Initialization
pid = PID(kp = 0.0, ki = 0.0, kd = 0.0)

...

# PID execution (call it as fast as you can)
command = pid(processValue = feedback, setpoint = targetValue)
```

In this usage the PID as no limitation, no history and the PID is in direct action (Error increasing -> Increase output).

### Indirect action PID
If you have a system that required to decrease command to increase feedback, you can use `indirectAction` parameters.

```Python
from PID_Py.PID import PID

# Initialization
pid = PID(kp = 0.0, ki = 0.0, kd = 0.0, indirectAction = True)

...

# PID execution (call it as fast as you can)
command = pid(processValue = feedback, setpoint = targetValue)
```

### Limiting output
If your command must be limit you can use `outputLimits` parameters.

```Python
from PID_Py.PID import PID

# Initialization
pid = PID(kp = 0.0, ki = 0.0, kd = 0.0, outputLimits = (0, 100))

...

# PID execution (call it as fast as you can)
command = pid(processValue = feedback, setpoint = targetValue)
```

By default the value is `(None, None)`, which implies that there is no limits. You can activate just the maximum limit with `(None, 100)`. The same for the minimum limit `(-100, None)`.

### Historian
If you want to historize PID values, you can configure the historian to record values.

```Python
from PID_Py.PID import PID
from PID_Py.PID import HistorianParameters

# Initialization
historianParameters = HistorianParamters.SETPOINT | HistorianParameters.PROCESS_VALUE
pid = PID(kp = 0.0, ki = 0.0, kd = 0.0, historianParameters = HistorianParameters)

...

# PID execution (call it as fast as you can)
command = pid(processValue = feedback, setpoint = targetValue)

...

# PID Historian
import matplotlib.pyplot as plt

plt.plot(pid.historian["TIME"], pid.historian["SETPOINT"], label="Setpoint")

plt.plot(pid.historian["TIME"], pid.historian["PROCESS_VALUE"], label="Process value")

plt.legend()
plt.show()
```
In the example above, the PID historian records `setpoint`, `processValue` and `time`. Time is the elapsed time from the start. After that a graphic is draw with `matplotlib`.

#### Historian parameters list
- `P` : proportionnal part
- `I` : integral part
- `D` : derivative part
- `ERROR` : PID error
- `SETPOINT` : PID setpoint
- `PROCESS_VALUE` : PID process value
- `OUTPUT` : PID output

The maximum lenght of the historian can be choose. By default it is set to 100 000 record per parameter. Take care about your memory.

In example for one parameters. A `float` value take 24 bytes in memory. So `100 000` floats take `2 400 000` bytes (~2.3MB).

For all parameters it takes `16 800 000` bytes (~16MB).
It's not big for a computer, but if PID is executed each millisecond (0.001s), 100 000 record represent only 100 seconds of recording. 

If you want to save 1 hour at 1 millisecond you will need 3 600 000 records (~82.4MB) for one parameter, and for all parameters it will takes ~576.8MB.

For a raspberry pi 3 B+ it's the half of the RAM capacity (1GB)

### Proportionnal on measurement
This avoid a strong response of proportionnal part when the setpoint is suddenly changed. 

This change the P equation as follow :
- False : P = error * kp
- True : P = -(processValue * kp)

This result in an augmentation of the stabilization time of the system, but there is no bump on the output when the setpoint change suddenly. There is no difference on the reponds to process disturbance.

```Python
from PID_Py.PID import PID

# Initialization
pid = PID(kp = 0.0, ki = 0.0, kd = 0.0, proportionnalOnMeasurement=True)

...

# PID execution (call it as fast as you can)
command = pid(processValue = feedback, setpoint = targetValue)
```

### Integral limitation
The integral part of the PID can be limit to avoid overshoot of the output when the error is too high (When the setpoint variation is too high, or when the system have trouble to reach setpoint).

```Python
from PID_Py.PID import PID

# Initialization
pid = PID(kp = 0.0, ki = 0.0, kd = 0.0, integralLimit = 20.0)

...

# PID execution (call it as fast as you can)
command = pid(processValue = feedback, setpoint = targetValue)
```

In the example above, the integral part of the PID is clamped between -20 and 20.

### Derivative on measurement
This avoid a strong response of derivate part when the setpoint is suddenly changed. 

This change the D equation as follow :
- False : D = ((error - lastError) / dt) * kd
- True : D = -(((processValue - lastProcessValue) / dt) * kd)

The effect is there is no bump when the setpoint change suddenly, and there is no difference on the responds to process disturbance.

```Python
from PID_Py.PID import PID

# Initialization
pid = PID(kp = 0.0, ki = 0.0, kd = 0.0, derivativeOnMeasurement=True)

...

# PID execution (call it as fast as you can)
command = pid(processValue = feedback, setpoint = targetValue)
```

### Manual mode
The PID can be switch in manual mode, this allow to operate output directly through `manualValue`.

```Python
from PID_Py.PID import PID

# Initialization
pid = PID(kp = 0.0, ki = 0.0, kd = 0.0)

...

# Manual mode
pid.manualMode = True
pid.manualValue = 12.7

...

# PID execution (call it as fast as you can)
command = pid(processValue = feedback, setpoint = targetValue)
```

In the example above, command will be always equal to 12.7. The PID calculation is no longer executed. The proportionnal, integral and derivative parts still at the same value to avoid bump when switching back to automatic.

To avoid bump when switching in manual there is `bumplessSwitching` attribute. This attributes keep `manualValue` equal to `output`. 

If you disable this function you will have bump when you switch in manual mode with `manualValue` different of `output`. If this case you can **destabilise** (:heavy_exclamation_mark:) your system. Be careful

### Logging
The PID can use a logger (logging.Logger built-in class) to log event. Logging configuration can be set outside of the PID.
See [logging.Logger](https://docs.python.org/3/library/logging.html#logger-objects) documentation.

```Python
from PID_Py.PID import PID
import logging

# Initialization
pid = PID(kp = 0.0, ki = 0.0, kd = 0.0, logger = logging.getLogger("PID"))

...

# PID execution (call it as fast as you can)
command = pid(processValue = feedback, setpoint = targetValue)
```

In the example above, the PID will send event on the logger. The logger can also get with the name.

```Python
pid = PID(kp = 0.0, ki = 0.0, kd = 0.0, logger = "PID")
```

### Threaded PID
With the threaded PID you don't have to call `pid(processValue, setpoint)`. It's call as fast as possible or with a constant cycle time. When you want to stop the PID use `quit` attribute to finish the current execution and exit. 

```Python
from PID_Py.PID import ThreadedPID

# Initialization
pid = ThreadedPID(kp = 0.0, ki = 0.0, kd = 0.0, cycleTime = 0.01)
pid.start()

...

# PID inputs
pid.setpoint = targetValue
pid.processValue = feedback

# PID output
command = pid.output

...

# Stop PID
pid.quit = True
pid.join()
```

In the example above the threaded PID is created with 10ms (0.01s) of cyclic time. It means that the calculation is executed each 10ms.