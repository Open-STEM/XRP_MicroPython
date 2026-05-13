from .board import Board
from .differential_drive import DifferentialDrive
from .motor import SinglePWMMotor, DualPWMMotor
from .encoder import Encoder
from .encoded_motor import EncodedMotor
from .rangefinder import Rangefinder
from .imu import IMU
from .reflectance import Reflectance
from .servo import Servo
from .webserver import Webserver
from .buzzer import Buzzer
from machine import Pin
from sys import implementation

"""
A simple file that constructs all of the default objects for the XRP robot
Run "from XRPLib.defaults import *" to use
"""

left_motor = EncodedMotor.get_default_encoded_motor(index=1)
right_motor = EncodedMotor.get_default_encoded_motor(index=2)
motor_three = EncodedMotor.get_default_encoded_motor(index=3)
if hasattr(Pin.board, "MOTOR_4_IN_1"):
    motor_four = EncodedMotor.get_default_encoded_motor(index=4)

imu = IMU.get_default_imu()

if "NanoXRP" in implementation._machine:
    drivetrain = DifferentialDrive(left_motor, right_motor, imu, wheel_diam=3.46, wheel_track=7.8)
else:
    drivetrain = DifferentialDrive.get_default_differential_drive()

rangefinder = Rangefinder.get_default_rangefinder()
reflectance = Reflectance.get_default_reflectance()
servo_one = Servo.get_default_servo(index=1)
servo_two = Servo.get_default_servo(index=2)
webserver = Webserver.get_default_webserver()
board = Board.get_default_board()

if hasattr(Pin.board, "SERVO_3"):
    servo_three = Servo.get_default_servo(index=3)
if hasattr(Pin.board, "SERVO_4"):
    servo_four = Servo.get_default_servo(index=4)

if hasattr(Pin.board, "BOARD_BUZZER"):
    buzzer = Buzzer.get_default_buzzer()
