from .differential_drive import DifferentialDrive
from .rangefinder import Rangefinder
from .imu import IMU
from .reflectance import Reflectance
from .servo import Servo

from machine import Timer
import time, os

# Dictionary mapping channel names to (rate, callback) tuples
DEFAULT_TELEMETRY_CHANNELS = {}

class Telemetry:

    _DEFAULT_TELEMETRY_INSTANCE = None

    @classmethod
    def get_default_telemetry(cls):
        """
        Get the default telemetry instance. This is a singleton, so only one instance of the board will ever exist.
        """
        if cls._DEFAULT_TELEMETRY_INSTANCE is None:
            cls._DEFAULT_TELEMETRY_INSTANCE = cls(
                drive = DifferentialDrive.get_default_differential_drive(),
                imu=IMU.get_default_imu(),
                rangefinder=Rangefinder.get_default_rangefinder(),
                reflectance=Reflectance.get_default_reflectance(),
                servo_one=Servo.get_default_servo(index=1),
                servo_two=Servo.get_default_servo(index=2),
            )
        return cls._DEFAULT_TELEMETRY_INSTANCE

    def __init__(self,
        drive = None,
        imu = None,
        rangefinder = None,
        reflectance = None,
        servo_one = None,
        servo_two = None,
    ):
        # Store start time to calculate elapsed time for each telemetry packet
        self.start_time = time.ticks_ms()

        # Telemetry timers for each telemetry rate, mapping rate (in Hz) to Timer object
        self.telemetry_timers = {}

        # Dictionary of telemetry channel rates to a dictionary of channel names to callback functions
        self.telemetry_channels = {}

        self.init_telemetry_channels(drive, imu, rangefinder, reflectance, servo_one, servo_two)

        
    def init_telemetry_channels(self, drive, imu, rangefinder, reflectance, servo_one, servo_two):
        """
        Initialize the telemetry channels by registering the required channels with their
        respective callback functions.
        """
        
        # Read the telemetry file to get a dictionary of required channels and rates
        required_telemetry = self.read_telemetry_file()
        
        # For each channel, check if the channel is required and the channel object exists, and if so,
        # register the channel with the appropriate callback function
        def register(obj, channel_name, callback):
            if obj is not None and channel_name in required_telemetry:
                self.register_telemetry_channel(
                    channel_name,
                    required_telemetry[channel_name],
                    lambda: callback(obj)
                )
                required_telemetry.pop(channel_name)

        # Register all required telemetry channels, consuming the required_telemetry dictionary
        register(drive, "left_distance", lambda drive: drive.get_left_encoder_position())
        register(drive, "right_distance", lambda drive: drive.get_right_encoder_position())
        register(imu, "imu_heading", lambda imu: imu.get_heading())
        register(imu, "imu_pitch", lambda imu: imu.get_pitch())
        register(imu, "imu_roll", lambda imu: imu.get_roll())
        register(imu, "imu_yaw", lambda imu: imu.get_yaw())

        # If there are remaining required telemetry channels, they are unknown
        if len(required_telemetry) > 0:
            print(f"WARNING: telemetry channel(s) not found: {list(required_telemetry.keys())}")


    def read_telemetry_file(self, file_path = "telemetry.txt"):
        """
        Read the telemetry file and return the contents as dictionary of channel names to rates.
        Each line in the file should contain a channel name and rate separated by whitespace, or a
        comment starting with a #.
        
        :param file_path: The path to the telemetry file
        :type file_path: str
        :return: A dictionary of channel names to rates
        :rtype: dict
        """
        telemetry_channels = {}
    
        try:
            with open(file_path, "r") as file:
                for line in file:
                    tokens = line.split()

                    if line.startswith("#") or len(tokens) < 2:
                        continue
                    channel_name, rate, *_ = tokens

                    telemetry_channels[channel_name] = float(rate)
        except OSError:
            # If the file doesn't exist, return an empty dictionary
            return {}

        return telemetry_channels


    def register_telemetry_channel(self, channel_name, rate, callback):
        """
        Register a telemetry channel with a callback function. Group channels by rate so that they
        can be shared by a single timer.
        
        :param channel_name: The name of the telemetry channel
        :type channel_name: str
        :param rate: The rate at which to send telemetry data for this channel, in Hz
        :type rate: float
        :param callback: The callback function to call to get the telemetry data for this channel
        :type callback: function
        """
        if rate not in self.telemetry_channels:
            self.telemetry_timers[rate] = Timer(-1)
            self.telemetry_channels[rate] = {}

        self.telemetry_channels[rate][channel_name] = callback


    def start_telemetry(self):
        """
        For each telemetry rate, start a timer that will poll the telemetry channels at that rate.
        """
        for rate, channels in self.telemetry_channels.items():
            # channels is a dictionary mapping channel names to callback functions
            print(f"Initializing telemetry flow at {rate} Hz for channels {list(channels.keys())}")
            self.telemetry_timers[rate].init(
                freq = rate,
                callback = lambda t, channels=channels: self.poll_telemetry_for_channels(channels)
            )

    def poll_telemetry_for_channels(self, channels):
        """
        Poll the telemetry channels for the given dictionary of channels.
        
        :param channels: A dictionary mapping channel names to callback functions
        :type channels: dict
        """
        current_time = time.ticks_ms()
        delta_time = time.ticks_diff(current_time, self.start_time)

        for channel_name, callback in channels.items():
            data = callback()
            print(f"[{delta_time}] Telemetry channel {channel_name} at: {data}")

    def stop_telemetry(self):
        """
        Stop all telemetry timers.
        """
        print("Stopping telemetry")
        for timer in self.telemetry_timers.values():
            timer.deinit()