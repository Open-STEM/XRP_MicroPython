from machine import Pin, ADC

class Reflectance:

    """
    Implements for a reflectance sensor using the built in 12-bit ADC.
    Reads from analog in and converts to a float from 0 (white) to 1 (black)
    """

    def __init__(self, leftPin, rightPin):
        self._leftReflectance = ADC(Pin(leftPin))
        # Set the ADC vref to 3.3V

        self._rightReflectance = ADC(Pin(rightPin))
        # Set the ADC vref to 3.3V

        self.MAX_ADC_VALUE: int = 65536

    def _get_value(self, sensor: ADC) -> float:

        return sensor.read_u16() / self.MAX_ADC_VALUE

    def get_left(self) -> float:
        """
        Gets the the reflectance of the left reflectance sensor
        :return: The reflectance ranging from 0 (white) to 1 (black)
        :rtype: float
        """
        return self._get_value(self._leftReflectance)

    def get_right(self) -> float:
        """
        Gets the the reflectance of the right reflectance sensor
        :return: The reflectance ranging from 0 (white) to 1 (black)
        :rtype: float
        """
        return self._get_value(self._rightReflectance)
