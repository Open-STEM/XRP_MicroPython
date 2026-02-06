from .puppet import Puppet, VAR_TYPE_FLOAT, VAR_TYPE_INT, VAR_TYPE_BOOL, PERM_WRITE_ONLY, PERM_READ_ONLY
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

    # Mapping from index to variable name
    _VAR_NAMES = {
        0: '$gamepad.x1',
        1: '$gamepad.y1',
        2: '$gamepad.x2',
        3: '$gamepad.y2',
        4: '$gamepad.button_a',
        5: '$gamepad.button_b',
        6: '$gamepad.button_x',
        7: '$gamepad.button_y',
        8: '$gamepad.bumper_l',
        9: '$gamepad.bumper_r',
        10: '$gamepad.trigger_l',
        11: '$gamepad.trigger_r',
        12: '$gamepad.back',
        13: '$gamepad.start',
        14: '$gamepad.dpad_up',
        15: '$gamepad.dpad_dn',
        16: '$gamepad.dpad_l',
        17: '$gamepad.dpad_r',
    }

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
        Manages communication with gamepad data coming from a remote computer via XPP protocol.
        """
        self._puppet = Puppet.get_default_puppet()
        self._started = False
        
        # Register all gamepad variables
        self._register_variables()

    def _register_variables(self):
        """
        Register all gamepad variables with the XPP protocol.
        """
        # Joystick axes are floats
        for idx in [self.X1, self.Y1, self.X2, self.Y2]:
            var_name = self._VAR_NAMES[idx]
            self._puppet.define_variable(var_name, VAR_TYPE_FLOAT, PERM_WRITE_ONLY)
        
        # Buttons are integers (1 or 0)
        for idx in range(4, 18):
            var_name = self._VAR_NAMES[idx]
            self._puppet.define_variable(var_name, VAR_TYPE_INT, PERM_WRITE_ONLY)
        
        # Register gamepad enabled variable (read-only from XRP side)
        self._puppet.define_variable('$gamepad.enabled', VAR_TYPE_BOOL, PERM_READ_ONLY)

    def start(self):
        """
        Signals the remote computer to begin sending gamepad data packets.
        Subscribes to all gamepad variables at a high rate (50 Hz).
        """
        self._puppet.start()
        self._puppet.send_program_start()

        # Enable gamepad - signal to client to start sending
        self._puppet.set_variable('$gamepad.enabled', True)

        if self._started:
            return
        
        # Subscribe to all gamepad variables at 50 Hz
        for var_name in self._VAR_NAMES.values():
            self._puppet.subscribe_variable(var_name, 50)
        
        self._started = True

    def stop(self):
        """
        Signals the remote computer to stop sending gamepad data packets.
        Unsubscribes from all gamepad variables.
        """

        self._puppet.send_program_end()

        if not self._started:
            return
        
        # Disable gamepad - signal to client to stop sending
        self._puppet.set_variable('$gamepad.enabled', False)
        
        # Unsubscribe from all gamepad variables
        for var_name in self._VAR_NAMES.values():
            self._puppet.subscribe_variable(var_name, 0)
            
        self._puppet.stop()
        self._started = False

    def get_value(self, index: int) -> float:
        """
        Get the current value of a joystick axis

        :param index: The joystick axis index 
        Gamepad.X1, Gamepad.Y1, Gamepad.X2, Gamepad.Y2
        :type int
        :returns: The value of the joystick between -1 and 1
        :rtype: float
        """
        if index not in self._VAR_NAMES:
            return 0.0
        
        var_name = self._VAR_NAMES[index]
        try:
            value = self._puppet.get_variable(var_name)
            # Return negative to make normal for user (backward compatibility)
            return -value
        except:
            # Return default if variable not available
            return 0.0

    def is_button_pressed(self, index: int) -> bool:
        """
        Checks if a specific button is currently pressed.

        :param index: The button index
        Gamepad.BUTTON_A, Gamepad.TRIGGER_L, Gamepad.DPAD_UP, etc
        :type int
        :returns: The value of the button 1 or 0
        :rtype: bool
        """
        if index not in self._VAR_NAMES:
            return False
        
        var_name = self._VAR_NAMES[index]
        try:
            value = self._puppet.get_variable(var_name)
            # Works for both int and float
            return value > 0
        except:
            # Return default if variable not available
            return False
