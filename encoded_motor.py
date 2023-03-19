from motor import Motor
from encoder import Encoder

class EncodedMotor(Motor):
    def __init__(self, direction_pin: int, speed_pin: int, enc_pin_a:int, enc_pin_b:int, ticks_per_revolution:int = 544, flip_dir:bool=False):
        super().__init__(direction_pin, speed_pin, flip_dir)
        self._encoder = Encoder(enc_pin_a,enc_pin_b,ticks_per_revolution)

    def get_position(self):
        if self.flip_dir:
            invert = -1
        else:
            invert = 1
        return self._encoder.get_position()*invert

    def reset_encoder_position(self):
        self._encoder.reset_encoder_position()
