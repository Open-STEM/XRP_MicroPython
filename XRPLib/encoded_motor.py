from .motor import SinglePWMMotor, DualPWMMotor
from .encoder import Encoder
from machine import Timer
from .controller import Controller
from .pid import PID
import sys

class EncodedMotor:

    ZERO_EFFORT_BREAK = True
    ZERO_EFFORT_COAST = False

    _DEFAULT_LEFT_MOTOR_INSTANCE = None
    _DEFAULT_RIGHT_MOTOR_INSTANCE = None
    _DEFAULT_MOTOR_THREE_INSTANCE = None
    _DEFAULT_MOTOR_FOUR_INSTANCE = None

    @classmethod
    def get_default_encoded_motor(cls, index:int = 1):
        """
        Get one of the default XRP motor instances. These are singletons, so only one instance of each of these will ever exist.
        Raises an exception if an invalid index is requested.

        :param index: The index of the motor to get; 1 for left, 2 for right, 3 for motor 3, 4 for motor 4
        :type index: int
        """
        
        if "RP2350" in sys.implementation._machine:
            MotorImplementation = DualPWMMotor
        else:
            MotorImplementation = SinglePWMMotor

        if index == 1:
            if cls._DEFAULT_LEFT_MOTOR_INSTANCE is None:
                cls._DEFAULT_LEFT_MOTOR_INSTANCE = cls(
                    MotorImplementation("MOTOR_L_IN_1", "MOTOR_L_IN_2", flip_dir=True),
                    Encoder(0, "MOTOR_L_ENCODER_A", "MOTOR_L_ENCODER_B")
                )
            motor = cls._DEFAULT_LEFT_MOTOR_INSTANCE
        elif index == 2:
            if cls._DEFAULT_RIGHT_MOTOR_INSTANCE is None:
                cls._DEFAULT_RIGHT_MOTOR_INSTANCE = cls(
                    MotorImplementation("MOTOR_R_IN_1", "MOTOR_R_IN_2"),
                    Encoder(1, "MOTOR_R_ENCODER_A", "MOTOR_R_ENCODER_B")
                )
            motor = cls._DEFAULT_RIGHT_MOTOR_INSTANCE
        elif index == 3:
            if cls._DEFAULT_MOTOR_THREE_INSTANCE is None:
                cls._DEFAULT_MOTOR_THREE_INSTANCE = cls(
                    MotorImplementation("MOTOR_3_IN_1", "MOTOR_3_IN_2", flip_dir=True),
                    Encoder(2, "MOTOR_3_ENCODER_A", "MOTOR_3_ENCODER_B")
                )
            motor = cls._DEFAULT_MOTOR_THREE_INSTANCE
        elif index == 4:
            if cls._DEFAULT_MOTOR_FOUR_INSTANCE is None:
                cls._DEFAULT_MOTOR_FOUR_INSTANCE = cls(
                    MotorImplementation("MOTOR_4_IN_1", "MOTOR_4_IN_2"),
                    Encoder(3, "MOTOR_4_ENCODER_A", "MOTOR_4_ENCODER_B")
                )
            motor = cls._DEFAULT_MOTOR_FOUR_INSTANCE
        else:
            return Exception("Invalid motor index")
        return motor
    
    def __init__(self, motor, encoder: Encoder):
        
        self._motor = motor
        self._encoder = encoder

        self.brake_at_zero = False

        self.target_speed = None
        self.DEFAULT_SPEED_CONTROLLER = PID(
            kp=0.035,
            ki=0.03,
            kd=0,
            max_integral=50
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
        if self.brake_at_zero and effort == 0:
            self.brake()
        else:
            self._motor.set_effort(effort)
    
    # EncodedMotor.set_zero_effort_behavior(EncodedMotor.ZERO_POWER_BRAKE)
    def set_zero_effort_behavior(self, brake_at_zero_effort):
        """
        Sets the behavior of the motor at 0 effort to either brake (hold position) or coast (free spin)
        :param brake_at_zero_effort: Whether or not to brake at 0 effort. Can use EncodedMotor.ZERO_EFFORT_BREAK or EncodedMotor.ZERO_EFFORT_COAST for clarity.
        :type brake_at_zero_effort: bool
        """
        self.brake_at_zero = brake_at_zero_effort

    def brake(self):
        """
        Causes the motor to resist rotation.
        """
        # Exact impl of brake depends on which board is being used. 
        self._motor.brake()

    def coast(self):
        """
        Allows the motor to spin freely.
        """
        self._motor.coast()

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