import numbers
import math

class Quaternion:
    """
    A simple class implementing basic quaternion arithmetic.
    """
    def __init__(self, w_or_q, x=None, y=None, z=None):
        """
        Initializes a Quaternion object
        :param w_or_q: A scalar representing the real part of the quaternion, another Quaternion object, or a
                    four-element list containing the quaternion values
        :param x: The first imaginary part if w_or_q is a scalar
        :param y: The second imaginary part if w_or_q is a scalar
        :param z: The third imaginary part if w_or_q is a scalar
        """
        self._q = [1, 0, 0, 0]

        if x is not None and y is not None and z is not None:
            w = w_or_q
            q = [w, x, y, z]
        elif isinstance(w_or_q, Quaternion):
            q = list(w_or_q.q)
        else:
            q = list(w_or_q)
            if len(q) != 4:
                raise ValueError("Expecting a 4-element list or w x y z as parameters")

        self.q = q

    # Quaternion specific interfaces

    def conj(self):
        """
        Returns the conjugate of the quaternion
        :rtype : Quaternion
        :return: the conjugate of the quaternion
        """
        return Quaternion(self._q[0], -self._q[1], -self._q[2], -self._q[3])

    def to_angle_axis(self):
        """
        Returns the quaternion's rotation represented by an Euler angle and axis.
        If the quaternion is the identity quaternion (1, 0, 0, 0), a rotation along the x-axis with angle 0 is returned.
        :return: rad, x, y, z
        """
        if self[0] == 1 and self[1] == 0 and self[2] == 0 and self[3] == 0:
            return 0, 1, 0, 0
        rad = math.acos(self[0]) * 2
        imaginary_factor = math.sin(rad / 2)
        if abs(imaginary_factor) < 1e-8:
            return 0, 1, 0, 0
        x = self._q[1] / imaginary_factor
        y = self._q[2] / imaginary_factor
        z = self._q[3] / imaginary_factor
        return rad, x, y, z

    @staticmethod
    def from_angle_axis(rad, x, y, z):
        s = math.sin(rad / 2)
        return Quaternion(math.cos(rad / 2), x*s, y*s, z*s)

    def to_euler_angles(self):
        pitch = math.asin(2 * self[1] * self[2] + 2 * self[0] * self[3])
        if abs(self[1] * self[2] + self[3] * self[0] - 0.5) < 1e-8:
            roll = 0
            yaw = 2 * math.atan2(self[1], self[0])
        elif abs(self[1] * self[2] + self[3] * self[0] + 0.5) < 1e-8:
            roll = -2 * math.atan2(self[1], self[0])
            yaw = 0
        else:
            roll = math.atan2(2 * self[0] * self[1] - 2 * self[2] * self[3], 1 - 2 * self[1] ** 2 - 2 * self[3] ** 2)
            yaw = math.atan2(2 * self[0] * self[2] - 2 * self[1] * self[3], 1 - 2 * self[2] ** 2 - 2 * self[3] ** 2)
        return roll, pitch, yaw

    def to_euler123(self):
        roll = math.atan2(-2 * (self[2] * self[3] - self[0] * self[1]), self[0] ** 2 - self[1] ** 2 - self[2] ** 2 + self[3] ** 2)
        pitch = math.asin(2 * (self[1] * self[3] + self[0] * self[1]))
        yaw = math.atan2(-2 * (self[1] * self[2] - self[0] * self[3]), self[0] ** 2 + self[1] ** 2 - self[2] ** 2 - self[3] ** 2)
        return roll, pitch, yaw

    def __mul__(self, other):
        """
        multiply the given quaternion with another quaternion or a scalar
        :param other: a Quaternion object or a number
        :return:
        """
        if isinstance(other, Quaternion):
            w = self._q[0]*other._q[0] - self._q[1]*other._q[1] - self._q[2]*other._q[2] - self._q[3]*other._q[3]
            x = self._q[0]*other._q[1] + self._q[1]*other._q[0] + self._q[2]*other._q[3] - self._q[3]*other._q[2]
            y = self._q[0]*other._q[2] - self._q[1]*other._q[3] + self._q[2]*other._q[0] + self._q[3]*other._q[1]
            z = self._q[0]*other._q[3] + self._q[1]*other._q[2] - self._q[2]*other._q[1] + self._q[3]*other._q[0]

            return Quaternion(w, x, y, z)
        elif isinstance(other, numbers.Number):
            q = [x * other for x in self._q]
            return Quaternion(q)

    def __add__(self, other):
        """
        add two quaternions element-wise or add a scalar to each element of the quaternion
        :param other:
        :return:
        """
        if not isinstance(other, Quaternion):
            if len(other) != 4:
                raise TypeError("Quaternions must be added to other quaternions or a 4-element list")
            q = [self._q[i] + other[i] for i in range(4)]
        else:
            q = [self._q[i] + other._q[i] for i in range(4)]

        return Quaternion(q)

    # Implementing other interfaces to ease working with the class

    @property
    def q(self):
        return self._q

    @q.setter
    def q(self, q):
        self._q = q

    def __getitem__(self, item):
        return self._q[item]

    def __array__(self):
        return self._q