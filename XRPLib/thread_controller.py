import _thread
import time
import gc
from machine import Timer

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
        _thread.start_new_thread(self._loop, ())

        # Set garbage collector to run every 50ms on the second thread to avoid memory leak
        gc.enable()
        self.gc_timer = Timer(-1)
        self.run(lambda: self.gc_timer.init(period=50, callback= lambda t:gc.collect()), ())

    def allocate_lock(self):
        """
        Allocates a lock for the thread.
        """
        return _thread.allocate_lock()

    def _loop(self):
        """
        A function to be run on a separate thread. This function will run all functions in the to_run_list.
        """
        while True:
            self.lock.acquire()
            if len(self.to_run_list) > 0:
                self.currently_running = True
                func = self.to_run_list.pop(0)
                print("Second thread received function")
                self.lock.release()
                func()
            else:
                self.currently_running = False
                self.lock.release()
            time.sleep(0.01)

    def run(self, function, args):
        """
        Sets a function to run on a separate thread.
        """
        with self.lock:
            self.to_run_list.append(lambda: function(*args))

    def is_running(self):
        """
        Returns whether or not a function is currently running on this thread.
        """
        with self.lock:
            currently_running = self.currently_running

        return currently_running
    
    def wait_until_done(self):
        """
        Waits until the thread is done running all functions in the to_run_list.
        """
        while self.is_running():
            time.sleep(0.01)