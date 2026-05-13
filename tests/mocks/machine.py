"""
Mock machine module for desktop unit testing.
Simulates Pin, ADC, PWM, Timer, I2C, disable_irq, enable_irq.
"""


class _PinBoard:
    """Simulates Pin.board with named pin attributes."""
    BOARD_VIN_MEASURE = 26
    BOARD_USER_BUTTON = 22
    BOARD_NEOPIXEL = 4
    LED = 25
    MOTOR_L_IN_1 = 6
    MOTOR_L_IN_2 = 7
    MOTOR_R_IN_1 = 14
    MOTOR_R_IN_2 = 15
    MOTOR_L_ENCODER_A = 0
    MOTOR_L_ENCODER_B = 1
    MOTOR_R_ENCODER_A = 2
    MOTOR_R_ENCODER_B = 3
    MOTOR_3_IN_1 = 8
    MOTOR_3_IN_2 = 9
    MOTOR_3_ENCODER_A = 10
    MOTOR_3_ENCODER_B = 11
    MOTOR_4_IN_1 = 12
    MOTOR_4_IN_2 = 13
    MOTOR_4_ENCODER_A = 16
    MOTOR_4_ENCODER_B = 17
    RANGE_TRIGGER = 20
    RANGE_ECHO = 21
    LINE_L = 27
    LINE_R = 28
    I2C_SCL_1 = 19
    I2C_SDA_1 = 18
    SERVO_1 = 10
    SERVO_2 = 11
    SERVO_3 = 12
    SERVO_4 = 13

    def __getattr__(self, name):
        # Return any pin name as an integer so hasattr() works
        return hash(name) % 30


class Pin:
    IN = 0
    OUT = 1
    PULL_UP = 1
    PULL_DOWN = 2
    IRQ_RISING = 1
    IRQ_FALLING = 2

    board = _PinBoard()

    def __init__(self, pin_id=0, mode=None, pull=None, *args, **kwargs):
        if isinstance(pin_id, str):
            self._pin_id = getattr(Pin.board, pin_id, 0)
        else:
            self._pin_id = pin_id
        self._mode = mode
        self._value = 0
        self._irq_handler = None

    def value(self, v=None):
        if v is not None:
            self._value = v
        return self._value

    def on(self):
        self._value = 1

    def off(self):
        self._value = 0

    def toggle(self):
        self._value = 1 - self._value

    def irq(self, trigger=None, handler=None):
        self._irq_handler = handler


class ADC:
    def __init__(self, pin=None):
        self._value = 0

    def read_u16(self):
        return self._value

    def _set_value(self, v):
        self._value = v


class PWM:
    def __init__(self, pin=None):
        self._freq = 0
        self._duty_u16 = 0
        self._duty_ns = 0

    def freq(self, f=None):
        if f is not None:
            self._freq = f
        return self._freq

    def duty_u16(self, d=None):
        if d is not None:
            self._duty_u16 = d
        return self._duty_u16

    def duty_ns(self, d=None):
        if d is not None:
            self._duty_ns = d
        return self._duty_ns


class Timer:
    ONE_SHOT = 0
    PERIODIC = 1

    def __init__(self, timer_id=-1):
        self._id = timer_id
        self._callback = None
        self._period = None
        self._freq = None

    def init(self, mode=PERIODIC, period=None, freq=None, callback=None):
        self._mode = mode
        self._period = period
        self._freq = freq
        self._callback = callback

    def deinit(self):
        self._callback = None
        self._period = None
        self._freq = None


class I2C:
    def __init__(self, id=0, scl=None, sda=None, freq=400000):
        self._id = id
        self._freq = freq
        self._data = {}

    def writeto_mem(self, addr, reg, data):
        self._data[(addr, reg)] = bytes(data)

    def readfrom_mem_into(self, addr, reg, buf):
        data = self._data.get((addr, reg), bytes(len(buf)))
        for i in range(min(len(buf), len(data))):
            buf[i] = data[i]


def disable_irq():
    return 0


def enable_irq(state):
    pass
