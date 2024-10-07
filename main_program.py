from XRPLib.defaults import *
import time


print("start")

telemetry.start_telemetry()
telemetry.send_data("test", 1)
telemetry.send_data("test2", 2)
telemetry.send_data("test3", 3)
telemetry.send_data("test4", 4)
telemetry.send_data("test5", 5)
time.sleep(2)

telemetry.stop_telemetry()
print("done")

# nums = [i for i in range(0, 128) if i != 4]
# buffer = bytearray(nums)

# encoded_data = buffer.decode('ascii')
# print("hi")
# print(encoded_data)
# print("world")
