from .encoded_motor import EncodedMotor
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