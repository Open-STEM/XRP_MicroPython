from machine import Pin
from micropython import const

class Encoder:
    def __init__(self, aPin:int, bPin:int, ticks_per_revolution:int = 585):
        self.currentPosition = 0
        self.ticks_per_rev = ticks_per_revolution
        # Set pins as inputs
        self._aPin = Pin(aPin, Pin.IN)
        self._bPin = Pin(bPin, Pin.IN)
        # Set up both pins with an interrupt to update the encoder count on any change
        self._aPin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=lambda pin:self.isr())
        self._bPin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=lambda pin:self.isr())

        self.prevAState = 0
        self.prevBState = 0
        # Use a lookup table based on the pin transitions to figure out if we are running forwards or backwards
        self._ENCODER_LOOKUP_TABLE = [ 0, 1, -1, 0,  -1, 0, 0, 1,  1, 0, 0, -1,  0, -1, 1, 0 ]


    def get_position(self):
        return self.currentPosition/self.ticks_per_rev

    def reset_encoder_position(self):
        self.currentPosition = 0

    def isr(self):
        aState = self._aPin.value()
        bState = self._bPin.value()

        index = self.prevAState*8 + self.prevBState*4 + aState*2 + bState

        self.currentPosition += self._ENCODER_LOOKUP_TABLE[index]

        # DEBUG ONLY
        #print(f"{index}, {self._ENCODER_LOOKUP_TABLE[index]}")

        self.prevAState = aState
        self.prevBState = bState
