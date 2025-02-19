from machine import Pin, PWM
import sys

class Servo:

    _DEFAULT_SERVO_ONE_INSTANCE = None
    _DEFAULT_SERVO_TWO_INSTANCE = None
    _DEFAULT_SERVO_THREE_INSTANCE = None
    _DEFAULT_SERVO_FOUR_INSTANCE = None

    @classmethod
    def get_default_servo(cls, index:int):
        """
        Gets one of the default XRP servo instances. These are singletons, so only one instance of each servo will ever exist.
        Raises an exception if an invalid index is requested.

        :param index: The index of the servo to get (1-4; Beta only has 1 and 2)
        :type index: int
        """
        if index == 1:
            if cls._DEFAULT_SERVO_ONE_INSTANCE is None:
                cls._DEFAULT_SERVO_ONE_INSTANCE = cls("SERVO_1")
            servo = cls._DEFAULT_SERVO_ONE_INSTANCE
        elif index == 2:
            if cls._DEFAULT_SERVO_TWO_INSTANCE is None:
                cls._DEFAULT_SERVO_TWO_INSTANCE = cls("SERVO_2")
            servo = cls._DEFAULT_SERVO_TWO_INSTANCE
        elif index == 3 and hasattr(Pin.board, "SERVO_3"):
            if cls._DEFAULT_SERVO_THREE_INSTANCE is None:
                cls._DEFAULT_SERVO_THREE_INSTANCE = cls("SERVO_3")
            servo = cls._DEFAULT_SERVO_THREE_INSTANCE
        elif index == 4 and hasattr(Pin.board, "SERVO_4"):
            if cls._DEFAULT_SERVO_FOUR_INSTANCE is None:
                cls._DEFAULT_SERVO_FOUR_INSTANCE = cls("SERVO_4")
            servo = cls._DEFAULT_SERVO_FOUR_INSTANCE
        else:
            return Exception("Invalid servo index")
        return servo

    def __init__(self, signal_pin: int|str):
        """
        A simple class for interacting with a servo through PWM
        
        :param signal_pin: The pin the servo is connected to
        :type signal_pin: int | str
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
