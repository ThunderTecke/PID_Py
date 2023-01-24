# PID_Py
`PID_Py` provide a PID controller wrote in Python. This PID controller is simple to use, but it's complete.

## Installation
```Shell
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

In this usage the PID as no limitation, no history and the PID is in direct action (Error increasing -> Increase output)

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

By default the value is `(None, None)`, wich implies that there is no limits. You can activate just the maximum limit with `(None, 100)`. The same for the minimum limit `(-100, None)`

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
In the example above, the PID historian records `setpoint`, `processValue` and `time`. Time is the elapsed time from the start. After that a graphic is draw with `matplotlib`