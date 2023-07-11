import time

class Timeout:
    def __init__(self, timeout):
        """
        Starts a timer that will expire after the given timeout.

        :param timeout: The timeout, in seconds
        :type timeout: float
        """
        self.timeout = timeout
        self.start_time = time.time()
    
    def is_done(self):
        """
        :return: True if the timeout has expired, False otherwise
        """
        if self.timeout is None:
            return False
        return time.time() - self.start_time > self.timeout