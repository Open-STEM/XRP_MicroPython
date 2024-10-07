from XRPLib.defaults import *
import time


print("start")

telemetry.start_telemetry()

drivetrain.straight(10, 0.7)


telemetry.stop_telemetry()
print("done")

# nums = [i for i in range(0, 128) if i != 4]
# buffer = bytearray(nums)

# encoded_data = buffer.decode('ascii')
# print("hi")
# print(encoded_data)
# print("world")
