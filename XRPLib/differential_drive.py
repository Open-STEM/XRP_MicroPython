from .encoded_motor import EncodedMotor
from .imu import IMU
from .board import Board
from .controller import Controller
from .pid import PID
from .timeout import Timeout
import time
import math
from sys import implementation

class DifferentialDrive:

    _DEFAULT_DIFFERENTIAL_DRIVE_INSTANCE =None

    @classmethod
    def get_default_differential_drive(cls):

        """
        Get the default XRP differential drive instance. This is a singleton, so only one instance of the drivetrain will ever exist.
        """

        if cls._DEFAULT_DIFFERENTIAL_DRIVE_INSTANCE is None:
            cls._DEFAULT_DIFFERENTIAL_DRIVE_INSTANCE = cls(
            EncodedMotor.get_default_encoded_motor(index=1),
            EncodedMotor.get_default_encoded_motor(index=2),
            IMU.get_default_imu()
        )
            
        return cls._DEFAULT_DIFFERENTIAL_DRIVE_INSTANCE

    def __init__(self, left_motor: EncodedMotor, right_motor: EncodedMotor, imu: IMU = None, wheel_diam:float = 0.0, wheel_track:float = 0.0):
        """
        A Differential Drive class designed for the XRP two-wheeled drive robot.

        :param leftMotor: The left motor of the drivetrain
        :type leftMotor: EncodedMotor
        :param rightMotor: The right motor of the drivetrain
        :type rightMotor: EncodedMotor
        :param imu: The IMU of the robot. If None, the robot will not use the IMU for turning or maintaining heading.
        :type imu: IMU
        :param wheelDiam: The diameter of the wheels in inches. Defaults to 6 cm.
        :type wheelDiam: float
        :param wheelTrack: The distance between the wheels in inches. Defaults to 15.5 cm.
        :type wheelTrack: float
        """
        
        self.left_motor = left_motor
        self.right_motor = right_motor
        self.imu = imu

        self.brake_at_zero_power = False

        # Resolve hardware defaults when the caller leaves the arg at its 0.0 sentinel;
        # honor any explicit non-zero value that is passed in.
        if wheel_diam == 0.0:
            if "NanoXRP" in implementation._machine:
                self.wheel_diam = 3.46
            else:
                self.wheel_diam = 6.0
        else:
            self.wheel_diam = wheel_diam

        if wheel_track == 0.0:
            if "NanoXRP" in implementation._machine:
                self.wheel_track = 7.8
            else:
                self.wheel_track = 15.5
        else:
            self.wheel_track = wheel_track

        # Effort is raw PWM duty, so torque scales with pack voltage. Gains are tuned against
        # nominal_voltage and voltage_scale corrects the duty for the pack actually installed.
        if "NanoXRP" in implementation._machine:
            self.nominal_voltage = 4.2
        else:
            self.nominal_voltage = 6.0

        self.voltage_scale = 1.0
        self.update_voltage_compensation()

        self.heading_pid = None
        self.current_heading = None
        self.reset_heading = True
        self.turning = False

        if self.imu:
            self.heading_pid = PID( kp = 0.075, kd=0.001, )

    def update_voltage_compensation(self) -> float:
        """
        Re-measures the battery and updates the effort scale applied to straight() and turn().
        Called at construction; call it again after a battery swap or a long run.

        :return: The effort scale now in use
        :rtype: float
        """
        if self.nominal_voltage is None:
            return self.voltage_scale

        board = Board.get_default_board()
        voltage = sum(board.get_battery_voltage() for _ in range(8)) / 8
        self.voltage_scale = min(max(self.nominal_voltage / max(voltage, 3.5), 0.7), 1.6)

        return self.voltage_scale

    def set_effort(self, left_effort: float, right_effort: float) -> None:
        """
        Set the raw effort of both motors individually

        :param leftEffort: The power (Bounded from -1 to 1) to set the left motor to.
        :type leftEffort: float
        :param rightEffort: The power (Bounded from -1 to 1) to set the right motor to.
        :type rightEffort: float
        """

        self.left_motor.set_effort(left_effort)
        self.right_motor.set_effort(right_effort)

    def set_speed(self, left_speed: float, right_speed: float) -> None:
        """
        Set the speed of both motors individually

        :param leftSpeed: The speed (In Centimeters per Second) to set the left motor to.
        :type leftSpeed: float
        :param rightSpeed: The speed (In Centimeters per Second) to set the right motor to.
        :type rightSpeed: float
        """
        # Convert from cm/s to RPM
        cmpsToRPM = 60 / (math.pi * self.wheel_diam)
        self.left_motor.set_speed(left_speed*cmpsToRPM)
        self.right_motor.set_speed(right_speed*cmpsToRPM)

    def set_zero_effort_behavior(self, brake_at_zero_effort):

        """
        Sets the behavior of both motor at 0 effort to either brake (hold position) or coast (free spin)
        :param brake_at_zero_effort: Whether or not to brake at 0 effort. Can use EncodedMotor.ZERO_EFFORT_BREAK or EncodedMotor.ZERO_EFFORT_COAST for clarity.
        :type brake_at_zero_effort: bool
        """
        self.left_motor.set_zero_effort_behavior(brake_at_zero_effort)
        self.right_motor.set_zero_effort_behavior(brake_at_zero_effort)

    def stop(self) -> None:
        """
        Stops both drivetrain motors by setting power to zero.
        """
        self.left_motor.set_speed()
        self.right_motor.set_speed()
        self.set_effort(0,0)

    def arcade(self, straight:float, turn:float):
        """
        Sets the raw effort of both motors based on the arcade drive scheme

        :param straight: The base effort (Bounded from -1 to 1) used to drive forwards or backwards.
        :type straight: float
        :param turn: The modifier effort (Bounded from -1 to 1) used to skew robot left (positive) or right (negative).
        :type turn: float
        """
        if straight == 0 and turn == 0:
            self.set_effort(0, 0)
        else:
            scale = max(abs(straight), abs(turn))/(abs(straight) + abs(turn))
            left_speed = (straight - turn)*scale
            right_speed = (straight + turn)*scale

            if not self.heading_pid:
                # if not using IMU assist to maintain heading, just pass down the left and right motor
                # speeds to control movement
                self.set_effort(left_speed, right_speed)
            else:
                # else if IMU assist is enabled, then use the IMU with PID to
                # maintain a constant heading while driving.
                if turn == 0:
                    # straight drive requested, then maintain the current heading
                    if self.turning:
                        # if previously turning, then clear the turn indicator and reset the course heading
                        self.reset_heading = True
                        self.turning = False

                    if self.reset_heading:
                        self.reset_heading = False
                        self.current_heading = self.imu.get_yaw()

                    # use the PID to set the heading correction based on the current heading
                    heading_correction = self.heading_pid.update(self.current_heading - self.imu.get_yaw())

                    self.set_effort(left_speed - heading_correction, right_speed + heading_correction)
                else:
                    # set the turning indicator and apply the left and right speeds
                    self.turning = True
                    self.set_effort(left_speed, right_speed)

    def reset_encoder_position(self) -> None:
        """
        Resets the position of both motors' encoders to 0
        """

        self.left_motor.reset_encoder_position()
        self.right_motor.reset_encoder_position()

    def get_left_encoder_position(self) -> float:
        """
        :return: the current position of the left motor's encoder in cm.
        :rtype: float
        """
        return self.left_motor.get_position()*math.pi*self.wheel_diam

    def get_right_encoder_position(self) -> float:
        """
        :return: the current position of the right motor's encoder in cm.
        :rtype: float
        """
        return self.right_motor.get_position()*math.pi*self.wheel_diam


    def _move(self, distance_target: float, heading_target: float, max_effort: float, min_effort: float, timeout: float, use_imu: bool,
              distance_controller: Controller = None, heading_controller: Controller = None) -> bool:
        """
        Shared translation/rotation controller for straight() and turn().
        """

        if "NanoXRP" in implementation._machine:
            if min_effort is None:
                min_effort = 0.10   

            if distance_controller is None:
                distance_controller = PID(
                    kp = 0.32,
                    kd = 0.0184,
                    max_output = max_effort,
                    tolerance = 0.2,
                    tolerance_count = 10,
                )

            if heading_controller is None:
                heading_controller = PID(
                    kp = 0.014,
                    kd = 0.001,
                    max_output = max_effort,
                    tolerance = 1,
                    tolerance_count = 10,
                )
        else:
            if min_effort is None:
                min_effort = 0.14

            if distance_controller is None:
                distance_controller = PID(
                    kp = 3.5,
                    kd = 0.1,
                    max_output = max_effort,
                    tolerance = 0.1,
                    tolerance_count = 10,
                )

            if heading_controller is None:
                heading_controller = PID(
                    kp = 0.064,
                    kd = 0.0045,
                    max_output = max_effort,
                    tolerance = 0.5,
                    tolerance_count = 10,
                )

        # a Controller that carries no tolerance keeps the effort floor on for the whole move
        distance_tolerance = getattr(distance_controller, "tolerance", 0)
        heading_tolerance = getattr(heading_controller, "tolerance", 0)

        min_effort = min(abs(min_effort), max_effort)

        time_out = Timeout(timeout)
        starting_left = self.get_left_encoder_position()
        starting_right = self.get_right_encoder_position()
        use_imu = use_imu and (self.imu is not None)
        starting_heading = self.imu.get_yaw() if use_imu else 0

        while True:

            left_delta = self.get_left_encoder_position() - starting_left
            right_delta = self.get_right_encoder_position() - starting_right

            if use_imu:
                heading = self.imu.get_yaw() - starting_heading
            else:
                heading = ((right_delta - left_delta) / 2) * 360 / (self.wheel_track * math.pi)

            distance_error = distance_target - (left_delta + right_delta) / 2
            heading_error = heading_target - heading

            translation = distance_controller.update(distance_error)
            rotation = heading_controller.update(heading_error)

            if (distance_controller.is_done() or distance_target == 0) and (heading_controller.is_done() or heading_target == 0):
                break
            if (time_out.is_done()):
                break

            left = translation - rotation
            right = translation + rotation

            # only hold the effort floor while an axis is still outside its tolerance
            correcting = abs(distance_error) > distance_tolerance or abs(heading_error) > heading_tolerance

            effort = max(abs(left), abs(right))
            if effort > max_effort:
                left, right = left * max_effort / effort, right * max_effort / effort
            elif correcting and 0 < effort < min_effort:
                left, right = left * min_effort / effort, right * min_effort / effort

            self.set_effort(left * self.voltage_scale, right * self.voltage_scale)

            time.sleep(0.01)

        self.stop()

        return not time_out.is_done()


    def straight(self, distance: float, max_effort: float = 0.5, timeout: float = None, main_controller: Controller = None, secondary_controller: Controller = None, min_effort: float = None) -> bool:
        """
        Go forward the specified distance in centimeters, and exit function when distance has been reached.
        Max_effort is bounded from -1 (reverse at full speed) to 1 (forward at full speed)

        :param distance: The distance for the robot to travel (In Centimeters)
        :type distance: float
        :param max_effort: The max effort for which the robot to travel (Bounded from -1 to 1). Default is half effort forward
        :type max_effort: float
        :param timeout: The amount of time before the robot stops trying to move forward and continues to the next step (In Seconds)
        :type timeout: float
        :param main_controller: The main controller, for handling the distance driven forwards
        :type main_controller: Controller
        :param secondary_controller: The secondary controller, for correcting heading error that may result during the drive.
        :type secondary_controller: Controller
        :param min_effort: The minimum effort applied to the motors while moving. Defaults to a board specific value
        :type min_effort: float
        :return: if the distance was reached before the timeout
        :rtype: bool
        """

        turn_degrees = 0

        # ensure effort is always positive while distance could be either positive or negative
        if max_effort < 0:
            max_effort *= -1
            distance *= -1

        return self._move(distance, turn_degrees, max_effort, min_effort, timeout, True, main_controller, secondary_controller)


    def turn(self, turn_degrees: float, max_effort: float = 0.5, timeout: float = None, main_controller: Controller = None, secondary_controller: Controller = None, use_imu:bool = True, min_effort: float = None) -> bool:
        """
        Turn the robot some relative heading given in turnDegrees, and exit function when the robot has reached that heading.
        effort is bounded from -1 (turn counterclockwise the relative heading at full speed) to 1 (turn clockwise the relative heading at full speed)
        Uses the IMU to determine the heading of the robot and P control for the motor controller.

        :param turnDegrees: The number of angle for the robot to turn (In Degrees)
        :type turnDegrees: float
        :param max_effort: The max speed for which the robot to travel (Bounded from -1 to 1)
        :type max_effort: float
        :param timeout: The amount of time before the robot stops trying to turn and continues to the next step (In Seconds)
        :type timeout: float
        :param main_controller: The main controller, for handling the angle turned
        :type main_controller: Controller
        :param secondary_controller: The secondary controller, for maintaining position during the turn by controlling the encoder count difference
        :type secondary_controller: Controller
        :param use_imu: A boolean flag that changes if the main controller bases its movement off of the imu (True) or the encoders (False)
        :type use_imu: bool
        :param min_effort: The minimum effort applied to the motors while turning. Defaults to a board specific value
        :type min_effort: float
        :return: if the distance was reached before the timeout
        :rtype: bool
        """
        distance = 0

        if max_effort < 0:
            max_effort = -max_effort
            turn_degrees = -turn_degrees

        return self._move(distance, turn_degrees, max_effort, min_effort, timeout, use_imu, secondary_controller, main_controller)
