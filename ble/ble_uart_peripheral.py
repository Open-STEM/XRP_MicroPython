# This implements the Nordic UART Service (NUS).

import bluetooth
#from .ble_advertising import advertising_payload
import struct
from micropython import const
from machine import Timer

#Advertise info
# org.bluetooth.characteristic.gap.appearance.xml
_ADV_APPEARANCE_GENERIC_COMPUTER = const(128)
_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_APPEARANCE = const(0x19)
_ADV_TYPE_NAME = const(0x09)

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_INDICATE_DONE = const(20)

_FLAG_READ = const(0x0002)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE,
)

# Define a new UUID for the binary data characteristic.
_UART_DATA_RX = (
    bluetooth.UUID("92ae6088-f24d-4360-b1b1-a432a8ed36ff"),
    _FLAG_WRITE,
)
# Define a new UUID for the binary data characteristic.
_UART_DATA_TX = (
    bluetooth.UUID("92ae6088-f24d-4360-b1b1-a432a8ed36fe"),
    _FLAG_NOTIFY,
)

_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX, _UART_DATA_RX, _UART_DATA_TX,),
)

_timer = Timer(-1)

def delayedRestart(_arg):
        import machine
        machine.reset()

class BLEUART:
    def __init__(self, ble, name="mpy-uart", rxbuf=100):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._tx_handle, self._rx_handle, self._data_rx_handle, self._data_tx_handle),) = self._ble.gatts_register_services((_UART_SERVICE,))
        # Increase the size of the rx buffer and enable append mode.
        self._ble.gatts_set_buffer(self._rx_handle, rxbuf, True)
        self._connections = set()
        self._rx_buffer = bytearray()
        self._handler = None
        self._payload = self._advertising_payload(name, _ADV_APPEARANCE_GENERIC_COMPUTER)
        self._data_callback = None
        self._advertise()

    def irq(self, handler):
        self._handler = handler

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if conn_handle in self._connections and value_handle == self._rx_handle:
                self._rx_buffer += self._ble.gatts_read(self._rx_handle)
                if(self._rx_buffer.find(b'##XRPSTOP#' + b'#') != -1): #WARNING: This is broken up so it won't restart during an update or this file.
                    self._rx_buffer = bytearray()
                    # set the bit in isrunning to tell main not to re-run the program so the IDE can connect
                    FILE_PATH = '/lib/ble/isrunning'
                    with open(FILE_PATH, 'r+b') as file:
                        file.write(b'\x01')
                    # slight delay to avoid errors on the browser side.
                    _timer.init(mode=Timer.PERIODIC, period=50, callback=delayedRestart)
            elif conn_handle in self._connections and value_handle == self._data_rx_handle:
                new_data = self._ble.gatts_read(self._data_rx_handle)
                if self._data_callback:
                    self._data_callback(new_data)
                    #schedule(self._data_callback, new_data)
        elif event == _IRQ_GATTS_INDICATE_DONE:
            if self._handler:
                self._handler()
        #else:
            #print("IRQ Event Code: " + str(event))

    def any(self):
        return len(self._rx_buffer)

    def read(self, sz=None):
        if not sz:
            sz = len(self._rx_buffer)
        result = self._rx_buffer[0:sz]
        self._rx_buffer = self._rx_buffer[sz:]
        return result

    def write(self, data):
        #print("write:" + data)
        for conn_handle in self._connections:
            self._ble.gatts_indicate(conn_handle, self._tx_handle, data)

    def write_data(self, data):
        #print("write_data:" + data)
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._data_tx_handle, data)
            
    def set_data_callback(self, callback):
        self._data_callback = callback
        
    def clear_data_callback(self):
        self._data_callback = None

    def close(self):
        for conn_handle in self._connections:
            self._ble.gap_disconnect(conn_handle)
        self._connections.clear()

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    # Generate a payload to be passed to gap_advertise(adv_data=...).
    def _advertising_payload(self, name, appearance):
        payload = bytearray()

        def _append(adv_type, value):
            nonlocal payload
            payload += struct.pack("BB", len(value) + 1, adv_type) + value

        _append(
            _ADV_TYPE_FLAGS,
            struct.pack("B", 0x02 + 0x04),
        )
        _append(_ADV_TYPE_NAME, name)
        _append(_ADV_TYPE_APPEARANCE, struct.pack("<h", appearance))
        
        return payload