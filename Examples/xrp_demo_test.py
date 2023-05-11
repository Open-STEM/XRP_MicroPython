from XRPLib.drivetrain import Drivetrain
from XRPLib.motor import Motor
from XRPLib.encoder import Encoder
from XRPLib.encoded_motor import EncodedMotor
from XRPLib.hcsr04 import HCSR04
from XRPLib.imu import IMU
from XRPLib.led import LED
from XRPLib.reflectance import Reflectance
from XRPLib.servo import Servo
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
time.sleep(0.1)
xrp.imu.calibrate()
time.sleep(0.5)

# print out x, y, z, accelerometer readings
def log_accelerometer():
    while True:
        accReadings = xrp.imu.get_acc()
        print(accReadings)
        time.sleep(0.1)

# value is a lambda. threshold is a constant value
# wait until value is [GREATER/LESS] than threshold
# numTimes is the number of consecutive times the condition must be met before exiting
GREATER_THAN = 1
LESS_THAN = 2
def wait_until(value, comparator, threshold, numTimes = 1):
    def compare(a, b, comparator):
        if comparator == GREATER_THAN:
            return a > b
        elif comparator == LESS_THAN:
            return a < b
        else:
            return False
    
    times = 0
    while True:
        v = value()
        if compare(v, threshold, comparator):
            times += 1
            if times >= numTimes:
                break
        else:
            times = 0
        print(v)
        time.sleep(0.01)

def go_forward():
    print("start go forward")
    xrp.drivetrain.set_effort(0.5, 0.5)
    time.sleep(2)
    xrp.drivetrain.stop()
    print("end go forward")

def ramp_demo():

    SPEED = 0.65

    Z_PARALLEL = 1000 # z acceleration when parallel to ground
    Z_CLIMBING = 970 # z acceleration when climbing ramp

    z = lambda: xrp.imu.get_acc()[2] # get z acceleration

    direction = 1 # 1 for forward, -1 for backward

    time.sleep(2)

    # start flat on the ground aimed at ramp
    while True:

        print("ramp begin")

        speed = SPEED * direction

        xrp.drivetrain.set_effort(speed, speed)
        
        # wait until going up ramp
        wait_until(z, LESS_THAN, Z_CLIMBING, 5)

        print("ramp climb")

        # wait until on ramp
        wait_until(z, GREATER_THAN, Z_PARALLEL, 5)
        print("ramp top")
        
        # go forward a little longer to get to center of ramp
        time.sleep(0.2)

        # stop on center of ramp and stay there for a few seconds
        xrp.drivetrain.stop()
        print("ramp stop")
        time.sleep(2)

        # get off ramp
        xrp.drivetrain.set_effort(speed, speed)
        wait_until(z, LESS_THAN, Z_CLIMBING, 5)

        print("ramp descend")

        # get back to flat ground
        wait_until(z, GREATER_THAN, Z_PARALLEL, 5)
        time.sleep(0.5) # wait a little longer to get some distance between robot and ramp

        # stop for a few seconds
        xrp.drivetrain.stop()
        print("ramp stop")
        time.sleep(2)

        # switch direction
        direction *= -1


