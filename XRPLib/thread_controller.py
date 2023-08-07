import _thread
import time

class ThreadController():
    """
    A controlling class for scheduling functions and processes to occur on a separate thread.
    """
    _DEFAULT_THREAD_CONTROLLER = None

    @classmethod
    def get_default_thread_controller(cls):
        """
        Get the default secondary thread instance. This is a singleton, so only one instance of the second thread can ever exist.
        """
        if cls._DEFAULT_THREAD_CONTROLLER is None:
            cls._DEFAULT_THREAD_CONTROLLER = cls()
        return cls._DEFAULT_THREAD_CONTROLLER

    def __init__(self):
        self.to_run_list = []
        self.currently_running = False
        self.lock = _thread.allocate_lock()
        self.start_thread()

    def allocate_lock(self):
        """
        Allocates a lock for the thread.
        """
        return _thread.allocate_lock()

    def start_thread(self):
        """
        Starts the thread.
        """
        self.thread = _thread.start_new_thread(self._loop, ())

    def stop_thread(self):
        """
        Stops the thread.
        """
        self.thread.exit()

    def _loop(self):
        """
        A function to be run on a separate thread. This function will run all functions in the to_run_list.
        """
        while True:
            self.lock.acquire()
            if len(self.to_run_list) > 0:
                self.currently_running = True
                func = self.to_run_list.pop(0)
                self.lock.release()
                func()
            else:
                self.currently_running = False
                self.lock.release()
            time.sleep(0.001)

    def run(self, function, *args):
        """
        Sets a function to run on a separate thread.
        """
        self.lock.acquire()
        self.to_run_list.append(lambda: function(*args))
        self.lock.release()

    def is_running(self):
        """
        Returns whether or not the thread is currently running.
        """
        self.lock.acquire()
        currently_running = self.currently_running
        self.lock.release()

        return currently_running
    
    def wait_until_done(self):
        """
        Waits until the thread is done running all functions in the to_run_list.
        """
        while self.is_running():
            time.sleep(0.001)