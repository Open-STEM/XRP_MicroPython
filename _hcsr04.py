import machine, time
from machine import Pin

class HCSR04:
    """
    A basic class for using the HC-SR04 Ultrasonic Rangefinder.
    The sensor range is between 2cm and 4m.
    Timeouts will return a MAX_VALUE (65535) instead of raising an exception.
    """
    def __init__(self, trigger_pin:int, echo_pin:int, timeout_us=500*2*30:int):
        """
        :param trigger_pin: The number of the pin on the microcontroller that's connected
            to the ``Trig`` pin on the HC-SR04.
        :type trig_pin: int
        :param echo_pin: The number of the pin on the microcontroller that's connected
            to the ``Echo`` pin on the HC-SR04.
        :type echo_pin: int
        :param timeout_us: Max microseconds seconds to wait for a response from the
            sensor before assuming it isn't going to answer. By default set to 30,000 us (0.03 s)
        :type timeout_us: int
        """
        self.timeout_us = timeout_us
        # Init trigger pin (out)
        self.trigger = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        self.trigger.value(0)
        self.MAX_VALUE = 65535

        # Init echo pin (in)
        self.echo = Pin(echo_pin, mode=Pin.IN, pull=None)

    def _send_pulse_and_wait(self):
        """
        Send the pulse to trigger and listen on echo pin.
        We use the method `machine.time_pulse_us()` to get the microseconds until the echo is received.
        """
        self.trigger.value(0) # Stabilize the sensor
        time.sleep_us(5)
        self.trigger.value(1)
        # Send a 10us pulse.
        time.sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_time = machine.time_pulse_us(self.echo, 1, self.timeout_us)
            return pulse_time
        except OSError as exception:
            raise exception

    def distance(self):
        """
        Get the distance in centimeters with floating point operations.
        It returns a float
        """
        try:
            pulse_time = self._send_pulse_and_wait()
        except OSError as exception:
            # We don't want programs to crash if the HC-SR04 doesn't see anything in range
            # So we catch those errors and return 65535 instead
            if exception.args[0] == 110: # 110 = ETIMEDOUT
                return self.MAX_VALUE
            raise exception

        # To calculate the distance we get the pulse_time and divide it by 2
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.034320 cm/us that is 1cm each 29.1us
        cms = (pulse_time / 2) / 29.1
        return cms
