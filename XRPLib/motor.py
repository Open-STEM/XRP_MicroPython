from machine import Pin, PWM
class Motor:

    """
    A wrapper class handling direction and power sets for DC motors on the XRP robots
    """

    def __init__(self, in1_direction_pin: int, in2_speed_pin: int, flip_dir:bool=False, pwmMode:bool=False):
        self._pwmMode = pwmMode
        self.flip_dir = flip_dir
        self._MAX_PWM = 65534 # Motor holds when actually at full power

        if self._pwmMode:
            self._in1DirPin = PWM(Pin(in1_direction_pin, Pin.OUT))
            self._in2SpeedPin = PWM(Pin(in2_speed_pin, Pin.OUT))
            self._in1DirPin.freq(50)
            self._in2SpeedPin.freq(50)
        else:
            self._in1DirPin = Pin(in1_direction_pin, Pin.OUT)
            self._in2SpeedPin = PWM(Pin(in2_speed_pin, Pin.OUT))
            self._in2SpeedPin.freq(50)

    def set_effort(self, effort: float):
        """
        Sets the effort value of the motor (corresponds to power)

        :param effort: The effort to set the motor to, between -1 and 1
        :type effort: float
        """

        if self._pwmMode:
            in1Pwm = (effort < 0) ^ (self.flip_dir)
            if in1Pwm:
                self._in1DirPin.duty_u16(int(abs(effort)*self._MAX_PWM))
                self._in2SpeedPin.duty_u16(int(0))
            else:
                self._in1DirPin.duty_u16(int(0))
                self._in2SpeedPin.duty_u16(int(abs(effort)*self._MAX_PWM))
        else:
            if effort < 0:
                # Change direction if negative power
                effort *= -1
                self._set_direction(1)
            else:
                self._set_direction(0)
            # Cap power to [0,1]
            effort = max(0,min(effort,1))
            self._in2SpeedPin.duty_u16(int(effort*self._MAX_PWM))
                

    def _set_direction(self, direction: int):
        if self.flip_dir:
            self._in1DirPin.value(not direction)
        else:
            self._in1DirPin.value(direction)
