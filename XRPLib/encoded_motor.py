from motor import Motor
from encoder import Encoder
from machine import Timer

class EncodedMotor(Motor):
    def __init__(self, direction_pin: int, speed_pin: int, enc_pin_a:int, enc_pin_b:int, ticks_per_revolution:int = 544, flip_dir:bool=False, kp:float = 5, ki:float = 0.25):
        super().__init__(direction_pin, speed_pin, flip_dir)
        self._encoder = Encoder(enc_pin_a,enc_pin_b,ticks_per_revolution)
        self.kp = kp
        self.ki = ki
        self.target_speed = None
        self.speed = 0
        self.prev_position = 0;
        self.errorSum = 0;
        # Use a virtual timer so we can leave the hardware timers up for the user
        self.updateTimer = Timer(-1)

    def get_position(self):
        if self.flip_dir:
            invert = -1
        else:
            invert = 1
        return self._encoder.get_position()*invert

    def reset_encoder_position(self):
        self._encoder.reset_encoder_position()

    def get_speed(self):
        return self.speed*3000

    def set_target_speed(self, target_speed_rpm:float = None):
        """
        Sets target speed (in rpm) to be maintained passively using PI Control
        """
        if target_speed_rpm is None:
            self.target_speed = None
            self.set_effort(0)
            return
        # If the update timer is not running, start it at 100 Hz (20ms updates)
        self.updateTimer.init(period=20, callback=lambda t:self.update())
        # Convert from rev per min to rev per 10ms
        self.target_speed = target_speed_rpm/(60*50)

    def set_PI_constants(self, new_kp:float, new_ki:float):
        self.kp = new_kp
        self.ki = new_ki
        self.errorSum = 0

    def update(self):

        current_position = self.get_position()
        self.speed = current_position - self.prev_position
        if self.target_speed is not None:
            error = self.target_speed - self.speed
            self.errorSum += error
            self.set_effort(self.kp * error + self.ki * self.errorSum)
        else:
            self.errorSum = 0
            self.updateTimer.deinit()

        self.prev_position = current_position

