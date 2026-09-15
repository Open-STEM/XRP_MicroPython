"""
Mock NeoPixel module for desktop unit testing.
"""


class NeoPixel:
    def __init__(self, pin, count):
        self._pixels = [(0, 0, 0)] * count

    def __setitem__(self, index, value):
        self._pixels[index] = value

    def __getitem__(self, index):
        return self._pixels[index]

    def write(self):
        pass
