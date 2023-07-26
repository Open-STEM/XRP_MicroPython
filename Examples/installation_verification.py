from XRPLib.defaults import *
import time

# Installation Verification Program
def ivp():
    # Print welcome message
    print("------------------------------------------")
    print("Running Installation Verification Program!")
    print("------------------------------------------")
    print()
    print("Welcome to the XRP! This example code will help")
    print("you verify that everything is working on your robot.")
    print("After each test, press the user button to continue.")
    print()
    
    # Flash LED at 5Hz
    print("Flashing LED")
    board.led_blink(5)
    
    # Wait for user to press button
    print("Press user button to test reflectance sensor")
    board.wait_for_button()
    
    # Stop blinking LED
    board.led_off()
    
    # Print reflectance values until button is pressed
    while not board.is_button_pressed():
        print(f"Reflectance    Left: {reflectance.get_left():.3f}    Right: {reflectance.get_right():.3f}    Press user button to test range sensor")
        time.sleep(0.1)
    
    # Wait until button is released
    while board.is_button_pressed():
        time.sleep(0.1)
    
    # Print range values until button is pressed
    while not board.is_button_pressed():
        print(f"Range    Distance: {rangefinder.distance():.1f}    Press user button to test servo")
        time.sleep(0.1)
    
    # Wait until button is released
    while board.is_button_pressed():
        time.sleep(0.1)
    
    # Print warning and wait for button press
    print()
    print("The next test will move the servo, so keep your hands clear!")
    print("Also please make sure the power switch is turned on!")
    print("Press user button to test servo")
    board.wait_for_button()
    
    # Test servo
    print("Testing servo")
    time.sleep(1)
    servo_one.set_angle(90)
    time.sleep(1)
    servo_one.set_angle(0)
    time.sleep(1)
    servo_one.set_angle(180)
    
    # Print warning and wait for button press
    print()
    print("The next test will drive the motors, so place the robot on a flat surface!")
    print("Also please make sure the power switch is turned on!")
    print("Press user button to test drivetrain")
    board.wait_for_button()
    
    # Test drivetrain
    print("Testing drivetrain")
    time.sleep(1)
    drivetrain.straight(25, 0.8)
    time.sleep(1)
    drivetrain.turn(90,0.8)
    time.sleep(1)
    drivetrain.turn(90, -0.8)
    time.sleep(1)
    drivetrain.straight(-25,0.8)
    
    print()
    print("-----------------------------------")
    print("All tests complete! Happy roboting!")
    print("-----------------------------------")

ivp()