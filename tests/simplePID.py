import PID_Py.PID as PID
import PID_Py.Simulation as Sim
from PID_Py.PID import HistorianParams as HistParams

import time
import matplotlib.pyplot as plt
import numpy as np

pid = PID.PID(kp = 1.0, ki = 0.1, kd = 0.0, logger="PID", simulation=Sim.Simulation(1.0, 0.1), historianParams=(HistParams.ERROR | HistParams.OUTPUT | HistParams.PROCESS_VALUE | HistParams.SETPOINT | HistParams.P | HistParams.I | HistParams.D))

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
    
    pid(setpoint = setpoint, currentTime = t)

fig, (systemPlot, pidPlot, outputPlot) = plt.subplots(3, sharex=True)

fig.suptitle(f'Kp = {pid.kp}, Ki = {pid.ki}, kd = {pid.kd}')
fig.set_size_inches(7, 8)

systemPlot.plot(pid.historian["TIME"], pid.historian["SETPOINT"], label="Setpoint")
systemPlot.plot(pid.historian["TIME"], pid.historian["PROCESS_VALUE"], label="Process value")
systemPlot.plot(pid.historian["TIME"], pid.historian["ERROR"], label="Error")
systemPlot.legend()
systemPlot.set_title("System")

pidPlot.plot(pid.historian["TIME"], pid.historian["P"], label="P")
pidPlot.plot(pid.historian["TIME"], pid.historian["I"], label="I")
pidPlot.plot(pid.historian["TIME"], pid.historian["D"], label="D")
pidPlot.legend()
pidPlot.set_title("PID")

outputPlot.plot(pid.historian["TIME"], pid.historian["OUTPUT"], label="Output")
outputPlot.legend()
outputPlot.set_title("Output")
outputPlot.set_xlabel("time (s)")

plt.show()