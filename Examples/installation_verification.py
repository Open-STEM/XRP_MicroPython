from XRPLib.defaults import *
from .drive_examples import *
from .misc_examples import *
import time

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
    wait_for_button()
    test_leds()
    print("Testing Drivetrain:")
    wait_for_button()
    test_drive()

ivp()