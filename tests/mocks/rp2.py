"""
Mock rp2 module for desktop unit testing.
"""


class PIO:
    SHIFT_LEFT = 0
    SHIFT_RIGHT = 1


class StateMachine:
    def __init__(self, index, program=None, in_base=None, *args, **kwargs):
        self._index = index
        self._active = False
        self._x = 0

    def active(self, state=None):
        if state is not None:
            self._active = bool(state)
        return self._active

    def get(self):
        return self._x

    def exec(self, instruction):
        if "set(x, 0)" in instruction:
            self._x = 0

    def _set_count(self, count):
        self._x = count


def asm_pio(**kwargs):
    """Decorator that returns the function unchanged for testing."""
    def decorator(func):
        return func
    return decorator
