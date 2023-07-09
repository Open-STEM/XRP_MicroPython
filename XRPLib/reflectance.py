from machine import Pin, ADC

class Reflectance:



    _DEFAULT_REFLECTANCE_INSTANCE = None

    @classmethod
    def get_default_reflectance(cls):
        """
        Get the default XRP v2 reflectance sensor instance. This is a singleton, so only one instance of the reflectance sensor will ever exist.
        """
        if cls._DEFAULT_REFLECTANCE_INSTANCE is None:
            cls._DEFAULT_REFLECTANCE_INSTANCE = cls(26, 27)
        return cls._DEFAULT_REFLECTANCE_INSTANCE

    def __init__(self, leftPin:int, rightPin:int):
        """
        Implements for a reflectance sensor using the built in 12-bit ADC.
        Reads from analog in and converts to a float from 0 (white) to 1 (black)
        
        :param leftPin: The pin the left reflectance sensor is connected to
        :type leftPin: int
        :param rightPin: The pin the right reflectance sensor is connected to
        :type rightPin: int
        """
        self._leftReflectance = ADC(Pin(leftPin))
        self._rightReflectance = ADC(Pin(rightPin))

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

    def get_right(self) -> float:
        """
        Gets the the reflectance of the right reflectance sensor
        : return: The reflectance ranging from 0 (white) to 1 (black)
        : rtype: float
        """
        return self._get_value(self._rightReflectance)
