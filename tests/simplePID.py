import PID_Py.PID as PID
import PID_Py.Simulation as Sim
from PID_Py.PID import HistorianParams as HistParams

import time
import matplotlib.pyplot as plt

pid = PID.PID(kp = 1.0, ki = 1.0, kd = 0.0, historianParams=(HistParams.ERROR | HistParams.OUTPUT | HistParams.PROCESS_VALUE | HistParams.SETPOINT | HistParams.P | HistParams.I | HistParams.D))
system = Sim.Simulation(1.0, 0.1)

startTime = time.time()
setpoint = 0.0

timeLenght = 20.0

print("Start...")
print(f"This will be take {timeLenght} secondes")

while time.time() - startTime < timeLenght:
    if time.time() - startTime >= 1.0:
        setpoint = 10.0
    
    if time.time() - startTime >= 5.0:
        pid.manualMode = True
    
    if time.time() - startTime >= 6.0:
        pid.manualValue = 2.0
        setpoint = 5.0
    
    if time.time() - startTime >= 8.0:
        pid.manualMode = False
    
    system(pid(system.output, setpoint))

    time.sleep(0.001)

fig, (systemPlot, pidPlot) = plt.subplots(2, sharex=True)

systemPlot.plot(pid.historian["TIME"], pid.historian["SETPOINT"], label="Setpoint")
systemPlot.plot(pid.historian["TIME"], pid.historian["PROCESS_VALUE"], label="Process value")
systemPlot.plot(pid.historian["TIME"], pid.historian["ERROR"], label="Error")
systemPlot.legend()

pidPlot.plot(pid.historian["TIME"], pid.historian["P"], label="P")
pidPlot.plot(pid.historian["TIME"], pid.historian["I"], label="I")
pidPlot.plot(pid.historian["TIME"], pid.historian["D"], label="D")
pidPlot.legend()

plt.show()