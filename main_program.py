from XRPLib.defaults import *
import time

telemetry.start_telemetry()

# Every second, for 10 seconds, print the index of the loop
for i in range(10):
    print(i)
    time.sleep(1)
    telemetry.send_data("loop", i)

telemetry.stop_telemetry()