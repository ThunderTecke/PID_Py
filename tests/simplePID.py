import PID_Py.PID as PID
import PID_Py.Simulation as Sim
from PID_Py.PID import HistorianParams as HistParams

import time
import matplotlib.pyplot as plt
import numpy as np

pid = PID.PID(kp = 1.0, ki = 1.0, kd = 0.0, deadband=1.0, deadbandActivationTime=5.0, proportionnalOnMeasurement=True, derivativeOnMeasurment=True, integralLimit=50.0, setpointStableLimit=0.1, setpointStableTime=1.0, processValueStableLimit=0.1, processValueStableTime=1.0, historianParams=(HistParams.ERROR | HistParams.OUTPUT | HistParams.PROCESS_VALUE | HistParams.SETPOINT | HistParams.P | HistParams.I | HistParams.D))
system = Sim.Simulation(1.0, 1.0)

startTime = time.time()
setpoint = 0.0

timeLenght = 20.0
cycleTime = 0.001

timeValue = np.arange(0, timeLenght, cycleTime)

memProcessValueStable = False
memSetpointReached = False

print("Start...")

for t in timeValue:
    if t >= 1.0:
        setpoint = 10.0
    
    if t >= 10.0:
        setpoint = 10.5
    
    if t >= 11.0:
        setpoint = 11.5

    if (pid.setpointReached and not memSetpointReached):
        print(f"PID reache setpoint at {t:.1f}s")
    
    if (not pid.setpointReached and memSetpointReached):
        print(f"PID leave the setpoint at {t:.1f}s")
    
    memSetpointReached = pid.setpointReached
    
    system(pid(system.output, setpoint, t), t)

fig, (systemPlot, pidPlot, outputPlot) = plt.subplots(3, sharex=True)

systemPlot.plot(pid.historian["TIME"], pid.historian["SETPOINT"], label="Setpoint")
systemPlot.plot(pid.historian["TIME"], pid.historian["PROCESS_VALUE"], label="Process value")
systemPlot.plot(pid.historian["TIME"], pid.historian["ERROR"], label="Error")
systemPlot.legend()

pidPlot.plot(pid.historian["TIME"], pid.historian["P"], label="P")
pidPlot.plot(pid.historian["TIME"], pid.historian["I"], label="I")
pidPlot.plot(pid.historian["TIME"], pid.historian["D"], label="D")
pidPlot.legend()

outputPlot.plot(pid.historian["TIME"], pid.historian["OUTPUT"], label="Output")
outputPlot.legend()

plt.show()