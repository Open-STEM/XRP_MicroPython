import time
from machine import Pin, Timer

class Rangefinder:

    """
    A class for using the HC-SR04 Ultrasonic Rangefinder that uses timers and interrupts to measure distance in a non-blocking way.
    The sensor range is between 2cm and 4m.
    Timeouts will return the previous legal value instead of raising an exception.
    """

    _DEFAULT_RANGEFINDER_INSTANCE = None

    @classmethod
    def get_default_rangefinder(cls):
        """
        Get the default XRP v2 rangefinder instance. This is a singleton, so only one instance of the rangefinder will ever exist.
        """
        if cls._DEFAULT_RANGEFINDER_INSTANCE is None:
            cls._DEFAULT_RANGEFINDER_INSTANCE = cls(20, 21)
        return cls._DEFAULT_RANGEFINDER_INSTANCE

    def __init__(self, trigger_pin:int, echo_pin:int, timeout_us:int=500*2*30):
        """
        : param trigger_pin: The number of the pin on the microcontroller that's connected
            to the ``Trig`` pin on the HC-SR04.
        : type trig_pin: int
        : param echo_pin: The number of the pin on the microcontroller that's connected
            to the ``Echo`` pin on the HC-SR04.
        : type echo_pin: int
        : param timeout_us: Max microseconds seconds to wait for a response from the
            sensor before assuming it isn't going to answer. By default set to 30,000 us (0.03 s)
        : type timeout_us: int
        """
        self.timeout_us = timeout_us
        # Init trigger pin (out)
        self._trigger = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        self._trigger.value(0)
        self.MAX_VALUE = 65535

        self.trigger_timer = Timer(-1)
        # Set a new timer to send a pulse every 5ms
        self.trigger_timer.init(period=100, mode=Timer.PERIODIC, callback=lambda t:self._send_pulse())

        # Init pulse tracking
        self._last_pulse_time = 0
        self.last_pulse_len = 0
        # Init echo pin (in)
        self._echo = Pin(echo_pin, mode=Pin.IN)
        self._echo.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=lambda pin:self._pulse_heard())


    def _send_pulse(self):
        """
        Send the pulse to trigger and listen on echo pin.
        When called on its own, blocks for 15us.
        """
        self._trigger.value(0) # Stabilize the sensor
        time.sleep_us(5)
        self._trigger.value(1) # Send the pulse
        
        time.sleep_us(10) # 10us wide pulse
        self._trigger.value(0)

    def _pulse_heard(self):
        """
        Interrupt handler that records the time of the echo pulse and computes the length of the pulse
        """
        pulse_time = time.ticks_us()
        if self._echo.value():
            # Rising edge of the pulse
            self._last_pulse_time = time.ticks_us()
        else:
            # Falling edge of the pulse
            pulse_len = time.ticks_diff(pulse_time, self._last_pulse_time)
            if pulse_len < self.timeout_us:
                self.last_pulse_len = pulse_len
            

    def distance(self) -> float:
        """
        Get the distance in centimeters by measuring the echo pulse time
        """

        # To calculate the distance we get the pulse_time and divide it by 2
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.034320 cm/us that is 1cm each 29.1us
        cms = (self.last_pulse_len / 2) / 29.1
        return cms
