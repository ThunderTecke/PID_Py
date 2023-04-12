from PID_Py.PID import PID, ThreadedPID, HistorianParams
from PID_Py.SetupTool import SetupToolApp
from PID_Py.Simulation import Simulation

from PySide6.QtWidgets import QApplication

import sys

pid = ThreadedPID(kp=1, ki=0, kd=0.0, 
                  cycleTime=0.01, 
                  historianParams=HistorianParams.SETPOINT | HistorianParams.PROCESS_VALUE, 
                  simulation=Simulation(1, 1))
pid.start()

app = QApplication(sys.argv)

setupToolApp = SetupToolApp(pid)
setupToolApp.show()

app.exec()

pid.quit = True
pid.join()