from XRPLib.board import Board
from XRPLib.differential_drive import DifferentialDrive
from XRPLib.motor import Motor
from XRPLib.encoder import Encoder
from XRPLib.encoded_motor import EncodedMotor
from XRPLib.rangefinder import Rangefinder
from XRPLib.imu import IMU
from XRPLib.reflectance import Reflectance
from XRPLib.servo import Servo
from XRPLib.webserver import Webserver

"""
A simple file that constructs all of the default objects for the XRP robot
Run "from XRPLib.defaults import *" to use
"""

left_motor = EncodedMotor.get_default_encoded_motor(index=1)
right_motor = EncodedMotor.get_default_encoded_motor(index=2)
imu = IMU.get_default_imu()
drivetrain = DifferentialDrive.get_default_differential_drive()
rangefinder = Rangefinder.get_default_rangefinder()
reflectance = Reflectance.get_default_reflectance()
servo_one = Servo.get_default_servo(index=1)
servo_two = Servo.get_default_servo(index=2)
webserver = Webserver.get_default_webserver()
board = Board.get_default_board()