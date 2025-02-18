from machine import Pin, PWM

class SinglePWMMotor:

    """
    A simple class handling direction and power sets for DC motors on the XRP robots

    This version is used for the XRP Beta, which uses the rp2040 processor
    """

    def __init__(self, in1_direction_pin: int|str, in2_speed_pin: int|str, flip_dir:bool=False):
        self.flip_dir = flip_dir
        self._MAX_PWM = 65534 # Motor holds when actually at full power

        self._in1DirPin = Pin(in1_direction_pin, Pin.OUT)
        self._in2SpeedPin = PWM(Pin(in2_speed_pin, Pin.OUT))
        self._in2SpeedPin.freq(50)

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
        self._in2SpeedPin.duty_u16(int(effort*self._MAX_PWM))

    def _set_direction(self, direction: int):
        if self.flip_dir:
            self._in1DirPin.value(not direction)
        else:
            self._in1DirPin.value(direction)

    def brake(self):
        # Motor holds with the real max duty cycle (65535)
        self._in2SpeedPin.duty_u16(self._MAX_PWM+1)

    def coast(self):
        self.set_effort(0)

class DualPWMMotor:
    """
    A simple class handling effort setting for DC motors on the XRP robots

    This version of the Motor class is used for the official release of the XRP
    """

    def __init__(self, in1_pwm_forward: int|str, in2_pwm_backward: int|str, flip_dir:bool=False):
        self.flip_dir = flip_dir
        self._MAX_PWM = 65535 # Motor holds when actually at full power

        self._in1ForwardPin = PWM(Pin(in1_pwm_forward, Pin.OUT))
        self._in2BackwardPin = PWM(Pin(in2_pwm_backward, Pin.OUT))
        self._in1ForwardPin.freq(50)
        self._in2BackwardPin.freq(50)

    def set_effort(self, effort: float):
        """
        Sets the effort value of the motor (corresponds to power)

        :param effort: The effort to set the motor to, between -1 and 1
        :type effort: float
        """

        in1Pwm = (effort < 0) ^ (self.flip_dir)
        if in1Pwm:
            self._in1ForwardPin.duty_u16(int(abs(effort)*self._MAX_PWM))
            self._in2BackwardPin.duty_u16(int(0))
        else:
            self._in1ForwardPin.duty_u16(int(0))
            self._in2BackwardPin.duty_u16(int(abs(effort)*self._MAX_PWM))

    def brake(self):
        """
        Powers the motor in both directions at the same time, enabling it to hold position
        """
        self._in1ForwardPin.duty_u16(int(self._MAX_PWM))
        self._in2BackwardPin.duty_u16(int(self._MAX_PWM))

    def coast(self):
        """
        Disables the motor in both directions at the same time, enabling it to spin freely
        """
        self._in1ForwardPin.duty_u16(int(0))
        self._in2BackwardPin.duty_u16(int(0))
        
                
