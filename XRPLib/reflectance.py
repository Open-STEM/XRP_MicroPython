from machine import Pin, ADC

class Reflectance:

    _DEFAULT_REFLECTANCE_INSTANCE = None

    @classmethod
    def get_default_reflectance(cls):
        """
        Get the default XRP reflectance sensor instance. This is a singleton, so only one instance of the reflectance sensor will ever exist.
        """
        if cls._DEFAULT_REFLECTANCE_INSTANCE is None:
            cls._DEFAULT_REFLECTANCE_INSTANCE = cls()
        return cls._DEFAULT_REFLECTANCE_INSTANCE

    def __init__(self, leftPin: int|str = "LINE_L", middlePin: int|str = "LINE_M", rightPin: int|str = "LINE_R"):
        """
        Implements for a reflectance sensor using the built in 12-bit ADC.
        Reads from analog in and converts to a float from 0 (white) to 1 (black)
        
        :param leftPin: The pin the left reflectance sensor is connected to
        :type leftPin: int|str
        :param middlePin: The pin the middle reflectance sensor is connected to
        :type middlePin: int|str
        :param rightPin: The pin the right reflectance sensor is connected to
        :type rightPin: int|str
        """
        self._leftReflectance = ADC(Pin(leftPin))
        self._rightReflectance = ADC(Pin(rightPin))

        # Guard for middlePin to prevent crashes on older XRP boards where LINE_M isn't defined
        self._middleReflectance = None
        if isinstance(middlePin, int):
            self._middleReflectance = ADC(Pin(middlePin))
        elif hasattr(Pin.board, middlePin):
            self._middleReflectance = ADC(Pin(middlePin))


        self.MAX_ADC_VALUE: int = 65536

    def _get_value(self, sensor: ADC) -> float:

        return sensor.read_u16() / self.MAX_ADC_VALUE

    def get_left(self) -> float:
        """
        Gets the the reflectance of the left reflectance sensor
        : return: The reflectance ranging from 0 (white) to 1 (black)
        : rtype: float
        """
        return self._get_value(self._leftReflectance)
        
    def get_middle(self) -> float:
        """
        Gets the reflectance of the middle sensor if available.
        :raises RuntimeError: If the middle pin is not supported on this board.
        :return: Reflectance from 0 (white) to 1 (black)
        : rtype: float
        """
        if self._middleReflectance is None:
            raise RuntimeError("Middle reflectance sensor is not available on this board configuration.")
        
        return self._get_value(self._middleReflectance)

    def get_right(self) -> float:
        """
        Gets the the reflectance of the right reflectance sensor
        : return: The reflectance ranging from 0 (white) to 1 (black)
        : rtype: float
        """
        return self._get_value(self._rightReflectance)
