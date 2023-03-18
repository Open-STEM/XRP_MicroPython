from machine import Pin, PWM

class Motor:
    """
    A wrapper class handling direction and power sets for the blue motors on the XRP robots
    """

    def __init__(self, dirPin: int, speedPin: int){
        self.dirPin = Pin(dirPin, Pin.OUT)
        self.speedPin = PWM(Pin(speedPin, Pin.OUT))
        self._MAX_PWM = 65534 # Motor holds when actually at full power
    }

    def setEffort(self, effort: float):
        setDirection(effort/abs(effort))
        effort = max(0,min(effort,1);
        self.speedPin.duty_u16(effort*_MAX_PWM)

    def setDirection(self, direction: int):
        pass
