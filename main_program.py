from XRPLib.defaults import *
import time


print("start")

telemetry.start_telemetry()


telemetry.send_data("state", "Straight")
drivetrain.straight(20, 1)

telemetry.send_data("state", "Turning")
drivetrain.turn(90, 1)

telemetry.send_data("state", "Arc")
drivetrain.set_effort(0.8, 1)
time.sleep(2)
drivetrain.stop()

telemetry.stop_telemetry()
print("done")

# nums = [i for i in range(0, 128) if i != 4]
# buffer = bytearray(nums)

# encoded_data = buffer.decode('ascii')
# print("hi")
# print(encoded_data)
# print("world")
