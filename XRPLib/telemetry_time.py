class TelemetryTime:

    # Get the current time in milliseconds
    def time_ms(self):
        raise NotImplementedError("time_ms method must be implemented by subclass")
    
    # Get the difference between two times in milliseconds
    def time_diff(self, end_time, start_time):
        raise NotImplementedError("time_diff method must be implemented by subclass")