import math
from .quaternion import Quaternion
import warnings

class MadgwickAHRS:
    quaternion = Quaternion(1, 0, 0, 0)
    _beta = 1

    def __init__(self, sample_period, quaternion=None, beta=None):
        self._samplePeriod = sample_period
        if quaternion is not None:
            self.quaternion = quaternion
        if beta is not None:
            self._beta = beta

    def update_imu(self, gyroscope, accelerometer):
        q = self.quaternion

        gyroscope = list(map(float, gyroscope))
        accelerometer = list(map(float, accelerometer))

        # Normalise accelerometer measurement
        acc_norm = math.sqrt(accelerometer[0] ** 2 + accelerometer[1] ** 2 + accelerometer[2] ** 2)
        if acc_norm == 0:
            warnings.warn("accelerometer is zero")
            return
        accelerometer = [x / acc_norm for x in accelerometer]

        # Gradient descent algorithm corrective step
        f = [
            2*(q[1]*q[3] - q[0]*q[2]) - accelerometer[0],
            2*(q[0]*q[1] + q[2]*q[3]) - accelerometer[1],
            2*(0.5 - q[1]**2 - q[2]**2) - accelerometer[2]
        ]
        j = [
            [-2*q[2], 2*q[3], -2*q[0], 2*q[1]],
            [2*q[1], 2*q[0], 2*q[3], 2*q[2]],
            [0, -4*q[1], -4*q[2], 0]
        ]
        step = [sum([j[i][j] * f[j] for j in range(3)]) for i in range(3)]
        step_norm = math.sqrt(sum([s ** 2 for s in step]))
        step = [s / step_norm for s in step]

        # Compute rate of change of quaternion
        qdot = [(q[i] * gyroscope[i]) * 0.5 - self._beta * step[i] for i in range(4)]

        # Integrate to yield quaternion
        q = [q[i] + qdot[i] * self._samplePeriod for i in range(4)]
        q_norm = math.sqrt(sum([x ** 2 for x in q]))
        self.quaternion = Quaternion([x / q_norm for x in q])