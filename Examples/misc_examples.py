from XRPLib.defaults import *
from .drive_examples import test_drive
import time

"""
    By the end of this file students will learn how to use the on-board buttons and LEDS,
    as well as control a servo that may be connected.
"""

def test_leds():
    board.led_blink(3)
    time.sleep(1)
    board.led_off()

# Test moving to both extremes of the servo motion and some middle value
def test_servo():
    servo_one.set_angle(135)
    time.sleep(2)
    servo_one.set_angle(0)
    time.sleep(2)
    servo_one.set_angle(60)
    time.sleep(2)

# Installation Verification Program
def ivp():
    while not board.is_button_pressed():
        print(f"Left Reflectance: {reflectance.get_left()}, Right Reflectance: {reflectance.get_right()}")
        time.sleep(0.1)
    while board.is_button_pressed():
        time.sleep(.01)
    while not board.is_button_pressed():
        print(f"Ultrasonic Distance: {rangefinder.distance()}")
        time.sleep(0.1)
    while board.is_button_pressed():
        time.sleep(.01)
    print("Testing Servo")
    test_servo()
    print("Testing LEDs")
    board.wait_for_button()
    test_leds()
    print("Testing Drivetrain:")
    board.wait_for_button()
    test_drive()