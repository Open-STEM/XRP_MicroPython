from machine import Pin, PWM

class Servo:

    _DEFAULT_SERVO_ONE_INSTANCE = None
    _DEFAULT_SERVO_TWO_INSTANCE = None

    @classmethod
    def get_default_servo(cls, index:int):
        """
        Gets one of the default XRP v2 servo instances. These are singletons, so only one instance of each servo will ever exist.
        Raises an exception if an invalid index is requested.

        :param index: The index of the servo to get (1 or 2)
        :type index: int
        """
        if index == 1:
            if cls._DEFAULT_SERVO_ONE_INSTANCE is None:
                cls._DEFAULT_SERVO_ONE_INSTANCE = cls(16)
            servo = cls._DEFAULT_SERVO_ONE_INSTANCE
        elif index == 2:
            if cls._DEFAULT_SERVO_TWO_INSTANCE is None:
                cls._DEFAULT_SERVO_TWO_INSTANCE = cls(17)
            servo = cls._DEFAULT_SERVO_TWO_INSTANCE
        else:
            return Exception("Invalid servo index")
        return servo

    def __init__(self, signal_pin:int):
        """
        A simple class for interacting with a servo through PWM
        
        :param signal_pin: The pin the servo is connected to
        :type signal_pin: int
        """

        self._servo = PWM(Pin(signal_pin, Pin.OUT))
        # Initialize base frequency for the PWM
        self._servo.freq(50)
        self.MICROSEC_PER_DEGREE: int = 10000
        self.LOW_ANGLE_OFFSET: int = 500000

    def set_angle(self, degrees: float):
        """
        Sets the angle of the servo
        :param degrees: The angle to set the servo to [0,200]
        :ptype degrees: float
        """
        self._servo.duty_ns(int(degrees * self.MICROSEC_PER_DEGREE + self.LOW_ANGLE_OFFSET))

    def free(self):
        """
        Allows the servo to spin freely without holding position
        """
        self._servo.duty_ns(0)
