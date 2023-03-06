from machine import Pin, PWM

class Servo:

    """
    A simple class for interacting with a servo through PWM
    """

    def __init__(self, signalPin):
        self.servo = PWM(Pin(signalPin, Pin.OUT))
        # Initialize base frequency for the PWM
        self.servo.freq(50)
        self.MICROSEC_PER_DEGREE: int = 10000
        self.LOW_ANGLE_OFFSET: int = 1000000

    def set_angle(self, degrees):
        """
        Sets the angle of the servo
        :param degrees: The angle to set the servo to [0,135]
        :ptype degrees: float
        """
        self.servo.duty_ns(int(degrees * self.MICROSEC_PER_DEGREE + self.LOW_ANGLE_OFFSET))

    def free(self):
        self.servo.duty_ns(0)
