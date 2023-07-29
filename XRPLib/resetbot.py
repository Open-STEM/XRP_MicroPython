from XRPLib.encoded_motor import EncodedMotor
from XRPLib.imu import IMU
from XRPLib.board import Board
from XRPLib.servo import Servo
"""
A simple file for shutting off all of the motors after a program gets interrupted from the REPL.
Run this file after interrupting a program to stop the robot by running "import XRPLib.resetbot" in the REPL.
"""

# using the EncodedMotor since the default drivetrain uses the IMU and takes 3 seconds to init
for i in range(4):
    motor = EncodedMotor.get_default_encoded_motor(i+1)
    motor.set_effort(0)
    motor.reset_encoder_position()

# Reset IMU registers
IMU.get_default_imu().reset()

# Turn off the on-board LED
Board.get_default_board().led_off()

# Turn off both Servos
Servo.get_default_servo().free()
Servo(17).free()