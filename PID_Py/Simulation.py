import time

class Simulation:
    def __init__(self, K: float, tau: float) -> None:
        # System simulation parameters
        self.K = K
        self.tau = tau

        # Internal attributes
        self._lastTime = None

        # Output
        self.output = 0.0
        
    def __call__(self, input: float) -> float:
        if self._lastTime is not None:
            deltaTime = time.time() - self._lastTime
            self.output += (1.0/self.tau) * ((self.K * input) - self.output) * deltaTime
        
        self._lastTime = time.time()