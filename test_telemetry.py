from XRPLib.telemetry_sender import EncodedTelemetrySender
from XRPLib.telemetry_time import TelemetryTime
from websocket_manager import WebsocketManager
import time

class ComputerTime(TelemetryTime):
    def time_ms(self):
        return round(time.time() * 1000)
    
    def time_diff(self, end_time, start_time):
        return end_time - start_time

ws_manager = WebsocketManager()
sender = EncodedTelemetrySender(ComputerTime(), send_function=ws_manager.send_data)
time.sleep(1)

sender.on_start_telemetry()

sender.send_telemetry("test", 1)
sender.send_telemetry("test2", 2)
time.sleep(2)
sender.send_telemetry("test", 2)
sender.send_telemetry("test", 3)
sender.send_telemetry("hello", 2)
sender.send_telemetry("asfdjfk", 3)
sender.send_telemetry("test2", 4)

sender.on_stop_telemetry()

time.sleep(10)