from .encoded_motor import EncodedMotor
from .imu import IMU
import time
import math

class Drivetrain:

    _DEFAULT_DRIVETRAIN_INSTANCE =None

    @classmethod
    def get_default_drivetrain(cls):

        """
        Get the default XRP v2 drivetrain instance. This is a singleton, so only one instance of the drivetrain will ever exist.
        """

        if cls._DEFAULT_DRIVETRAIN_INSTANCE is None:
            cls._DEFAULT_DRIVETRAIN_INSTANCE = cls(
            EncodedMotor.get_default_left_motor(),
            EncodedMotor.get_default_right_motor(),
            IMU.get_default_imu()
        )
            
        return cls._DEFAULT_DRIVETRAIN_INSTANCE

    def __init__(self, left_motor: EncodedMotor, right_motor: EncodedMotor, imu: IMU | None = None, wheel_diam:float = 6.5, wheel_track:float = 13.5):
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


    def straight(self, distance: float, speed: float = 0.5, timeout: float = None) -> bool:
        """
        Go forward the specified distance in centimeters, and exit function when distance has been reached.
        Speed is bounded from -1 (reverse at full speed) to 1 (forward at full speed)

        : param distance: The distance for the robot to travel (In Centimeters)
        : type distance: float
        : param speed: The speed for which the robot to travel (Bounded from -1 to 1). Default is half speed forward
        : type speed: float
        : param timeout: The amount of time before the robot stops trying to move forward and continues to the next step (In Seconds)
        : type timeout: float
        : return: if the distance was reached before the timeout
        : rtype: bool
        """
        # ensure distance is always positive while speed could be either positive or negative
        if distance < 0:
            speed *= -1
            distance *= -1

        startTime = time.time()
        startingLeft = self.get_left_encoder_position()
        startingRight = self.get_right_encoder_position()

        KP = 5

        rotationsToDo = distance  / (self.wheel_diam * math.pi)

        while True:

            leftPosition = self.get_left_encoder_position()
            rightPosition = self.get_right_encoder_position()
            leftDelta = leftPosition - startingLeft
            rightDelta = rightPosition - startingRight

            if _isTimeout(startTime, timeout) or abs(leftDelta + rightDelta)/2 >= rotationsToDo:
                break

            error = KP * (leftDelta - rightDelta) # positive if bearing right

            self.set_effort(speed - error, speed + error)

            time.sleep(0.01)

        self.stop()

        if timeout is None:
            return True
        else:
            return time.time() < startTime+timeout


    def turn(self, turn_degrees: float, speed: float = 0.5, timeout: float = None) -> bool:
        """
        Turn the robot some relative heading given in turnDegrees, and exit function when the robot has reached that heading.
        Speed is bounded from -1 (turn counterclockwise the relative heading at full speed) to 1 (turn clockwise the relative heading at full speed)

        : param turnDegrees: The number of angle for the robot to turn (In Degrees)
        : type turnDegrees: float
        : param speed: The speed for which the robot to travel (Bounded from -1 to 1). Default is half speed forward.
        : type speed: float
        : param timeout: The amount of time before the robot stops trying to turn and continues to the next step (In Seconds)
        : type timeout: float
        : return: if the distance was reached before the timeout
        : rtype: bool
        """

        if speed < 0:
            speed *= -1
            turn_degrees *= -1

        #rotationsToDo = (turn_degrees/360) * self.track_width / self.wheel_diam

        startTime = time.time()
        #startingLeft = self.get_left_encoder_position()
        #startingRight = self.get_right_encoder_position()

        KP = 0.02
        TOLERANCE_DEGREES = 0.5
        NUM_TIMES_IN_TOLERANCE = 3
        MIN_EFFORT_MAGNITUDE = 0.15
        times = 0

        print("start turn")

        self.imu.reset_yaw() 
        while True:

            currentHeading = self.imu.get_yaw()
            deltaHeading = turn_degrees - currentHeading

            print(deltaHeading)

            # heading must fall within tolerance for NUM_TIMES_IN_TOLERANCE consecutive times to exit
            if abs(deltaHeading) < TOLERANCE_DEGREES:
                times += 1
            else:
                times = 0
            
            if _isTimeout(startTime, timeout) or times >= NUM_TIMES_IN_TOLERANCE:
                break

            error = KP * deltaHeading

            # clamp error by (-speed, speed)
            if error > speed:
                error = speed
            elif error < -speed:
                error = -speed

            # if error is too small, set effort to minimum
            if abs(error) < MIN_EFFORT_MAGNITUDE:
                error = MIN_EFFORT_MAGNITUDE * (1 if error > 0 else -1)

            self.set_effort(-error, error)

            time.sleep(0.01)

        self.stop()

        if timeout is None:
            return True
        else:
            return time.time() < startTime+timeout

# A helper function for our straight and turn functions
# Returns true if the timeout has been reached
def _isTimeout(startTime, timeout):

    if timeout is None:
        return False
    return time.time() >= startTime+timeout
