from XRPLib.defaults import *
import time

def test():
    telemetry.send_data("state", "Straight")
    drivetrain.straight(20, 1)

    telemetry.send_data("state", "Turning")
    drivetrain.turn(90, 1)

    telemetry.send_data("state", "Arc")
    drivetrain.set_effort(0.8, 1)
    time.sleep(2)
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


telemetry.start_telemetry()

proportional_control()


telemetry.stop_telemetry()

# nums = [i for i in range(0, 128) if i != 4]
# buffer = bytearray(nums)

# encoded_data = buffer.decode('ascii')
# print("hi")
# print(encoded_data)
# print("world")
