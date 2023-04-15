from .drivetrain import Drivetrain
from .motor import Motor
from .encoder import Encoder
from .encoded_motor import EncodedMotor
from .hcsr04 import HCSR04
from .imu import IMU
from .led import LED
from .reflectance import Reflectance
from .servo import Servo

class XRPBot:
    def __init__(self):
        # Default Robot Configuration
        self.left_motor = EncodedMotor(Motor(6,7),4,5)
        self.right_motor = EncodedMotor(Motor(14,15),12,13)
        self.drivetrain = Drivetrain(self.left_motor, self.right_motor)
        self.servo = Servo(16)
        self.imu = IMU()
        self.reflectance = Reflectance(26,27)
        self.sonar = HCSR04(22,28)
        self.led = LED()
