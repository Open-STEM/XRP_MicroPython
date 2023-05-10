from machine import Pin, Timer

class LED:

    """
    A very simple class for using the LED onboard the Raspberry Pi Pico
    Uses a virtual timer to allow for flexible blinking control
    Default pin on the XRP Controller is Pin 25
    """

    def __init__(self, ledPin="LED"):
        self._led = Pin(ledPin, Pin.OUT)
        # A timer ID of -1 is a virtual timer.
        # Leaves the hardware timers for more important uses
        self._virt_timer = Timer(-1)
        self.is_blinking = False

    def blink(self, frequency: int):
        if self.is_blinking:
            # disable the old timer so we can reinitialize it
            self._virt_timer.deinit()
        # We set it to twice in input frequency so that
        # the led flashes on and off frequency times per second
        self._virt_timer.init(freq=frequency*2, mode=Timer.PERIODIC,
            callback=lambda t:self.change_state())
        self.is_blinking = True

    def change_state(self):
        self._led.toggle()

    def off(self):
        self.is_blinking = False
        self._led.off()
        self._virt_timer.deinit()

    def on(self):
        self.is_blinking = False
        self._led.on()
        self._virt_timer.deinit()
