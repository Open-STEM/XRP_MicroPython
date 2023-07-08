from XRPLib.encoded_motor import EncodedMotor

# using the EncodedMotor since the default drivetrain uses the IMU and takes 3 seconds to init
for i in range(4):
    EncodedMotor.get_default_encoded_motor(i).reset_encoder_position()
