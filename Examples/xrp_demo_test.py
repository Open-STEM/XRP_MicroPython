from ..XRPLib.drivetrain import Drivetrain
from ..XRPLib.motor import Motor
from ..XRPLib.encoder import Encoder
from ..XRPLib.encoded_motor import EncodedMotor
from ..XRPLib.hcsr04 import HCSR04
from ..XRPLib.imu import IMU
from ..XRPLib.led import LED
from ..XRPLib.reflectance import Reflectance
from ..XRPLib.servo import Servo
import math
import time

class XRPBot:
    def __init__(self):
        # Default Robot Configuration
        self.left_motor = EncodedMotor(Motor(6,7, flip_dir=True),4,5)
        self.right_motor = EncodedMotor(Motor(14,15),12,13)
        self.drivetrain = Drivetrain(self.left_motor, self.right_motor)
        self.servo = Servo(16)
        self.imu = IMU()
        self.reflectance = Reflectance(26,27)
        self.sonar = HCSR04(22,28)
        self.led = LED()

xrp = XRPBot()
xrp.imu.calibrate()

def pitch():
    accReadings = xrp.imu.get_acc()
    return math.atan2(accReadings[1],accReadings[2])*180/math.pi

def logAccelerometer():
    while True:
        accReadings = xrp.imu.get_acc()
        print(accReadings)
        time.sleep(0.1)

def balance(seconds = -1):
    start_time = time.time()
    while (seconds == -1) or (time.time() < start_time + seconds):
        kp = 1/40 # set so that robot will go max speed at 40 degrees
        effort = kp * pitch()
        xrp.drivetrain.set_effort(effort, effort)
        time.sleep(0.05)
    xrp.drivetrain.stop()

def drive_until_change(effort:float, boundary: float, comparator: int, tolerance:float = 0):
    # 0 - within tolerance of the boundary
    # 1 - less than boundary
    # 2 - more than boundary
    if comparator == 0:
        compare_function = lambda pitch: abs(pitch - boundary) < tolerance
    elif comparator == 1:
        compare_function = lambda pitch: pitch < boundary
    else:
        compare_function = lambda pitch: pitch > boundary
    while not compare_function(pitch()):
        xrp.drivetrain.set_effort(effort, effort)
        time.sleep(0.05)
    xrp.drivetrain.stop()

def ramp_demo():
    # Start by driving forwards
    direction = 1
    speed = 1

    while True:
        # Drive until we get onto ramp
        drive_until_change(direction*speed, direction*10, 2)
        # Balance on ramp
        balance(5)
        # Wait a second before continuing
        time.sleep(1)
        # Drive until ramp tips
        drive_until_change(direction*speed, direction*-10, 0,tolerance=0.5)
        # Drive until back on flat ground
        drive_until_change(direction*speed, 0, 0,tolerance=0.5)
        # Wait a second before doing it again in the other direction
        time.sleep(1)
        direction *= -1
