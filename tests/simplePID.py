import PID_Py.PID as PID
import PID_Py.Simulation as Sim
from PID_Py.PID import HistorianParams as HistParams

import time
import matplotlib.pyplot as plt

pid = PID.PID(kp = 1.0, ki = 1.0, kd = 0.0, proportionnalOnMeasurement=True, derivativeOnMeasurment=True, integralLimit=50.0, setpointStableLimit=0.1, setpointStableTime=1.0, processValueStableLimit=0.1, processValueStableTime=1.0, historianParams=(HistParams.ERROR | HistParams.OUTPUT | HistParams.PROCESS_VALUE | HistParams.SETPOINT | HistParams.P | HistParams.I | HistParams.D))
system = Sim.Simulation(1.0, 0.1)

startTime = time.time()
setpoint = 0.0

timeLenght = 20.0

memProcessValueStable = False
memSetpointReached = False

print("Start...")
print(f"This will be take {timeLenght} secondes")

while time.time() - startTime < timeLenght:
    if time.time() - startTime >= 1.0:
        setpoint = 10.0
    
    if (pid.processValueStabilized and not memProcessValueStable):
        print(f"PID stabilized at {pid._lastProcessValue}, {time.time() - startTime}")
    
    if (not pid.processValueStabilized and memProcessValueStable):
        print(f"PID unstable at {pid._lastProcessValue}, {time.time() - startTime}")
    
    memProcessValueStable = pid.processValueStabilized

    if (pid.setpointReached and not memSetpointReached):
        print(f"PID reache setpoint at {time.time() - startTime}")
    
    if (not pid.setpointReached and memSetpointReached):
        print(f"PID leave the setpoint at {time.time() - startTime}")
    
    memSetpointReached = pid.setpointReached
    
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