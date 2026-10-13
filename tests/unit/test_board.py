"""
Unit tests for Board class logic.
"""
import pytest
from XRPLib.board import Board


class TestBoardPowerDetection:
    def test_motors_powered_high_adc(self):
        b = Board()
        b.on_switch._set_value(30000)
        assert b.are_motors_powered() is True

    def test_motors_not_powered_low_adc(self):
        b = Board()
        b.on_switch._set_value(10000)
        assert b.are_motors_powered() is False

    def test_motors_powered_boundary(self):
        b = Board()
        b.on_switch._set_value(20001)
        assert b.are_motors_powered() is True

    def test_motors_not_powered_at_boundary(self):
        b = Board()
        b.on_switch._set_value(20000)
        assert b.are_motors_powered() is False


class TestBoardButton:
    def test_button_not_pressed(self):
        b = Board()
        b.button._value = 1  # Pull-up: high when not pressed
        assert b.is_button_pressed() is False

    def test_button_pressed(self):
        b = Board()
        b.button._value = 0  # Active low
        assert b.is_button_pressed() is True


class TestBoardLED:
    def test_led_on(self):
        b = Board()
        b.led_on()
        assert b.led._value == 1
        assert b.is_led_blinking is False

    def test_led_off(self):
        b = Board()
        b.led_on()
        b.led_off()
        assert b.led._value == 0
        assert b.is_led_blinking is False

    def test_led_blink_starts(self):
        b = Board()
        b.led_blink(5)
        assert b.is_led_blinking is True
        assert b._virt_timer._freq == 10  # 5Hz * 2

    def test_led_blink_zero_stops(self):
        b = Board()
        b.led_blink(5)
        b.led_blink(0)
        assert b.is_led_blinking is False


class TestBoardRGBLED:
    def test_set_rgb_on_supported_board(self):
        b = Board()
        # Manually add rgb_led (simulating a board that supports it)
        from tests.mocks.neopixel import NeoPixel
        from tests.mocks.machine import Pin
        b.rgb_led = NeoPixel(Pin(), 1)
        b.set_rgb_led(255, 0, 128)
        assert b.rgb_led[0] == (255, 0, 128)

    def test_set_rgb_raises_on_beta(self):
        b = Board()
        # Remove rgb_led if it exists to simulate beta board
        if "rgb_led" in b.__dict__:
            del b.rgb_led
        with pytest.raises(NotImplementedError):
            b.set_rgb_led(255, 0, 0)
