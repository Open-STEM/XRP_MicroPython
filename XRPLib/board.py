from machine import Pin, ADC, Timer
from neopixel import NeoPixel
import time
import sys

class Board:

    _DEFAULT_BOARD_INSTANCE = None

    @classmethod
    def get_default_board(cls):
        """
        Get the default board instance. This is a singleton, so only one instance of the board will ever exist.
        """
        if cls._DEFAULT_BOARD_INSTANCE is None:
            cls._DEFAULT_BOARD_INSTANCE = cls()
        return cls._DEFAULT_BOARD_INSTANCE

    def __init__(self, vin_pin="BOARD_VIN_MEASURE", button_pin="BOARD_USER_BUTTON", 
                 rgb_led_pin = "BOARD_NEOPIXEL", led_pin = "LED"):
        """
        Implements for extra features on the XRP board. Handles the on/off switch, button, and LED.

        :param vin_pin: The pin the on/off switch is connected to
        :type vin_pin: int
        :param button_pin: The pin the button is connected to
        :type button_pin: int
        """

        self.on_switch = ADC(Pin(vin_pin))
        
        self.button = Pin(button_pin, Pin.IN, Pin.PULL_UP)

        self.led = Pin(led_pin, Pin.OUT)

        if hasattr(Pin.board, rgb_led_pin):
            self.rgb_led = NeoPixel(Pin(rgb_led_pin, Pin.OUT), 1)
        # A timer ID of -1 is a virtual timer.
        # Leaves the hardware timers for more important uses
        self._virt_timer = Timer(-1)
        self.is_led_blinking = False


    def are_motors_powered(self) -> bool:
        """
        :return: Returns true if the batteries are connected and powering the motors, false otherwise
        :rytpe: bool
        """
        return self.on_switch.read_u16() > 20000

    def is_button_pressed(self) -> bool:
        """
        Returns the state of the button

        :return: True if the button is pressed, False otherwise
        :rtype: bool
        """
        return not self.button.value()
    
    def wait_for_button(self):
        """
        Halts the program until the button is pressed
        """

        # Wait until user command before running
        while not self.is_button_pressed():
            time.sleep(.01)

        # Wait until user to release button before running
        while self.is_button_pressed():
            time.sleep(.01)

    
    def led_on(self):
        """
        Turns the LED on
        Stops the blinking timer if it is running
        """
        self.is_led_blinking = False
        self.led.on()
        self._virt_timer.deinit()

    def led_off(self):
        """
        Turns the LED off
        Stops the blinking timer if it is running
        """
        self.is_led_blinking = False
        self.led.off()
        self._virt_timer.deinit()

    def led_blink(self, frequency: int=0):
        """
        Blinks the LED at a given frequency. If the frequency is 0, the LED will stop blinking.

        :param frequency: The frequency to blink the LED at (in Hz)
        :type frequency: int
        """
        if self.is_led_blinking:
            # disable the old timer so we can reinitialize it
            self._virt_timer.deinit()
        # We set it to twice in input frequency so that
        # the led flashes on and off frequency times per second
        if frequency != 0:
            self._virt_timer.init(freq=frequency*2, mode=Timer.PERIODIC,
                callback=lambda t:self.led.toggle())
            self.is_led_blinking = True
        else:
            self._virt_timer.deinit()
            self.is_led_blinking = False

    def set_rgb_led(self, r:int, g:int, b:int):
        """
        Sets the Neopixel RGB LED to a specified color. Throws a NotImplementedError on the XRP Beta

        :param r: The amount of red in the desired color
        :type r: int
        :param g: The amount of green in the desired color
        :type g: int
        :param b: The amount of blue in the desired color
        :type b: int
        """
        if "rgb_led" in self.__dict__:
            self.rgb_led[0] = (r, g, b)
            self.rgb_led.write()
        else:
            raise NotImplementedError("Board.set_rgb_led not implemented for the XRP Beta")
