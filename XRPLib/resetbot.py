from XRPLib.encoded_motor import EncodedMotor

"""
A simple file for shutting off all of the motors after a program gets interrupted from the REPL.
Run this file after interrupting a program to stop the robot by running "import XRPLib.resetbot" in the REPL.
"""

# using the EncodedMotor since the default drivetrain uses the IMU and takes 3 seconds to init
for i in range(4):
    motor = EncodedMotor.get_default_encoded_motor(i)
    motor.set_effort(0)
    motor.reset_encoder_position()
