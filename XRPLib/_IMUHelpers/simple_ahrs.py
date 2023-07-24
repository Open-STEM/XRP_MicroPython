from .ahrs import AHRS

from .quaternion import Quaternion

class SimpleAHRS:
    """
    Performs simple integration of the input gyroscope readings
    """
    def __init__(self, sample_time:float):
        self.sample_time = sample_time
        self.pitch = 0
        self.roll = 0
        self.yaw = 0

    def update_imu(self, gyroscope: tuple, accelerometer: tuple) -> Quaternion:
        """
        Perform one update step with data from a IMU sensor array
        :param gyroscope: A three-element tuple containing the gyroscope data in radians per second.
        :type gyroscope: tuple
        :param accelerometer: A three-element tuple containing the accelerometer data. Can be any unit since a normalized value is used.
        :type accelerometer: tuple
        :return: A quaternion representing the rotation of the robot
        :rtype: Quaternion
        """
        self.pitch += gyroscope[0]*self.sample_time
        self.roll += gyroscope[1]*self.sample_time
        self.yaw += gyroscope[2]*self.sample_time
        
        # Since the AHRS abstract specifies that it returns the angle with a quaternion
        # Which is more than we really need for this, but we will follow the contract anyways
        return Quaternion.from_euler(self.pitch, self.roll, self.yaw)
        