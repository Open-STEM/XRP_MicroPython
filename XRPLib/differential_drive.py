from .encoded_motor import EncodedMotor
from .imu import IMU
from .controller import Controller
from .pid import PID
from .timeout import Timeout
import time
import math

class DifferentialDrive:

    _DEFAULT_DIFFERENTIAL_DRIVE_INSTANCE =None

    @classmethod
    def get_default_differential_drive(cls):

        """
        Get the default XRP v2 differential drive instance. This is a singleton, so only one instance of the drivetrain will ever exist.
        """

        if cls._DEFAULT_DIFFERENTIAL_DRIVE_INSTANCE is None:
            cls._DEFAULT_DIFFERENTIAL_DRIVE_INSTANCE = cls(
            EncodedMotor.get_default_encoded_motor(index=1),
            EncodedMotor.get_default_encoded_motor(index=2),
            IMU.get_default_imu()
        )
            
        return cls._DEFAULT_DIFFERENTIAL_DRIVE_INSTANCE

    def __init__(self, left_motor: EncodedMotor, right_motor: EncodedMotor, imu: IMU = None, wheel_diam:float = 6.0, wheel_track:float = 15.5):
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

        self.wheel_diam = wheel_diam
        self.track_width = wheel_track

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

    def stop(self) -> None:
        """
        Stops both drivetrain motors
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


    def straight(self, distance: float, max_effort: float = 0.5, timeout: float = None, main_controller: Controller = None, secondary_controller: Controller = None) -> bool:
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
        :return: if the distance was reached before the timeout
        :rtype: bool
        """
        # ensure effort is always positive while distance could be either positive or negative
        if max_effort < 0:
            max_effort *= -1
            distance *= -1

        time_out = Timeout(timeout)
        starting_left = self.get_left_encoder_position()
        starting_right = self.get_right_encoder_position()


        if main_controller is None:
            main_controller = PID(
                kp = 0.1,
                ki = 0.04,
                kd = 0.04,
                min_output = 0.3,
                max_output = max_effort,
                max_integral = 10,
                tolerance = 0.25,
                tolerance_count = 3,
            )

        # Secondary controller to keep encoder values in sync
        if secondary_controller is None:
            secondary_controller = PID(
                kp = 0.075, kd=0.001,
            )

        if self.imu is not None:
            # record current heading to maintain it
            initial_heading = self.imu.get_yaw()
        else:
            initial_heading = 0

        while True:

            # calculate the distance traveled
            left_delta = self.get_left_encoder_position() - starting_left
            right_delta = self.get_right_encoder_position() - starting_right
            dist_traveled = (left_delta + right_delta) / 2

            # PID for distance
            distance_error = distance - dist_traveled
            effort = main_controller.update(distance_error)
            
            if main_controller.is_done() or time_out.is_done():
                break

            # calculate heading correction
            if self.imu is not None:
                # record current heading to maintain it
                current_heading = self.imu.get_yaw()
            else:
                current_heading = ((right_delta-left_delta)/2)*360/(self.track_width*math.pi)

            headingCorrection = secondary_controller.update(initial_heading - current_heading)
            
            self.set_effort(effort - headingCorrection, effort + headingCorrection)

            time.sleep(0.01)

        self.stop()

        return not time_out.is_done()


    def turn(self, turn_degrees: float, max_effort: float = 0.5, timeout: float = None, main_controller: Controller = None, secondary_controller: Controller = None, use_imu:bool = True) -> bool:
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
        :return: if the distance was reached before the timeout
        :rtype: bool
        """

        if max_effort < 0:
            max_effort = -max_effort
            turn_degrees = -turn_degrees

        time_out = Timeout(timeout)
        starting_left = self.get_left_encoder_position()
        starting_right = self.get_right_encoder_position()

        if main_controller is None:
            main_controller = PID(
                kp = 0.02,
                ki = 0.001,
                kd = 0.00165,
                min_output = 0.35,
                max_output = max_effort,
                max_integral = 75,
                tolerance = 1,
                tolerance_count = 3
            )

        # Secondary controller to keep encoder values in sync
        if secondary_controller is None:
            secondary_controller = PID(
                kp = 0.8,
            )
 
        if use_imu and (self.imu is not None):
            turn_degrees += self.imu.get_yaw()

        while True:
            
            # calculate encoder correction to minimize drift
            left_delta = self.get_left_encoder_position() - starting_left
            right_delta = self.get_right_encoder_position() - starting_right
            encoder_correction = secondary_controller.update(left_delta + right_delta)

            if use_imu and (self.imu is not None):
                # calculate turn error (in degrees) from the imu
                turn_error = turn_degrees - self.imu.get_yaw()
            else:
                # calculate turn error (in degrees) from the encoder counts
                turn_error = turn_degrees - ((right_delta-left_delta)/2)*360/(self.track_width*math.pi)

            # Pass the turn error to the main controller to get a turn speed
            turn_speed = main_controller.update(turn_error)
            
            # exit if timeout or tolerance reached
            if main_controller.is_done() or time_out.is_done():
                break

            self.set_effort(-turn_speed - encoder_correction, turn_speed - encoder_correction)

            time.sleep(0.01)

        self.stop()

        return not time_out.is_done()
