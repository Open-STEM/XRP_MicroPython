from .motor import Motor
from .encoder import Encoder
from machine import Timer

class EncodedMotor:

    _DEFAULT_LEFT_MOTOR_INSTANCE = None
    _DEFAULT_RIGHT_MOTOR_INSTANCE = None

    @classmethod
    def get_default_left_motor(cls):
        """
        Get the default XRP v2 left motor instance. This is a singleton, so only one instance of the drivetrain will ever exist.
        Motor pins set to 6 and 7 and the encoder pins set to 4 and 5
        """

        if cls._DEFAULT_LEFT_MOTOR_INSTANCE is None:
            cls._DEFAULT_LEFT_MOTOR_INSTANCE = cls(
                Motor(6, 7, flip_dir=True),
                Encoder(4, 5)
            )

        return cls._DEFAULT_LEFT_MOTOR_INSTANCE
    
    @classmethod
    def get_default_right_motor(cls):
        """
        Get the default XRP v2 right motor instance. This is a singleton, so only one instance of the drivetrain will ever exist.
        Motor pins set to 14 and 15 and the encoder pins set to 12 and 13
        """

        if cls._DEFAULT_RIGHT_MOTOR_INSTANCE is None:
            cls._DEFAULT_RIGHT_MOTOR_INSTANCE = cls(
                Motor(14, 15),
                Encoder(12, 13)
            )

        return cls._DEFAULT_RIGHT_MOTOR_INSTANCE
    
    def __init__(self, motor: Motor, encoder: Encoder):
        
        self._motor = motor
        self._encoder = encoder

        # PI Control Constants for motor sped
        self.kp = 5
        self.ki = 0.25

        self.target_speed = None
        self.speed = 0
        self.prev_position = 0
        self.errorSum = 0
        # Use a virtual timer so we can leave the hardware timers up for the user
        self.updateTimer = Timer(-1)

    def set_effort(self, effort: float):
        self._motor.set_effort(effort)

    def get_position(self):
        if self._motor.flip_dir:
            invert = -1
        else:
            invert = 1
        return self._encoder.get_position()*invert
    
    def get_position_ticks(self):
        if self._motor.flip_dir:
            invert = -1
        else:
            invert = 1
        return self._encoder.get_position_ticks()*invert

    def reset_encoder_position(self):
        self._encoder.reset_encoder_position()

    def get_speed(self):
        return self.speed*3000

    def set_target_speed(self, target_speed_rpm:float = None):
        """
        Sets target speed (in rpm) to be maintained passively using PI Control
        """
        if target_speed_rpm is None:
            self.target_speed = None
            self.set_effort(0)
            return
        # If the update timer is not running, start it at 100 Hz (20ms updates)
        self.updateTimer.init(period=20, callback=lambda t:self.update())
        # Convert from rev per min to rev per 10ms
        self.target_speed = target_speed_rpm/(60*50)

    def set_PI_constants(self, new_kp:float, new_ki:float):
        """
        Sets the Proportional and Integration constants for speed control
        """
        self.kp = new_kp
        self.ki = new_ki
        self.errorSum = 0

    def update(self):

        current_position = self.get_position()
        self.speed = current_position - self.prev_position
        if self.target_speed is not None:
            error = self.target_speed - self.speed
            self.errorSum += error
            self._motor.set_effort(self.kp * error + self.ki * self.errorSum)
        else:
            self.errorSum = 0
            self.updateTimer.deinit()

        self.prev_position = current_position

