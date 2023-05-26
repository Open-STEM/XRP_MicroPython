from machine import Pin, PWM

class Servo:

    """
    A simple class for interacting with a servo through PWM
    """

    _DEFAULT_SERVO_INSTANCE = None

    @classmethod
    def get_default_servo(cls):
        """
        Get the default XRP v2 servo instance. This is a singleton, so only one instance of the servo will ever exist.
        """
        if cls._DEFAULT_SERVO_INSTANCE is None:
            cls._DEFAULT_SERVO_INSTANCE = cls(16)
        return cls._DEFAULT_SERVO_INSTANCE

    def __init__(self, signal_pin:int):
        self._servo = PWM(Pin(signal_pin, Pin.OUT))
        # Initialize base frequency for the PWM
        self._servo.freq(50)
        self.MICROSEC_PER_DEGREE: int = 10000
        self.LOW_ANGLE_OFFSET: int = 1000000

    def set_angle(self, degrees: float):
        """
        Sets the angle of the servo
        :param degrees: The angle to set the servo to [0,135]
        :ptype degrees: float
        """
        self._servo.duty_ns(int(degrees * self.MICROSEC_PER_DEGREE + self.LOW_ANGLE_OFFSET))

    def free(self):
        self._servo.duty_ns(0)
