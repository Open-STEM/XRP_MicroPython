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
            EncodedMotor.get_default_encoded_motor(0),
            EncodedMotor.get_default_encoded_motor(1),
            IMU.get_default_imu()
        )
            
        return cls._DEFAULT_DIFFERENTIAL_DRIVE_INSTANCE

    def __init__(self, left_motor: EncodedMotor, right_motor: EncodedMotor, imu: IMU | None = None, wheel_diam:float = 6.0, wheel_track:float = 13.5):
        self.left_motor = left_motor
        self.right_motor = right_motor
        self.imu = imu

        self.wheel_diam = wheel_diam
        self.track_width = wheel_track

    def set_effort(self, left_effort: float, right_effort: float) -> None:
        """
        Set the raw effort of both motors individually

        : param leftEffort: The power (Bounded from -1 to 1) to set the left motor to.
        : type leftEffort: float
        : param rightEffort: The power (Bounded from -1 to 1) to set the right motor to.
        : type rightEffort: float
        """

        self.left_motor.set_effort(left_effort)
        self.right_motor.set_effort(right_effort)

    def stop(self) -> None:
        """
        Stops both drivetrain motors
        """
        self.set_effort(0,0)

    def reset_encoder_position(self) -> None:
        """
        Set the position of the motors' encoders in degrees. Note that this does not actually move the motor but just recalibrates the stored encoder value.
        If only one encoder position is specified, the encoders for each motor will be set to that position.
        """

        self.left_motor.reset_encoder_position()
        self.right_motor.reset_encoder_position()

    def get_left_encoder_position(self) -> float:
        """
        Return the current position of the left motor's encoder in revolutions.
        """
        return self.left_motor.get_position()

    def get_right_encoder_position(self) -> float:
        """
        Return the current position of the right motor's encoder in revolutions.
        """
        return self.right_motor.get_position()


    def straight(self, distance: float, max_effort: float = 0.5, timeout: float = None, main_controller: Controller = None, secondary_controller: Controller = None) -> bool:
        """
        Go forward the specified distance in centimeters, and exit function when distance has been reached.
        Speed is bounded from -1 (reverse at full speed) to 1 (forward at full speed)

        : param distance: The distance for the robot to travel (In Centimeters)
        : type distance: float
        : param speed: The speed for which the robot to travel (Bounded from -1 to 1). Default is half speed forward
        : type speed: float
        : param timeout: The amount of time before the robot stops trying to move forward and continues to the next step (In Seconds)
        : type timeout: float
        : param main_controller: The main controller, for handling the distance driven forwards
        : type main_controller: Controller
        : param secondary_controller: The secondary controller, for correcting heading error that may result during the drive.
        : type secondary_controller: Controller
        : return: if the distance was reached before the timeout
        : rtype: bool
        """
        # ensure distance is always positive while speed could be either positive or negative
        if distance < 0:
            max_effort *= -1
            distance *= -1

        time_out = Timeout(timeout)
        startingLeft = self.get_left_encoder_position()
        startingRight = self.get_right_encoder_position()


        if main_controller is None:
            main_controller = PID(
                kp = 0.5,
                minOutput = 0.12,
                maxOutput = max_effort,
                tolerance = 0.1,
                toleranceCount = 3,
            )

        # Secondary controller to keep encoder values in sync
        if secondary_controller is None:
            secondary_controller = PID(
                kp = 0.0175, kd=0.005, 
            )

        rotationsToDo = distance  / (self.wheel_diam * math.pi)
        #print("rot:", rotationsToDo)

        if self.imu is not None:
            # record current heading to maintain it
            initial_heading = self.imu.get_yaw()
        else:
            initial_heading = 0

        while True:

            # calculate the distance traveled
            leftDelta = self.get_left_encoder_position() - startingLeft
            rightDelta = self.get_right_encoder_position() - startingRight
            rotationsDelta = (leftDelta + rightDelta) / 2

            # PID for distance
            distanceError = rotationsToDo - rotationsDelta
            effort = main_controller.tick(distanceError)
            
            if main_controller.is_done() or time_out.is_done():
                break

            # calculate heading correction
            if self.imu is not None:
                # record current heading to maintain it
                current_heading = self.imu.get_yaw()
            else:
                current_heading = ((leftDelta-rightDelta)/2)*360*self.wheel_diam/self.track_width

            headingCorrection = secondary_controller.tick(current_heading - initial_heading)

            self.set_effort(effort - headingCorrection, effort + headingCorrection)

            time.sleep(0.01)

        self.stop()

        return not time_out.is_done()


    def turn(self, turn_degrees: float, max_effort: float = 0.5, timeout: float = None, main_controller: Controller = None, secondary_controller: Controller = None, use_imu:bool = True) -> bool:
        """
        Turn the robot some relative heading given in turnDegrees, and exit function when the robot has reached that heading.
        Speed is bounded from -1 (turn counterclockwise the relative heading at full speed) to 1 (turn clockwise the relative heading at full speed)
        Uses the IMU to determine the heading of the robot and P control for the motor controller.

        : param turnDegrees: The number of angle for the robot to turn (In Degrees)
        : type turnDegrees: float
        : param speed: The speed for which the robot to travel (Bounded from -1 to 1). Default is half speed forward.
        : type speed: float
        : param timeout: The amount of time before the robot stops trying to turn and continues to the next step (In Seconds)
        : type timeout: float
        : param main_controller: The main controller, for handling the angle turned
        : type main_controller: Controller
        : param secondary_controller: The secondary controller, for maintaining position during the turn by controlling the encoder count difference
        : type secondary_controller: Controller
        : param use_imu: A boolean flag that changes if the main controller bases it's movement off of 
        : return: if the distance was reached before the timeout
        : rtype: bool
        """

        if max_effort < 0:
            max_effort *= -1
            turn_degrees *= -1

        time_out = Timeout(timeout)
        startingLeft = self.get_left_encoder_position()
        startingRight = self.get_right_encoder_position()

        if main_controller is None:
            main_controller = PID(
                kp = .015,
                kd = 0.0012,
                minOutput = 0.25,
                maxOutput = max_effort,
                tolerance = 0.5,
                toleranceCount = 3
            )

        # Secondary controller to keep encoder values in sync
        if secondary_controller is None:
            secondary_controller = PID(
                kp = 0.002,
            )
 
        if use_imu and (self.imu is not None):
            turn_degrees += self.imu.get_yaw()

        while True:
            
            # calculate encoder correction to minimize drift
            leftDelta = self.get_left_encoder_position() - startingLeft
            rightDelta = self.get_right_encoder_position() - startingRight
            encoderCorrection = secondary_controller.tick(leftDelta + rightDelta)

            if use_imu and (self.imu is not None):
                # calculate turn error (in degrees) from the imu
                turnError = turn_degrees - self.imu.get_yaw()
            else:
                # calculate turn error (in degrees) from the encoder counts
                turnError = turn_degrees - ((rightDelta-leftDelta)/2)*360*self.wheel_diam/self.track_width

            # Pass the turn error to the main controller to get a turn speed
            turnSpeed = main_controller.tick(turnError)
            
            # exit if timeout or tolerance reached
            if main_controller.is_done() or time_out.is_done():
                break

            self.set_effort(-turnSpeed - encoderCorrection, turnSpeed - encoderCorrection)

            time.sleep(0.01)

        self.stop()

        return not time_out.is_done()