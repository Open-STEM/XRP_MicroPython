# REPL over ble 5.0 using the Nordic UART protocal

import bluetooth
import io
import os
import micropython
from micropython import const
from machine import Timer, Pin, disable_irq, enable_irq, unique_id
import time
                    

from ble.ble_uart_peripheral import BLEUART

_MP_STREAM_POLL = const(3)
_MP_STREAM_POLL_RD = const(0x0001)

_timer = Timer(-1)

waitingForTimer = False

uart = None

#_led = Pin("LED", Pin.OUT) //for debugging

# Batch writes into 50ms intervals.
def schedule_in(handler, delay_ms):
    def _wrap(_arg):
        handler()
    #using PERIODIC vs ONE_SHOT because sometimes ONE_SHOT didn't fire when IMU timer was going
    #We deinit() once the timer goes off. So for all means a ONE_SHOT.
    _timer.init(mode=Timer.PERIODIC, period=delay_ms, callback=_wrap)

# Simple buffering stream to support the dupterm requirements.
class BLEUARTStream(io.IOBase):
    def __init__(self, uart):
        self._uart = uart
        self._tx_buf = bytearray()
        self._uart.irq(self._indicate_handler)
        self._tx_buf_index = 0


    def _indicate_handler(self):
        if waitingForTimer:
            return
        if self._tx_buf:
            self._flush()
            
    def _timer_handler(self):
        waitingForTimer = False
        _timer.deinit()
        if self._tx_buf:
            self._flush()

    def read(self, sz=None):
        return self._uart.read(sz)

    def readinto(self, buf):
        avail = self._uart.read(len(buf))
        if not avail:
            return None
        for i in range(len(avail)):
            buf[i] = avail[i]
        return len(avail)

    def ioctl(self, op, arg):
        if op == _MP_STREAM_POLL:
            if self._uart.any():
                return _MP_STREAM_POLL_RD
        return 0

    def _flush(self):
        data = self._tx_buf[self._tx_buf_index:self._tx_buf_index + 200]
        self._tx_buf_index += 200
        if self._tx_buf_index >= len(self._tx_buf):
            self._tx_buf = bytearray()
            self._tx_buf_index = 0
        self._uart.write(data)

    def write(self, buf):
        state = disable_irq()
        empty = not self._tx_buf
        self._tx_buf += buf
        enable_irq(state)

        if empty:
            waitingForTimer = True
            schedule_in(self._timer_handler, 50)

def background_task():
    global uart
    ble = bluetooth.BLE()
    x = (''.join(['{:02x}'.format(b) for b in unique_id()]))
    uart = BLEUART(ble, name="XRP-" + x[11:], rxbuf = 250)
    stream = BLEUARTStream(uart)
    os.dupterm(stream,0)

# Start the background task
background_task()
    