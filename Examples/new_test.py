from XRPLib.drivetrain import Drivetrain
from XRPLib.encoded_motor import EncodedMotor
from XRPLib.hcsr04 import HCSR04
from XRPLib.imu import IMU
from XRPLib.led import LED
from XRPLib.reflectance import Reflectance
from XRPLib.servo import Servo
import math
import time

drivetrain = Drivetrain.get_default_drivetrain()
left_motor = EncodedMotor.get_default_left_motor()
right_motor = EncodedMotor.get_default_right_motor()
imu = IMU.get_default_imu()