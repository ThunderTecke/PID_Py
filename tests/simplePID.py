import PID_Py.PID as PID
import PID_Py.Simulation as Sim
from PID_Py.PID import HistorianParams as HistParams

import time
import matplotlib.pyplot as plt

pid = PID.PID(kp = 1.0, ki = 11.0, kd = 0.0, proportionnalOnMeasurement=True, derivativeOnMeasurment=True, historianParams=(HistParams.ERROR | HistParams.OUTPUT | HistParams.PROCESS_VALUE | HistParams.SETPOINT | HistParams.P | HistParams.I | HistParams.D))
system = Sim.Simulation(1.0, 0.1)

startTime = time.time()
setpoint = 0.0

timeLenght = 20.0

print("Start...")
print(f"This will be take {timeLenght} secondes")

while time.time() - startTime < timeLenght:
    if time.time() - startTime >= 1.0:
        setpoint = 10.0
    
    system(pid(system.output, setpoint))

    time.sleep(0.001)

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