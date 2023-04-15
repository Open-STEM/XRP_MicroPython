from drivetrain import Drivetrain
from motor import Motor
from encoder import Encoder
from encoded_motor import EncodedMotor
from hcsr04 import HCSR04
from imu import IMU
from led import LED
from reflectance import Reflectance
from servo import Servo
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

def balance():
    start_time = time.time()
    while time.time() < start_time+20:
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

    while True:
        # Drive until we get onto ramp
        drive_until_change(direction*0.5, direction*10, 2)
        # Balance on ramp
        balance()
        # Wait a second before continuing
        time.sleep(1)
        # Drive until ramp tips
        drive_until_change(direction*0.5, direction*-10, 0,tolerance=0.5)
        # Drive until back on flat ground
        drive_until_change(direction*0.5, 0, 0,tolerance=0.5)
        # Wait a second before doing it again in the other direction
        time.sleep(1)
        direction *= -1

