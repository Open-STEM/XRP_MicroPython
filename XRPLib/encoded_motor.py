from .motor import Motor
from .encoder import Encoder
from machine import Timer
from .controller import Controller
from .pid import PID
from .timeout import Timeout
import time

class EncodedMotor:

    _DEFAULT_LEFT_MOTOR_INSTANCE = None
    _DEFAULT_RIGHT_MOTOR_INSTANCE = None
    _DEFAULT_MOTOR_THREE_INSTANCE = None
    _DEFAULT_MOTOR_FOUR_INSTANCE = None

    @classmethod
    def get_default_encoded_motor(cls, index:int = 1):
        """
        Get one of the default XRP v2 motor instances. These are singletons, so only one instance of each of these will ever exist.
        Raises an exception if an invalid index is requested.

        :param index: The index of the motor to get; 1 for left, 2 for right, 3 for motor 3, 4 for motor 4
        :type index: int
        """
        if index == 1:
            if cls._DEFAULT_LEFT_MOTOR_INSTANCE is None:
                cls._DEFAULT_LEFT_MOTOR_INSTANCE = cls(
                    Motor(6, 7, flip_dir=True),
                    Encoder(0, 4, 5)
                )
            motor = cls._DEFAULT_LEFT_MOTOR_INSTANCE
        elif index == 2:
            if cls._DEFAULT_RIGHT_MOTOR_INSTANCE is None:
                cls._DEFAULT_RIGHT_MOTOR_INSTANCE = cls(
                    Motor(14, 15),
                    Encoder(1, 12, 13)
                )
            motor = cls._DEFAULT_RIGHT_MOTOR_INSTANCE
        elif index == 3:
            if cls._DEFAULT_MOTOR_THREE_INSTANCE is None:
                cls._DEFAULT_MOTOR_THREE_INSTANCE = cls(
                    Motor(2, 3),
                    Encoder(2, 0, 1)
                )
            motor = cls._DEFAULT_MOTOR_THREE_INSTANCE
        elif index == 4:
            if cls._DEFAULT_MOTOR_FOUR_INSTANCE is None:
                cls._DEFAULT_MOTOR_FOUR_INSTANCE = cls(
                    Motor(10, 11, flip_dir=True),
                    Encoder(3, 8, 9)
                )
            motor = cls._DEFAULT_MOTOR_FOUR_INSTANCE
        else:
            return Exception("Invalid motor index")
        return motor
    
    def __init__(self, motor: Motor, encoder: Encoder):
        
        self._motor = motor
        self._encoder = encoder

        self.target_speed = None
        self.DEFAULT_SPEED_CONTROLLER = PID(
            kp=0.035,
            ki=0.03,
            kd=0,
        )
        self.speedController = self.DEFAULT_SPEED_CONTROLLER
        self.prev_position = 0
        self.speed = 0
        # Use a virtual timer so we can leave the hardware timers up for the user
        self.updateTimer = Timer(-1)
        # If the update timer is not running, start it at 50 Hz (20ms updates)
        self.updateTimer.init(period=20, callback=lambda t:self._update())

    def set_effort(self, effort: float):
        """
        :param effort: The effort to set this motor to, from -1 to 1
        :type effort: float
        """
        self._motor.set_effort(effort)

    def get_position(self) -> float:
        """
        :return: The position of the encoded motor, in revolutions, relative to the last time reset was called.
        :rtype: float
        """
        if self._motor.flip_dir:
            invert = -1
        else:
            invert = 1
        return self._encoder.get_position()*invert
    
    def get_position_counts(self) -> int:
        """
        :return: The position of the encoded motor, in encoder counts, relative to the last time reset was called.
        :rtype: int
        """
        if self._motor.flip_dir:
            invert = -1
        else:
            invert = 1
        return self._encoder.get_position_counts()*invert

    def reset_encoder_position(self):
        """
        Resets the encoder position back to zero.
        """
        self._encoder.reset_encoder_position()

    def get_speed(self) -> float:
        """
        :return: The speed of the motor, in rpm
        :rtype: float
        """
        # Convert from counts per 20ms to rpm (60 sec/min, 50 Hz)
        return self.speed*(60*50)/self._encoder.resolution

    def set_speed(self, speed_rpm: float = None):
        """
        Sets target speed (in rpm) to be maintained passively
        Call with no parameters or 0 to turn off speed control

        :param target_speed_rpm: The target speed for the motor in rpm, or None
        :type target_speed_rpm: float, or None
        """
        if speed_rpm is None or speed_rpm == 0:
            self.target_speed = None
            self.set_effort(0)
            return
        # Convert from rev per min to counts per 20ms (60 sec/min, 50 Hz)
        self.target_speed = speed_rpm*self._encoder.resolution/(60*50)
        self.speedController.clear_history()
        self.prev_position = self.get_position_counts()

    def set_speed_controller(self, new_controller: Controller):
        """
        Sets a new controller for speed control

        :param new_controller: The new Controller for speed control
        :type new_controller: Controller
        """
        self.speedController = new_controller
        self.speedController.clear_history()

    def _update(self):
        """
        Non-api method; used for updating motor efforts for speed control
        """
        current_position = self.get_position_counts()
        self.speed = current_position - self.prev_position
        if self.target_speed is not None:
            error = self.target_speed - self.speed
            effort = self.speedController.update(error)
            self._motor.set_effort(effort)
        self.prev_position = current_position

    def rotate(self, degrees: float, max_effort: float = 0.5, timeout: float = None, main_controller: Controller = None) -> bool:
        """
        Rotate the motor by some number of degrees, and exit function when distance has been traveled.
        Max_effort is bounded from -1 (reverse at full speed) to 1 (forward at full speed)

        :param degrees: The distance for the motor to rotate (In Degrees)
        :type degrees: float
        :param max_effort: The max effort for which the robot to travel (Bounded from -1 to 1). Default is half effort forward
        :type max_effort: float
        :param timeout: The amount of time before the robot stops trying to move forward and continues to the next step (In Seconds)
        :type timeout: float
        :param main_controller: The main controller, for handling the motor's rotation
        :type main_controller: Controller
        :return: if the distance was reached before the timeout
        :rtype: bool
        """
        # ensure effort is always positive while distance could be either positive or negative
        if max_effort < 0:
            max_effort *= -1
            degrees *= -1

        time_out = Timeout(timeout)
        starting = self.get_position_counts()

        degrees *= self._encoder.resolution/360

        if main_controller is None:
            main_controller = PID(
                kp = 0.1,
                ki = 0.065,
                kd = 0.0275,
                min_output = 0.3,
                max_output = max_effort,
                max_integral = 25,
                tolerance = 3,
                tolerance_count = 3,
            )


        while True:

            # calculate the distance traveled
            delta = self.get_position_counts() - starting

            # PID for distance
            error = degrees - delta
            effort = main_controller.update(error)
            
            if main_controller.is_done() or time_out.is_done():
                break

            self.set_effort(effort)

            time.sleep(0.01)

        self.set_effort(0)

        return not time_out.is_done()