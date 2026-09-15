"""
Test stand support module for automated hardware testing.

When running on a test stand, tests skip manual intervention steps
(button presses, visual checks) and instead use automated sensors.

Test stand mode is activated by placing a file called 'teststand_mode'
on the Pico's filesystem root:
    mpremote fs touch :teststand_mode

Sensor pin assignments (using spare Motor 3/4 and Servo 3/4 ports):
    - LED phototransistor:  MOTOR_3_ENCODER_A (ADC)
    - Servo break-beam:     MOTOR_3_ENCODER_B (digital in)
    - Reflectance slide:    SERVO_4 (PWM servo)
    - Button test GPIO:     SERVO_3 (optional, digital out)
    - RGB color sensor:     I2C bus (shared with IMU, addr 0x29)
"""
import os
import time


def is_teststand():
    """Check if running on an automated test stand."""
    try:
        os.stat("/teststand_mode")
        return True
    except OSError:
        return False


def wait_if_manual(board):
    """In manual mode, wait for button press. In teststand mode, continue immediately."""
    if not is_teststand():
        board.wait_for_button()


# ---------------------------------------------------------------------------
# Test stand sensor helpers (Phase 2-4: only usable with instrumentation wired)
# ---------------------------------------------------------------------------

def read_led_sensor(pin_name="MOTOR_3_ENCODER_A"):
    """Read phototransistor aimed at the onboard LED. Returns ADC value 0-65535."""
    from machine import Pin, ADC
    return ADC(Pin(pin_name)).read_u16()


def read_servo_beam(pin_name="MOTOR_3_ENCODER_B"):
    """Read break-beam sensor at servo arm. Returns 0 if beam blocked, 1 if clear."""
    from machine import Pin
    return Pin(pin_name, Pin.IN, Pin.PULL_UP).value()


def move_reflectance_slide(position, pin_name="SERVO_4"):
    """
    Move the reflectance test surface slide to a position.
    :param position: 'white' or 'black'
    :param pin_name: Servo pin controlling the slide actuator
    """
    from machine import Pin, PWM
    servo = PWM(Pin(pin_name, Pin.OUT))
    servo.freq(50)
    if position == "white":
        servo.duty_ns(500000)   # 0 degrees — white half under sensors
    elif position == "black":
        servo.duty_ns(2500000)  # 200 degrees — black half under sensors
    time.sleep(0.5)  # allow slide to settle


def simulate_button_press(pin_name="SERVO_3", duration_ms=100):
    """
    Optional: toggle the button pin for testing is_button_pressed().
    Requires SERVO_3 wired to BOARD_USER_BUTTON via 1kΩ resistor.
    """
    from machine import Pin
    pin = Pin(pin_name, Pin.OUT)
    pin.value(0)   # active low — simulate press
    time.sleep_ms(duration_ms)
    pin.value(1)   # release
    pin = Pin(pin_name, Pin.IN)  # tri-state to avoid holding the line
