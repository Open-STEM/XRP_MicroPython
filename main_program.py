from XRPLib.defaults import *
import time, math

def square():
    
    for i in range(4):
        drivetrain.straight(15, 0.5)
        drivetrain.turn(90, 0.5)

def print_reflectance():
    while True:
        left = reflectance.get_left()
        right = reflectance.get_right()

        print("Left: ", left)
        print("Right: ", right)

        time.sleep(0.1)

def approach_wall():

    # approach wall until the error is less than 1cm

    KP = 0.05
    DISTANCE = 10

    while math.fabs(rangefinder.distance() - DISTANCE) > 1:

        error = rangefinder.distance() - DISTANCE
        
        # Bound between -0.5 and 0.5
        effort = max(min(KP * error, 0.5), -0.5)

        # min effort is 0.2
        if effort < 0.2 and effort > 0:
            effort = 0.2
        elif effort > -0.2 and effort < 0:
            effort = -0.2

        drivetrain.set_effort(effort, effort)

        telemetry.send_data("error", error)
        telemetry.send_data("effort", effort)

        time.sleep(0.02)

    
    drivetrain.stop()


def line_follow():

    KP = 0.6
    BASE_EFFORT = 0.4
    DISTANCE = 10


    while (rangefinder.distance() > DISTANCE):


        left = reflectance.get_left()
        right = reflectance.get_right()

        error = left - right
        effort = KP * error

        left_effort = BASE_EFFORT - effort
        right_effort = BASE_EFFORT + effort

        drivetrain.set_effort(left_effort, right_effort)

        telemetry.send_data("left", left)
        telemetry.send_data("right", right)
        telemetry.send_data("error", error)
        telemetry.send_data("effort", effort)

        time.sleep(0.02)

    drivetrain.stop()

def proportional_control():

    TARGET_HEADING = 90
    KP = 0.05
    BASE_EFFORT = 0.5

    DISTANCE = 50

    initial_yaw = imu.get_yaw()

    drivetrain.reset_encoder_position()
    while (drivetrain.get_left_encoder_position() + drivetrain.get_right_encoder_position()) / 2 < DISTANCE:

        yaw = imu.get_yaw() - initial_yaw

        error = TARGET_HEADING - yaw
        effort = KP * error

        left_effort = BASE_EFFORT - effort
        right_effort = BASE_EFFORT + effort

        drivetrain.set_effort(left_effort, right_effort)

        telemetry.send_data("yaw", yaw)
        telemetry.send_data("error", error)
        telemetry.send_data("effort", effort)

        time.sleep(0.02)

    drivetrain.stop()


#print_reflectance()
telemetry.start_telemetry()

approach_wall()

telemetry.stop_telemetry()

# nums = [i for i in range(0, 128) if i != 4]
# buffer = bytearray(nums)

# encoded_data = buffer.decode('ascii')
# print("hi")
# print(encoded_data)
# print("world")
