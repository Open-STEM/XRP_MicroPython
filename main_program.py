#from XRPLib.defaults import *
from XRPLib.telemetry import Telemetry
import time


print("start")

telemetry = Telemetry.get_default_telemetry()
telemetry.start_telemetry()

# Every second, for 10 seconds, print the index of the loop
for i in range(3):
    telemetry.send_data("test", i)
    time.sleep(0.5)

telemetry.stop_telemetry()
print("done")

# nums = [i for i in range(0, 128) if i != 4]
# buffer = bytearray(nums)

# encoded_data = buffer.decode('ascii')
# print("hi")
# print(encoded_data)
# print("world")
