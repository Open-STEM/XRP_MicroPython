from XRPLib.encoded_motor import EncodedMotor

# using the EncodedMotor since the default drivetrain uses the IMU and takes 3 seconds to init
left = EncodedMotor.get_default_left_motor()
right = EncodedMotor.get_default_right_motor()
left.set_effort(0.0)
right.set_effort(0.0)
