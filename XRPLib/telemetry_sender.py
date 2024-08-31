import time


class TelemetrySender:
    """
    Abstract class for sending telemetry data to a telemetry receiver. Must implement the send_telemetry method.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """
        Reset telemetry run. All metadata for telemetry channels is reset.
        """
        self.start_time = time.ticks_ms()

    def get_current_time(self):
        """
        Get the current time in milliseconds since last reset.
        
        :return: The current time in milliseconds
        :rtype: int
        """
        return time.ticks_diff(time.ticks_ms(), self.start_time)
    
    def send_telemetry(self, channel, data):
        """
        Send numeric telemetry data for a channel with the given name.
        
        :param channel: The name of the channel to send data for
        :type channel: str
        :param data: The numeric data to send
        :type data: float
        """
        raise NotImplementedError("send_telemetry method must be implemented by subclass")


class StdoutTelemetrySender(TelemetrySender):
    """
    Sends telemetry data directly to stdout without any additional processing or buffering.
    """

    def send_telemetry(self, channel, data):
        """
        Send telemetry data to stdout.
        
        :param channel: The name of the channel to send data for
        :type channel: str
        :param data: The numeric data to send
        :type data: float
        """
        current_time = self.get_current_time()
        print(f"[{current_time}] Telemetry channel {channel} at: {data}")