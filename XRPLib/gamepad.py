from ble.blerepl import uart
import sys
from micropython import const

class Gamepad:

    _DEFAULT_GAMEPAD_INSTANCE = None

    X1 = const(0)
    Y1 = const(1)
    X2 = const(2)
    Y2 = const(3)
    BUTTON_A = const(4)
    BUTTON_B = const(5)
    BUTTON_X = const(6)
    BUTTON_Y = const(7)
    BUMPER_L = const(8)
    BUMPER_R = const(9)
    TRIGGER_L = const(10)
    TRIGGER_R = const(11)
    BACK = const(12)
    START = const(13)
    DPAD_UP = const(14)
    DPAD_DN = const(15)
    DPAD_L = const(16)
    DPAD_R = const(17)

    _joyData = [
    0.0,
    0.0,
    0.0,
    0.0,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0]

    @classmethod
    def get_default_gamepad(cls):
        """
        Get the default XRP bluetooth joystick instance. This is a singleton, so only one instance of the gamepad sensor will ever exist.
        """
        if cls._DEFAULT_GAMEPAD_INSTANCE is None:
            cls._DEFAULT_GAMEPAD_INSTANCE = cls()
        cls._DEFAULT_GAMEPAD_INSTANCE.start()
        return cls._DEFAULT_GAMEPAD_INSTANCE

    def __init__(self):
        """
        Manages communication with gamepad data coming from a remote computer via bluetooth

        """
    def start(self):
        """
        Signals the remote computer to begin sending gamepad data packets.
        """
        for i in range(len(self._joyData)):
            self._joyData[i] = 0.0
        uart.set_data_callback(self._data_callback)
        sys.stdout.write(chr(27))
        sys.stdout.write(chr(101))


    def stop(self):
        """
        Signals the remote computer to stop sending gamepad data packets. 
        """
        sys.stdout.write(chr(27))
        sys.stdout.write(chr(102))

    def get_value(self, index:int) -> float:
        """
        Get the current value of a joystick axis

        :param index: The joystick axis index 
        Gamepad.X1, Gamepad.Y1, Gamepad.X2, Gamepad.Y2
        :type int
        :returns: The value of the joystick between -1 and 1
        :rtype: float
        """
        return -self._joyData[index] #returning the negative to make normal for user 

    def is_button_pressed(self, index:int) -> bool:
        """
        Checks if a specific button is currently pressed.

        :param index: The button index
        Gamepad.BUTTON_A, Gamepad.TRIGGER_L, Gamepad.DPAD_UP, etc
        :type int
        :returns: The value of the button 1 or 0
        :rtype: bool
        """
        return self._joyData[index] > 0      

    def _data_callback(self, data):
        if(data[0] == 0x55 and len(data) == data[1] + 2):
            for i in range(2, data[1] + 2, 2):
                self._joyData[data[i]] = round(data[i + 1]/127.5 - 1, 2)
            
        
