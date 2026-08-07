from .motor import SinglePWMMotor, DualPWMMotor
from .encoder import Encoder
from machine import Timer, Pin
from .controller import Controller
from .pid import PID
from .board import Board
from sys import implementation

class EncodedMotor:

    ZERO_EFFORT_BREAK = True
    ZERO_EFFORT_COAST = False

    # Speed control runs on a fixed-period timer, and the rpm <-> counts conversions depend on that period.
    _UPDATE_PERIOD_MS = 20
    _UPDATE_HZ = 1000 // _UPDATE_PERIOD_MS

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
        
        if "Beta" in implementation._machine:
            MotorImplementation = SinglePWMMotor
        else:
            MotorImplementation = DualPWMMotor

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
        elif index == 4 and hasattr(Pin.board, "MOTOR_4_IN_1"):
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

        # Velocity control = feedforward (kS breaks stiction, kV per unit speed) plus a proportional trim.
        if "NanoXRP" in implementation._machine:
            self.kS = 0.00
            self.kV = 0.00
            self.DEFAULT_SPEED_CONTROLLER = PID(kp=0.015)
        else:
            self.kS = 0.12
            self.kV = 0.02
            self.DEFAULT_SPEED_CONTROLLER = PID(kp=0.1)

        self.speedController = self.DEFAULT_SPEED_CONTROLLER

        # voltage_scale is measured once when Board is constructed; just hold a reference.
        self._board = Board.get_default_board()

        self.prev_position = 0
        self._counts_per_update = 0   # encoder counts moved in the last update period
        self.prev_speed = 0
        # Use a virtual timer so we can leave the hardware timers up for the user
        self.updateTimer = Timer(-1)
        # If the update timer is not running, start it at the update rate
        self.updateTimer.init(period=self._UPDATE_PERIOD_MS, callback=lambda t:self._update())


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

    def _counts_per_update_to_rpm(self, counts: float) -> float:
        # counts moved in one update period -> revolutions per minute
        return counts * 60 * self._UPDATE_HZ / self._encoder.resolution

    def _rpm_to_counts_per_update(self, rpm: float) -> float:
        # revolutions per minute -> counts moved in one update period
        return rpm * self._encoder.resolution / (60 * self._UPDATE_HZ)

    def get_speed(self) -> float:
        """
        :return: The speed of the motor, in rpm
        :rtype: float
        """
        return self._counts_per_update_to_rpm(self._counts_per_update)

    def set_speed(self, speed_rpm: float = None):
        """
        Sets target speed (in rpm) to be maintained passively
        Call with no parameters or 0 to turn off speed control

        :param target_speed_rpm: The target speed for the motor in rpm, or None
        :type target_speed_rpm: float, or None
        """
        if speed_rpm is None or speed_rpm == 0:
            self.target_speed = None
            self.prev_speed = 0   # forget direction; the controller is cleared right below
            self.set_effort(0)
            self.speedController.clear_history()
            return

        if self.prev_speed * speed_rpm < 0:
            self.speedController.clear_history()

        self.prev_speed = speed_rpm

        self.target_speed = self._rpm_to_counts_per_update(speed_rpm)

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
        self._counts_per_update = current_position - self.prev_position
        if self.target_speed is not None:
            error = self.target_speed - self._counts_per_update
            feedforward = (self.kS if self.target_speed > 0 else -self.kS) + self.kV * self.target_speed
            effort = (feedforward + self.speedController.update(error)) * self._board.voltage_scale
            self._motor.set_effort(max(-1.0, min(1.0, effort)))
        self.prev_position = current_position
