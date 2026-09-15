import time
from machine import Pin, Timer

class Rangefinder:

    _DEFAULT_RANGEFINDER_INSTANCE = None
    _instances = []
    _timer = None
    _current_index = 0

    @classmethod
    def get_default_rangefinder(cls):
        """
        Get the default XRP rangefinder instance. This is a singleton, so only one instance of the rangefinder will ever exist.
        """
        if cls._DEFAULT_RANGEFINDER_INSTANCE is None:
            cls._DEFAULT_RANGEFINDER_INSTANCE = cls()
        return cls._DEFAULT_RANGEFINDER_INSTANCE

    @classmethod
    def _start_shared_timer(cls):
        """
        Start the shared timer if it isn't already running.
        One timer cycles through all rangefinder instances to prevent acoustic crosstalk.
        """
        if cls._timer is None:
            cls._timer = Timer(-1)
            cls._timer.init(mode=Timer.PERIODIC, period=60, callback=cls._timer_callback)

    @classmethod
    def _timer_callback(cls, _t):
        """
        Shared timer callback that triggers one rangefinder per tick,
        cycling through all instances in round-robin order.
        """
        if not cls._instances:
            return
        instance = cls._instances[cls._current_index]
        instance._do_ping()
        cls._current_index = (cls._current_index + 1) % len(cls._instances)

    def __init__(self, trigger_pin: int|str = "RANGE_TRIGGER", echo_pin: int|str = "RANGE_ECHO", timeout_us:int=500*2*30):
        """
        A non-blocking class for using the HC-SR04 Ultrasonic Rangefinder.
        The sensor range is between 2cm and 4m.
        Measurements are taken continuously in the background using a shared timer
        and pin IRQ, so distance() returns immediately with the most recent value.
        When multiple rangefinders exist, they are pinged sequentially to prevent
        acoustic crosstalk.
        Timeouts will return a MAX_VALUE (65535) instead of raising an exception.

        :param trigger_pin: The number of the pin on the microcontroller that's connected to the ``Trig`` pin on the HC-SR04.
        :type trigger_pin: int
        :param echo_pin: The number of the pin on the microcontroller that's connected to the ``Echo`` pin on the HC-SR04.
        :type echo_pin: int
        :param timeout_us: Max microseconds to wait for a response from the sensor before assuming it isn't going to answer. By default set to 30,000 us (0.03 s)
        :type timeout_us: int
        """
        self.timeout_us = timeout_us
        # Init trigger pin (out)
        self._trigger = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        self._trigger.value(0)
        self.MAX_VALUE = 65535

        # Init echo pin (in)
        self.echo = Pin(echo_pin, mode=Pin.IN, pull=None)

        # Cache time functions as instance attributes for use in hard IRQ context,
        # where global module lookups are not allowed
        self._ticks_us = time.ticks_us
        self._ticks_diff = time.ticks_diff

        self.cms = self.MAX_VALUE
        self._echo_start = 0
        self._waiting_for_echo = False
        self._trigger_time = 0
        self._first_reading_done = False

        # Pre-bind methods as instance attributes so the shared timer callback
        # can call them without creating bound method objects (which would
        # allocate memory in hard IRQ context)
        self._do_ping = self._trigger_ping
        self._do_echo = self._echo_handler

        # Register echo pin IRQ for both rising and falling edges
        self.echo.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._do_echo)

        # Register this instance and start the shared timer
        Rangefinder._instances.append(self)
        Rangefinder._start_shared_timer()

    def _trigger_ping(self):
        """
        Send a trigger pulse to the HC-SR04.
        Called by the shared timer callback.
        Only ~15us of work per call (negligible blocking).
        Also detects timeouts from previous measurements.
        """
        if self._waiting_for_echo:
            # Check if previous measurement timed out
            if self._ticks_diff(self._ticks_us(), self._trigger_time) > self.timeout_us:
                self.cms = self.MAX_VALUE
                self._waiting_for_echo = False
                self._first_reading_done = True
            else:
                # Still waiting for a valid echo, skip this trigger
                return

        # Send trigger pulse
        self._trigger.value(0)
        self._delay_us(5)
        self._trigger.value(1)
        self._delay_us(10)
        self._trigger.value(0)
        self._trigger_time = self._ticks_us()
        self._waiting_for_echo = True

    def _echo_handler(self, pin):
        """
        Pin IRQ handler for the echo pin.
        Rising edge: record start time.
        Falling edge: compute distance from pulse width.
        """
        if pin.value() == 1:
            # Rising edge - echo pulse started
            self._echo_start = self._ticks_us()
        else:
            # Falling edge - echo pulse ended
            if self._waiting_for_echo:
                pulse_time = self._ticks_diff(self._ticks_us(), self._echo_start)
                if pulse_time > 0:
                    # Sound speed 343.2 m/s = 0.034320 cm/us = 1cm per 29.1us
                    # Divide by 2 because pulse travels to target and back
                    self.cms = (pulse_time / 2) / 29.1
                else:
                    self.cms = self.MAX_VALUE
                self._waiting_for_echo = False
                self._first_reading_done = True

    def distance(self) -> float:
        """
        Get the most recent distance measurement in centimeters.
        Blocks until the first measurement is available, then returns
        immediately on all subsequent calls.
        """
        while not self._first_reading_done:
            pass
        return self.cms

    def _delay_us(self, delay:int):
        """
        Custom implementation of time.sleep_us(), used to get around the bug in MicroPython where time.sleep_us()
        doesn't work properly and causes the IDE to hang when uploading the code
        """
        start = self._ticks_us()
        while self._ticks_diff(self._ticks_us(), start) < delay:
            pass
