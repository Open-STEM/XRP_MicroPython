from XRPLib.defaults import *
import time

"""
    By the end of this file students will learn how to read and use data from
    both the ultrasonic sensors and the line followers.
    They will also have a chance to learn the basics of proportional control.
"""

# Polling data from the ultrasonic sensor
def ultrasonic_test():
    while True:
        print(rangefinder.distance())
        time.sleep(0.1)

# Approaches a wall at a set speed and then stops
def drive_till_close(target_distance: float = 10.0):
    speed = 0.6
    while rangefinder.distance() > target_distance:
        drivetrain.set_effort(speed, speed)
        time.sleep(0.01)
    drivetrain.set_effort(0, 0)

# Maintains a certain distance from the wall using proportional control
def standoff(target_distance: float = 10.0):
    KP = 0.2
    while True:
        distance = rangefinder.distance()
        error = distance - target_distance
        drivetrain.set_effort(error * KP, error*KP)
        time.sleep(0.01)

# Maintains a certain distance from the wall while driving
#     using proportional control (sensor on right side of robot this time)
def wall_follow(target_distance: float = 10.0):
    KP = 0.1
    base_speed = 0.5
    while True:
        distance = rangefinder.distance()
        error = distance - target_distance
        print(error)
        drivetrain.set_effort(base_speed + error * KP, base_speed - error*KP)
        time.sleep(0.01)

# Follows a line using the line followers
def line_track():
    base_effort = 0.6
    KP = 0.6
    while True:
        # You always want to take the difference of the sensors because the raw value isn't always consistent.
        error = reflectance.get_left() - reflectance.get_right()
        print(error)
        drivetrain.set_effort(base_effort - error * KP, base_effort + error * KP)
        time.sleep(0.01)

# Polling data from the IMU
def imu_test():
    while True:
        print(f"Pitch: {imu.get_pitch()}, Heading: {imu.get_heading()}, Roll: {imu.get_yaw()}, Accelerometer output: {imu.get_acc_rates()}")
        time.sleep(0.1)

def climb_ramp(ramp_angle, angle_tolerance=3.5):
    speed = 0.6
    # Find ramp by driving forward
    while imu.get_pitch() < ramp_angle-angle_tolerance:
        drivetrain.set_effort(speed, speed)
        time.sleep(0.05)
    # Drive up ramp until angle levels out again
    while imu.get_pitch() >= ramp_angle-angle_tolerance:
        drivetrain.set_effort(speed, speed)
        time.sleep(0.05)
    # Then stop
    drivetrain.set_effort(0, 0)

ultrasonic_test()