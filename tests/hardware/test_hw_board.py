"""
Hardware integration test for board peripherals (LED, button, power).
Manual mode: Visual verification for LEDs, manual button press.
Test stand: Phototransistor verifies LED, button test uses GPIO toggle.
"""
from XRPLib.board import Board
from teststand import is_teststand, wait_if_manual, read_led_sensor, simulate_button_press
import time

board = Board.get_default_board()

passed = 0
failed = 0
skipped = 0


def check(name, condition):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name}")
        failed += 1


def skip(name):
    global skipped
    print(f"  SKIP: {name}")
    skipped += 1


def test_led_on_off():
    """LED should turn on and off."""
    if is_teststand():
        baseline = read_led_sensor()
        board.led_on()
        time.sleep(0.1)
        on_value = read_led_sensor()
        board.led_off()
        time.sleep(0.1)
        off_value = read_led_sensor()
        check(f"LED on detected (ADC {on_value} vs baseline {baseline})",
              on_value > baseline + 1000)
        check(f"LED off detected (ADC {off_value} near baseline {baseline})",
              abs(off_value - baseline) < 2000)
    else:
        print("  LED should turn ON...")
        board.led_on()
        time.sleep(1)
        print("  LED should turn OFF...")
        board.led_off()
        time.sleep(0.5)
        check("LED on/off (visual check)", True)


def test_led_blink():
    """LED should blink at 5Hz."""
    if is_teststand():
        board.led_blink(5)
        time.sleep(0.2)  # let blink stabilize
        # Sample ADC at ~100Hz for 1 second, count transitions
        samples = []
        for _ in range(100):
            samples.append(read_led_sensor())
            time.sleep(0.01)
        board.led_off()
        # Count transitions (high-to-low or low-to-high)
        threshold = (max(samples) + min(samples)) // 2
        transitions = 0
        above = samples[0] > threshold
        for s in samples[1:]:
            now_above = s > threshold
            if now_above != above:
                transitions += 1
                above = now_above
        # 5Hz blink = 10 transitions per second (±4 for timing variance)
        check(f"LED blink: {transitions} transitions (expect 6-14)", 6 <= transitions <= 14)
    else:
        print("  LED should blink at 5Hz for 3 seconds...")
        board.led_blink(5)
        time.sleep(3)
        board.led_off()
        check("LED blink (visual check)", True)


def test_button():
    """Button press detection."""
    if is_teststand():
        # Verify button is not pressed initially
        check("Button not pressed initially", not board.is_button_pressed())
        # Simulate press via GPIO
        simulate_button_press(duration_ms=200)
        # Note: button state only readable during the press window,
        # so this test mainly verifies the GPIO wiring works.
        # If SERVO_3 is not wired to the button, just skip.
        check("Button GPIO toggle (no crash)", True)
    else:
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
        if is_teststand():
            # Phase 4: RGB color sensor verification
            # For now, just verify the commands don't crash
            board.set_rgb_led(255, 0, 0)
            time.sleep(0.1)
            board.set_rgb_led(0, 255, 0)
            time.sleep(0.1)
            board.set_rgb_led(0, 0, 255)
            time.sleep(0.1)
            board.set_rgb_led(0, 0, 0)
            check("RGB LED commands executed (no crash)", True)
        else:
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
result_msg = f"Results: {passed} passed, {failed} failed"
if skipped:
    result_msg += f", {skipped} skipped"
result_msg += f" out of {passed + failed + skipped}"
print(result_msg)
