from encoded_motor import EncodedMotor
import time
import math

class Drivetrain:
    def __init__(self, left_motor: EncodedMotor, right_motor: EncodedMotor, wheel_diam:float = 6.5, wheel_track:float = 13.5):
        self.left_motor = left_motor
        self.right_motor = right_motor
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

        # ensure distance is always positive while speed could be either positive or negative
        if turn_degrees < 0:
            speed *= -1
            turn_degrees *= -1

        rotationsToDo = (turn_degrees/360) * self.track_width / self.wheel_diam

        startTime = time.time()
        startingLeft = self.get_left_encoder_position()
        startingRight = self.get_right_encoder_position()

        KP = 5

        while True:

            leftPosition = self.get_left_encoder_position()
            rightPosition = self.get_right_encoder_position()
            leftDelta = leftPosition - startingLeft
            rightDelta = rightPosition - startingRight

            if _isTimeout(startTime, timeout) or abs(leftDelta + rightDelta)/2 >= rotationsToDo:
                break

            error = KP * (leftDelta - rightDelta)

            self.set_effort(speed - error, speed + error)

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
