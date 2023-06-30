from machine import Pin, ADC

# Last updated 29-June-2023
__version__ = '0.8'

class Board:

    _DEFAULT_BOARD_INSTANCE = None

    @classmethod
    def get_default_board(cls):
        """
        Get the default board instance. This is a singleton, so only one instance of the board will ever exist.
        """
        if cls._DEFAULT_BOARD_INSTANCE is None:
            cls._DEFAULT_BOARD_INSTANCE = cls(28)
        return cls._DEFAULT_BOARD_INSTANCE

    def __init__(self, vin_pin:int):
        self.on_switch = ADC(Pin(vin_pin))


    def are_motors_powered(self):
        """
        Returns true if the batteries are connected and powering the motors, false otherwise
        """
        return self.on_switch.read_u16() > 20000
