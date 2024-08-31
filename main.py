from XRPLib.defaults import *
import time

telemetry.start_telemetry()
for i in range(10):
    time.sleep(0.5)
    telemetry.send_data("custom", 12345)
telemetry.stop_telemetry()