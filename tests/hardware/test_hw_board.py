"""
Hardware integration test for board peripherals (LED, button, power).
Visual verification required for LEDs.
"""
from XRPLib.board import Board
import time

board = Board.get_default_board()

passed = 0
failed = 0


def check(name, condition):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name}")
        failed += 1


def test_led_on_off():
    """LED should turn on and off."""
    print("  LED should turn ON...")
    board.led_on()
    time.sleep(1)
    print("  LED should turn OFF...")
    board.led_off()
    time.sleep(0.5)
    check("LED on/off (visual check)", True)


def test_led_blink():
    """LED should blink at 5Hz."""
    print("  LED should blink at 5Hz for 3 seconds...")
    board.led_blink(5)
    time.sleep(3)
    board.led_off()
    check("LED blink (visual check)", True)


def test_button():
    """Button press detection."""
    print("  Press the user button NOW...")
    start = time.ticks_ms()
    pressed = False
    while time.ticks_diff(time.ticks_ms(), start) < 5000:
        if board.is_button_pressed():
            pressed = True
            break
        time.sleep(0.01)
    check("Button press detected", pressed)

    if pressed:
        print("  Release the button...")
        while board.is_button_pressed():
            time.sleep(0.01)
        check("Button release detected", not board.is_button_pressed())


def test_power_detect():
    """Power detection should return True when batteries connected."""
    powered = board.are_motors_powered()
    check(f"Motors powered: {powered}", powered is True)


def test_rgb_led():
    """RGB LED should show colors (newer boards only)."""
    try:
        print("  RGB LED: Red...")
        board.set_rgb_led(255, 0, 0)
        time.sleep(1)
        print("  RGB LED: Green...")
        board.set_rgb_led(0, 255, 0)
        time.sleep(1)
        print("  RGB LED: Blue...")
        board.set_rgb_led(0, 0, 255)
        time.sleep(1)
        board.set_rgb_led(0, 0, 0)
        check("RGB LED colors (visual check)", True)
    except NotImplementedError:
        print("  SKIP: RGB LED not available on this board")


print("=" * 40)
print("BOARD HARDWARE TESTS")
print("=" * 40)

test_led_on_off()
test_led_blink()
test_button()
test_power_detect()
test_rgb_led()

print()
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
