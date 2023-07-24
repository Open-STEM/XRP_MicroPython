from .quaternion import Quaternion

class AHRS:
    """
    An abstract class to be entended to demonstrate different types of heading determination algorithms. A Madgwick subclass has also been provided
    """
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
        pass