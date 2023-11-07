from machine import Pin, PWM
class Motor:

    """
    A wrapper class handling direction and power sets for DC motors on the XRP robots
    """

    def __init__(self, direction_pin: int, speed_pin: int, flip_dir:bool=False):
        self._dirPin = Pin(direction_pin, Pin.OUT)
        self._speedPin = PWM(Pin(speed_pin, Pin.OUT))
        self._speedPin.freq(50)
        self.flip_dir = flip_dir
        self._MAX_PWM = 65534 # Motor holds when actually at full power

    def set_effort(self, effort: float):
        """
        Sets the effort value of the motor (corresponds to power)

        :param effort: The effort to set the motor to, between -1 and 1
        :type effort: float
        """

        if effort < 0:
            # Change direction if negative power
            effort *= -1
            self._set_direction(1)
        else:
            self._set_direction(0)
        # Cap power to [0,1]
        effort = max(0,min(effort,1))
        self._speedPin.duty_u16(int(effort*self._MAX_PWM))

    def _set_direction(self, direction: int):
        if self.flip_dir:
            self._dirPin.value(not direction)
        else:
            self._dirPin.value(direction)
