from .encoded_motor import EncodedMotor
from .controller import Controller
from .pid import PID
from .timeout import Timeout
import time

class MotorGroup(EncodedMotor):
    def __init__(self, *motors: EncodedMotor):
        """
        A wrapper class for multiple motors, allowing them to be treated as one motor.
        
        :param motors: The motors to add to this group
        :type motors: tuple<EncodedMotor>
        """
        self.motors = []
        for motor in motors:
            self.add_motor(motor)

    def add_motor(self, motor:EncodedMotor):
        """
        :param motor: The motor to add to this group
        :type motor: EncodedMotor
        """
        self.motors.append(motor)

    def remove_motor(self, motor:EncodedMotor):
        """
        :param motor: The motor to remove from this group
        :type motor: EncodedMotor
        """
        try:
            self.motors.remove(motor)
        except:
            print("Failed to remove motor from Motor Group")

    def set_effort(self, effort: float):
        """
        :param effort: The effort to set all motors in this group to, from -1 to 1
        :type effort: float
        """
        for motor in self.motors:
            motor.set_effort(effort)
        
    def get_position(self) -> float:
        """
        :return: The average position of all motors in this group, in revolutions, relative to the last time reset was called.
        :rtype: float
        """
        avg = 0
        for motor in self.motors:
            avg += motor.get_position()
        return avg / len(self.motors)

    def get_position_counts(self) -> int:
        """
        :return: The average position of all motors in this group, in encoder counts, relative to the last time reset was called.
        :rtype: int
        """
        avg = 0
        for motor in self.motors:
            avg += motor.get_position_counts()
        return round(avg / len(self.motors))

    def reset_encoder_position(self):
        """
        Resets the encoder position of all motors in this group back to zero.
        """
        for motor in self.motors:
            motor.reset_encoder_position()

    def get_speed(self) -> float:
        """
        :return: The average speed of the motors, in rpm
        :rtype: float
        """
        avg = 0
        for motor in self.motors:
            avg += motor.get_speed()
        return avg / len(self.motors)


    def set_speed(self, target_speed_rpm: float = None):
        """
        Sets target speed (in rpm) to be maintained passively by all motors in this group
        Call with no parameters to turn off speed control

        :param target_speed_rpm: The target speed for these motors in rpm, or None
        :type target_speed_rpm: float, or None
        """
        for motor in self.motors:
            motor.set_speed(target_speed_rpm)

    def set_speed_controller(self, new_controller):
        """
        :param new_controller: The new Controller for speed control
        :type new_controller: Controller
        """
        for motor in self.motors:
            motor.set_speed_controller(new_controller)

    def rotate(self, degrees: float, max_effort: float = 0.5, timeout: float = None, main_controller: Controller = None) -> bool:
        """
        Rotate all motors in this group by some number of degrees, and exit function when distance has been traveled.
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
                kp = 58.5,
                ki = 38.025,
                kd = 16.0875,
                min_output = 0.3,
                max_output = max_effort,
                max_integral = 0.04,
                tolerance = 0.01,
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