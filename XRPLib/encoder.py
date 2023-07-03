from machine import Pin
from micropython import const

class Encoder:
    def __init__(self, aPin:int, bPin:int, ticks_per_revolution:int = 146.25):
        # TODO: Look into PIO implementation as to not take CPU time
        self.currentPosition = 0
        self.ticks_per_rev = ticks_per_revolution
        # Set pins as inputs
        self._aPin = Pin(aPin, Pin.IN)
        self._bPin = Pin(bPin, Pin.IN)
        # Set up both pins with an interrupt to update the encoder count on any change
        self._aPin.irq(trigger=Pin.IRQ_RISING, handler=lambda pin:self._isr())
        #self._bPin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=lambda pin:self.isr("b"))

        #self.prevAState = 0
        #self.prevBState = 0
        # Use a lookup table based on the pin transitions to figure out if we are running forwards or backwards
        #self._ENCODER_LOOKUP_TABLE = [ 0, 1, -1, 0,  -1, 0, 0, 1,  1, 0, 0, -1,  0, -1, 1, 0 ]


    def get_position(self):
        """
        : return: The position of the encoded motor, in revolutions, relative to the last time reset was called.
        : rtype: float
        """
        return self.currentPosition/self.ticks_per_rev
    
    # return position in ticks
    def get_position_ticks(self):
        """
        : return: The position of the encoder, in ticks, relative to the last time reset was called.
        : rtype: int
        """
        return self.currentPosition

    def reset_encoder_position(self):
        """
        Resets the encoder position back to zero.
        """
        self.currentPosition = 0

    def _isr(self):
        # aState = self._aPin.value()
        bState = self._bPin.value()

        # At rising edge of A. If B is low, we are going forwards, if B is high, we are going backwards
        if bState == 0:
            self.currentPosition -= 1
        else:
            self.currentPosition += 1

        #print(self.currentPosition)

        
        # index = self.prevAState*8 + self.prevBState*4 + aState*2 + bState

        # print(text, aState, bState, index)

        # self.currentPosition += self._ENCODER_LOOKUP_TABLE[index]

        # # DEBUG ONLY
        # #print(f"{index}, {self._ENCODER_LOOKUP_TABLE[index]}")

        # self.prevAState = aState
        # self.prevBState = bState
