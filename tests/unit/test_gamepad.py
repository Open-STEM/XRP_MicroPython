"""
Unit tests for Gamepad data parsing.
"""
import pytest
from XRPLib.gamepad import Gamepad


class TestGamepadParsing:
    def setup_method(self):
        self.gp = Gamepad()
        # Reset shared class data
        for i in range(len(self.gp._joyData)):
            self.gp._joyData[i] = 0.0

    def test_valid_packet_joystick(self):
        # Packet: header=0x55, length=2, index=0 (X1), value=255 (full right)
        data = bytearray([0x55, 2, 0, 255])
        self.gp._data_callback(data)
        # value = round(255/127.5 - 1, 2) = round(1.0, 2) = 1.0
        assert self.gp._joyData[0] == pytest.approx(1.0)

    def test_valid_packet_center(self):
        # value = 127 -> round(127/127.5 - 1, 2) = round(-0.004, 2) = 0.0
        data = bytearray([0x55, 2, 0, 127])
        self.gp._data_callback(data)
        assert abs(self.gp._joyData[0]) < 0.01

    def test_valid_packet_minimum(self):
        # value = 0 -> round(0/127.5 - 1, 2) = -1.0
        data = bytearray([0x55, 2, 0, 0])
        self.gp._data_callback(data)
        assert self.gp._joyData[0] == pytest.approx(-1.0)

    def test_multiple_axes_in_one_packet(self):
        # length=4: two axis pairs
        data = bytearray([0x55, 4, 0, 255, 1, 0])
        self.gp._data_callback(data)
        assert self.gp._joyData[0] == pytest.approx(1.0)
        assert self.gp._joyData[1] == pytest.approx(-1.0)

    def test_button_press(self):
        # Button A (index 4), value 255 (pressed)
        data = bytearray([0x55, 2, 4, 255])
        self.gp._data_callback(data)
        assert self.gp._joyData[4] == pytest.approx(1.0)

    def test_invalid_header_ignored(self):
        data = bytearray([0xAA, 2, 0, 255])
        self.gp._data_callback(data)
        assert self.gp._joyData[0] == 0.0

    def test_wrong_length_ignored(self):
        # Header says length=4, but only 4 bytes total (should be 6)
        data = bytearray([0x55, 4, 0, 255])
        self.gp._data_callback(data)
        assert self.gp._joyData[0] == 0.0


class TestGamepadAPI:
    def setup_method(self):
        self.gp = Gamepad()
        for i in range(len(self.gp._joyData)):
            self.gp._joyData[i] = 0.0

    def test_get_value_negated(self):
        """get_value returns negated value for user convention."""
        self.gp._joyData[0] = 1.0
        assert self.gp.get_value(0) == -1.0

    def test_is_button_pressed_true(self):
        self.gp._joyData[Gamepad.BUTTON_A] = 1.0
        assert self.gp.is_button_pressed(Gamepad.BUTTON_A) is True

    def test_is_button_pressed_false(self):
        self.gp._joyData[Gamepad.BUTTON_A] = 0.0
        assert self.gp.is_button_pressed(Gamepad.BUTTON_A) is False

    def test_is_button_pressed_negative(self):
        self.gp._joyData[Gamepad.BUTTON_B] = -0.5
        assert self.gp.is_button_pressed(Gamepad.BUTTON_B) is False
