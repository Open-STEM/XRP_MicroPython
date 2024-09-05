

from XRPLib.encoded_motor import EncodedMotor
import time
from XRPLib.differential_drive import DifferentialDrive

differentialDrive = DifferentialDrive.get_default_differential_drive()

def turn_test(angle, effort):
    for i in range(2):
        differentialDrive.turn(angle, effort)
        differentialDrive.turn(-angle, effort)
    differentialDrive.stop()


turn_test(30, 0.5)
turn_test(180, 0.5)
turn_test(30, 0.75)
turn_test(180, 0.75)
turn_test(30, 1)
turn_test(180, 1)
