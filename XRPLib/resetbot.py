import sys
import time
"""
A simple file for shutting off all of the motors after a program gets interrupted from the REPL.
Run this file after interrupting a program to stop the robot by running "import XRPLib.resetbot" in the REPL.
"""
print("Stopping all motors and shutting down the robot...")

if "XRPLib.encoded_motor" in sys.modules:
    from XRPLib.encoded_motor import EncodedMotor
    # using the EncodedMotor since the default drivetrain uses the IMU and takes 3 seconds to init
    for i in range(4):
        motor = EncodedMotor.get_default_encoded_motor(i+1)
        motor.set_speed(0)
        motor.reset_encoder_position()

if "XRPLib.board" in sys.modules:
    from XRPLib.board import Board
    # Turn off the on-board LED
    Board.get_default_board().led_off()

if "XRPLib.servo" in sys.modules:
    from XRPLib.servo import Servo
    # Turn off both Servos
    Servo.get_default_servo(1).free()
    Servo.get_default_servo(2).free()

if "XRPLib.webserver" in sys.modules:
    from XRPLib.webserver import Webserver
    # Shut off the webserver and close network connections
    Webserver.get_default_webserver().stop_server()