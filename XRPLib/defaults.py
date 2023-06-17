from .board import Board
from .button import Button
from .drivetrain import Drivetrain
from .motor import Motor
from .encoder import Encoder
from .encoded_motor import EncodedMotor
from .rangefinder import Rangefinder
from .imu import IMU
from .led import LED
from .reflectance import Reflectance
from .servo import Servo
from .webserver import Webserver

left_motor = EncodedMotor.get_default_left_motor()
right_motor = EncodedMotor.get_default_right_motor()
imu = IMU.get_default_imu()
drivetrain = Drivetrain.get_default_drivetrain()
rangefinder = Rangefinder.get_default_rangefinder()
reflectance = Reflectance.get_default_reflectance()
led = LED.get_default_led()
servo_one = Servo.get_default_servo()
button = Button.get_default_button()
webserver = Webserver.get_default_webserver()
board = Board.get_default_board()