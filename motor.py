from machine import Pin, PWM

class Motor:

    """
    A wrapper class handling direction and power sets for the blue motors on the XRP robots

    TODO: Add Encoder support
    """

    def __init__(self, direction_pin: int, speed_pin: int):
        self._dirPin = Pin(direction_pin, Pin.OUT)
        self._speedPin = PWM(Pin(speed_pin, Pin.OUT))
        self._MAX_PWM = 65534 # Motor holds when actually at full power

    def set_effort(self, effort: float):
        if effort < 0:
            # Change direction if negative power
            effort *= -1
            self.set_direction(1)
        else:
            self.set_direction(0)
        # Cap power to [0,1]
        effort = max(0,min(effort,1))
        self._speedPin.duty_u16(int(effort*self._MAX_PWM))

    def set_direction(self, direction: int):
        self._dirPin.value(direction)
