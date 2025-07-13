import time

class Timeout:
    def __init__(self, timeout: float):
        """
        Starts a timer that will expire after the given timeout.

        :param timeout: The timeout, in seconds
        :type timeout: float
        """
        self.timeout = timeout
        if self.timeout != None:
            self.timeout = timeout*1000
        
        self.start_time = time.ticks_ms()
    
    def is_done(self):
        """
        :return: True if the timeout has expired, False otherwise
        """
        if self.timeout is None:
            return False
        return time.ticks_ms() - self.start_time > self.timeout