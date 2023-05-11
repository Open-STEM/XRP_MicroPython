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
print("calibrating")
time.sleep(0.1)
xrp.imu.calibrate()
time.sleep(0.5)
print("calibrated")

# print out x, y, z, accelerometer readings
def log_accelerometer():
    while True:
        accReadings = xrp.imu.get_acc()
        print(accReadings)
        time.sleep(0.1)

def pitch():
    accReadings = xrp.imu.get_acc()
    return math.atan2(accReadings[1],accReadings[2])*180/math.pi

def log_imu():


    while True:
        print(f"{xrp.imu.adjusted_pitch:.2f} {xrp.imu.running_heading:.2f} {xrp.imu.gyro_pitch_bias:.2f}  {xrp.imu.gyro_pitch_running_total/1000:.2f}  {pitch():.2f}" )
        time.sleep(0.1)

# value is a lambda. threshold is a constant value
# wait until value is [GREATER/LESS] than threshold
# numTimes is the number of consecutive times the condition must be met before exiting
GREATER_THAN = 1
LESS_THAN = 2
def wait_until(value, comparator, threshold, numTimes = 1, code = lambda: None):
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

        code()

        print(v)
        time.sleep(0.01)

def go_forward():
    print("start go forward")
    xrp.drivetrain.set_effort(0.5, 0.5)
    time.sleep(2)
    xrp.drivetrain.stop()
    print("end go forward")

def clamp(x, min, max):
    if x < min:
        return min
    elif x > max:
        return max
    else:
        return x

# nonblocking function to set speed given effort and heading in degrees 
def setSpeed(effort, targetHeading):
    KP = 0.1

    currentHeading = xrp.imu.running_heading
    error = KP * (targetHeading - currentHeading)
    
    left = clamp(effort - error, -1, 1)
    right = clamp(effort + error, -1, 1)

    xrp.drivetrain.set_effort(left, right)

def ramp_demo():

    SPEED = 0.65

    Z_PARALLEL = 1000 # z acceleration when parallel to ground
    Z_CLIMBING = 970 # z acceleration when climbing ramp

    # get z acceleration
    z = lambda: xrp.imu.get_acc()[2] 

    # go forward while maintaining heading
    targetHeading = xrp.imu.running_heading

    direction = 1 # 1 for forward, -1 for backward

    time.sleep(2)

    # start flat on the ground aimed at ramp
    while True:

        print("ramp begin")

        speed = SPEED * direction
        code = lambda: setSpeed(speed, targetHeading)
        
        # wait until going up ramp
        wait_until(z, LESS_THAN, Z_CLIMBING, 5, code)

        print("ramp climb")

        # wait until on ramp
        wait_until(z, GREATER_THAN, Z_PARALLEL, 5, code)
        print("ramp top")
        
        # go forward a little longer to get to center of ramp
        time.sleep(0.2)

        # stop on center of ramp and stay there for a few seconds
        xrp.drivetrain.stop()
        print("ramp stop")
        time.sleep(2)

        # get off ramp
        wait_until(z, LESS_THAN, Z_CLIMBING, 5, code)

        print("ramp descend")

        # get back to flat ground
        wait_until(z, GREATER_THAN, Z_PARALLEL, 5, code)
        time.sleep(0.5) # wait a little longer to get some distance between robot and ramp

        # stop for a few seconds
        xrp.drivetrain.stop()
        print("ramp stop")
        time.sleep(2)

        # switch direction
        direction *= -1


