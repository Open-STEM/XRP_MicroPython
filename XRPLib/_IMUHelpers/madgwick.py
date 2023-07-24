from ulab import numpy as np
from .quaternion import Quaternion
from .ahrs import AHRS

class MadgwickAHRS(AHRS):
    quaternion = Quaternion(1, 0, 0, 0)
    beta = 1

    def __init__(self, sample_period, quaternion=None, beta=None):
        """
        Initialize the class with the given parameters.
        :param sampleperiod: The sample period
        :param quaternion: Initial quaternion
        :param beta: Algorithm gain beta
        :return:
        """
        self.sample_period = sample_period
        if quaternion is not None:
            self.quaternion = quaternion
        if beta is not None:
            self.beta = beta

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
        q = self.quaternion
        
        gyroscope = np.array(gyroscope, dtype=np.float).flatten()
        accelerometer = np.array(accelerometer, dtype=np.float).flatten()

        # Normalise accelerometer measurement
        if np.linalg.norm(accelerometer) is 0:
            print("Warning: Accelerometer is zero")
            return
        accelerometer /= np.linalg.norm(accelerometer)

        # Gradient descent algorithm corrective step
        f = np.array([
            2*(q[1]*q[3] - q[0]*q[2]) - accelerometer[0],
            2*(q[0]*q[1] + q[2]*q[3]) - accelerometer[1],
            2*(0.5 - q[1]**2 - q[2]**2) - accelerometer[2]
        ])
        j = np.array([
            [-2*q[2], 2*q[3], -2*q[0], 2*q[1]],
            [2*q[1], 2*q[0], 2*q[3], 2*q[2]],
            [0, -4*q[1], -4*q[2], 0]
        ])
        step = np.dot(j.transpose(),f)
        step /= np.linalg.norm(step)  # normalise step magnitude

        # Compute rate of change of quaternion
        qdot = (q * Quaternion(0, gyroscope[0], gyroscope[1], gyroscope[2])) * 0.5 + (-1 * self.beta) * step.transpose()

        # Integrate to yield quaternion
        q += qdot * self.sample_period
        self.quaternion = q

        return self.quaternion