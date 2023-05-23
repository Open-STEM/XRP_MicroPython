from XRPLib.drivetrain import Drivetrain
from XRPLib.motor import Motor
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
print("calibrating")
time.sleep(0.1)
xrp.imu.calibrate()
time.sleep(0.5)
print("calibrated")

class RollingAverage:
    def __init__(self, N):
        self.N = N
        self.values = []

    def add(self, value):
        self.values.append(value)
        if len(self.values) > self.N:  # If more than N, remove the first value
            self.values.pop(0)

    def average(self):
        if len(self.values) == 0:  # If no values, return 0
            return 0
        return sum(self.values) / len(self.values)

# print out x, y, z, accelerometer readings
def log_accelerometer():
    while True:
        accReadings = xrp.imu._get_acc_rates()
        print(f"{accReadings[2]:.2f}, {xrp.imu._get_gyro_z_rate():.2f}")
        time.sleep(0.1)

def pitch():
    accReadings = xrp.imu._get_acc_rates()
    return math.atan2(accReadings[1],accReadings[2])*180/math.pi

def log_imu():

    r = RollingAverage(10)

    i = 0
    while True:

        pitch = xrp.imu.adjusted_pitch
        r.add(pitch)

        i = (i + 1) % 10
        if i == 0:
            print(f"{r.average():.2f} {xrp.imu.running_yaw:.2f}")

        time.sleep(0.01)

def clamp(x, min, max):
    if x < min:
        return min
    elif x > max:
        return max
    else:
        return x

# value is a lambda. threshold is a constant value
# wait until value is [GREATER/LESS] than threshold
# numTimes is the number of consecutive times the condition must be met before exiting
GREATER_THAN = 1
LESS_THAN = -1

def compare(a, b, comparator):
        if comparator == GREATER_THAN:
            return a > b
        elif comparator == LESS_THAN:
            return a < b
        else:
            return False
        

def straight_until_pitch(effort, targetHeading, comparator, threshold):
    
    KP = 0.005
    average = RollingAverage(10)
    
    while True:

        average.add(xrp.imu.adjusted_pitch)
        pitch = average.average()

        if compare(pitch, threshold, comparator):
            break

        currentHeading = xrp.imu.running_yaw
        error = KP * (targetHeading - currentHeading)

        left = clamp(effort - error, -1, 1)
        right = clamp(effort + error, -1, 1)

        xrp.drivetrain.set_effort(left, right)

        time.sleep(0.01)

def ramp_demo():

    SPEED = 0.6

    Z_PARALLEL = 2 #1000 # z acceleration when parallel to ground
    Z_CLIMBING = 15 #970 # z acceleration when climbing ramp

    # go forward while maintaining heading
    targetHeading = 0

    direction = 1 # 1 for forward, -1 for backward

    time.sleep(2)

    # start flat on the ground aimed at ramp
    while True:

        print("ramp begin")

        effort = SPEED * direction
        
        # wait until going up ramp
        straight_until_pitch(effort, targetHeading, GREATER_THAN * direction, Z_CLIMBING)

        print("ramp climb")

        # wait until on ramp
        straight_until_pitch(effort, targetHeading, LESS_THAN * direction, Z_PARALLEL)
        print("ramp top")
        
        # go forward a little longer to get to center of ramp
        time.sleep(0.2)

        # stop on center of ramp and stay there for a few seconds
        xrp.drivetrain.stop()
        print("ramp stop")
        time.sleep(2)

        # get off ramp
        straight_until_pitch(effort, targetHeading, GREATER_THAN * direction, Z_CLIMBING)

        print("ramp descend")

        # get back to flat ground
        straight_until_pitch(effort, targetHeading, LESS_THAN * direction, Z_PARALLEL)
        time.sleep(0.5) # wait a little longer to get some distance between robot and ramp

        # stop for a few seconds
        xrp.drivetrain.stop()
        print("ramp stop")
        time.sleep(2)

        # switch direction
        direction *= -1


