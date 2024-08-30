from machine import Timer
import time

class Telemetry:

    _DEFAULT_TELEMETRY_INSTANCE = None

    @classmethod
    def get_default_telemetry(cls):
        """
        Get the default telemetry instance. This is a singleton, so only one instance of the board will ever exist.
        """
        if cls._DEFAULT_TELEMETRY_INSTANCE is None:
            cls._DEFAULT_TELEMETRY_INSTANCE = cls()
        return cls._DEFAULT_TELEMETRY_INSTANCE

    def __init__(self):
        self.telemetry_timer = Timer(-1)
        self.start_time = time.ticks_ms()

    def start_telemetry(self):
        print("Starting telemetry")
        self.telemetry_timer.init(freq=1, callback= lambda t: self.send_telemetry())

    def send_telemetry(self):
        current_time = time.ticks_ms()
        print("Telemetry", current_time - self.start_time)

    def stop_telemetry(self):
        print("Stopping telemetry")
        self.telemetry_timer.deinit()