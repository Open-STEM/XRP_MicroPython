from XRPLib.defaults import *
import time


print("start")

telemetry.start_telemetry()

def log_encoder():
    telemetry.send_data("left", left_motor.get_position())
    telemetry.send_data("right", right_motor.get_position())
    telemetry.send_data("left_raw", left_motor.get_position(raw=True))
    telemetry.send_data("right_raw", right_motor.get_position(raw=True))

drivetrain.straight(10, 0.7)
log_encoder()
drivetrain.straight(10, 0.7)
log_encoder()

drivetrain.reset_encoder_position()
log_encoder()

drivetrain.straight(10, 0.7)
log_encoder()
drivetrain.straight(10, 0.7)
log_encoder()


telemetry.stop_telemetry()
print("done")

# nums = [i for i in range(0, 128) if i != 4]
# buffer = bytearray(nums)

# encoded_data = buffer.decode('ascii')
# print("hi")
# print(encoded_data)
# print("world")
