"""
Pytest conftest that installs mock modules before any XRPLib imports.
Must run before any test that imports from XRPLib.
"""
import sys
import os
import types

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MOCKS_DIR = os.path.join(os.path.dirname(__file__), "..", "mocks")

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, MOCKS_DIR)

# Install mock modules before any XRPLib code tries to import them
from tests.mocks import machine as mock_machine
from tests.mocks import rp2 as mock_rp2
from tests.mocks import neopixel as mock_neopixel

sys.modules["machine"] = mock_machine
sys.modules["rp2"] = mock_rp2
sys.modules["neopixel"] = mock_neopixel

# Mock uctypes for IMU
uctypes_mock = types.ModuleType("uctypes")
uctypes_mock.UINT8 = 0
uctypes_mock.BFUINT8 = 0
uctypes_mock.BF_POS = 8
uctypes_mock.BF_LEN = 16


def _mock_struct(addr, layout):
    """Return an object whose fields are readable/writable attributes."""
    obj = types.SimpleNamespace()
    for name in layout:
        setattr(obj, name, 0)
    return obj


def _mock_addressof(buf):
    return id(buf)


uctypes_mock.struct = _mock_struct
uctypes_mock.addressof = _mock_addressof
sys.modules["uctypes"] = uctypes_mock

# Mock gc.threshold (MicroPython-specific, not in CPython)
import gc
if not hasattr(gc, 'threshold'):
    gc.threshold = lambda *args: None

# Add MicroPython-specific time functions to the standard time module
import time
if not hasattr(time, 'ticks_ms'):
    time.ticks_ms = lambda: int(time.time() * 1000) & 0x3FFFFFFF
if not hasattr(time, 'ticks_us'):
    time.ticks_us = lambda: int(time.time() * 1_000_000) & 0x3FFFFFFF
if not hasattr(time, 'ticks_diff'):
    def _ticks_diff(end, start):
        # Simplified ticks_diff for testing (no wraparound in short tests)
        return end - start
    time.ticks_diff = _ticks_diff
if not hasattr(time, 'sleep_us'):
    time.sleep_us = lambda us: time.sleep(us / 1_000_000)

# Mock micropython module
micropython_mock = types.ModuleType("micropython")
micropython_mock.const = lambda x: x
sys.modules["micropython"] = micropython_mock

# Mock phew and its submodules (for webserver)
phew_mock = types.ModuleType("phew")
phew_server = types.ModuleType("phew.server")
phew_template = types.ModuleType("phew.template")
phew_logging = types.ModuleType("phew.logging")
phew_access_point = types.ModuleType("phew.access_point")
phew_dns = types.ModuleType("phew.dns")

phew_logging.LOG_INFO = 1
phew_logging.log_file = ""
phew_logging.debug = lambda *a: None
phew_logging.info = lambda *a: None
phew_logging.warn = lambda *a: None
phew_logging.warning = lambda *a: None
phew_logging.error = lambda *a: None
phew_logging.disable_logging_types = lambda *a: None
phew_logging.enable_logging_types = lambda *a: None

phew_server.run = lambda: None
phew_server.stop = lambda: None
phew_server.close = lambda: None
phew_server.redirect = lambda url: f"redirect:{url}"

_routes = {}


def _route(path, methods=None):
    def decorator(func):
        _routes[path] = func
        return func
    return decorator


def _catchall():
    def decorator(func):
        return func
    return decorator


phew_server.route = _route
phew_server.catchall = _catchall

phew_template.render_template = lambda *a: ""

phew_mock.server = phew_server
phew_mock.template = phew_template
phew_mock.logging = phew_logging
phew_mock.dns = phew_dns
phew_mock.access_point = lambda ssid, pw=None: types.SimpleNamespace(
    ifconfig=lambda: ("192.168.4.1", "", "", ""),
    active=lambda v=None: True,
    isconnected=lambda: True,
    disconnect=lambda: None,
)

phew_dns.run_catchall = lambda ip: None

sys.modules["phew"] = phew_mock
sys.modules["phew.server"] = phew_server
sys.modules["phew.template"] = phew_template
sys.modules["phew.logging"] = phew_logging
sys.modules["phew.access_point"] = phew_access_point
sys.modules["phew.dns"] = phew_dns

# Mock network module
network_mock = types.ModuleType("network")
network_mock.STA_IF = 0
network_mock.AP_IF = 1


class _MockWLAN:
    def __init__(self, mode=0):
        self._active = False

    def active(self, v=None):
        if v is not None:
            self._active = v
        return self._active

    def connect(self, ssid, pw):
        pass

    def isconnected(self):
        return True

    def ifconfig(self):
        return ("192.168.4.1", "", "", "")

    def disconnect(self):
        pass


network_mock.WLAN = _MockWLAN
sys.modules["network"] = network_mock

# Mock BLE for gamepad
ble_mock = types.ModuleType("ble")
blerepl_mock = types.ModuleType("ble.blerepl")


class _MockUart:
    def set_data_callback(self, cb):
        self._callback = cb


blerepl_mock.uart = _MockUart()
ble_mock.blerepl = blerepl_mock
sys.modules["ble"] = ble_mock
sys.modules["ble.blerepl"] = blerepl_mock

# Patch sys.implementation._machine for board detection
if not hasattr(sys.implementation, "_machine"):
    sys.implementation._machine = "Raspberry Pi Pico W with RP2350"

# Suppress the XRPLib __init__.py version check
xrplib_init = types.ModuleType("XRPLib")
xrplib_init.__path__ = [os.path.join(PROJECT_ROOT, "XRPLib")]
sys.modules["XRPLib"] = xrplib_init
