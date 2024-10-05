from .telemetry_time import TelemetryTime
import time, struct


class TelemetrySender:
    """
    Abstract class for sending telemetry data to a telemetry receiver. Must implement the send_telemetry method.
    """

    def __init__(self, telemetry_time):
        """
        Create a new TelemetrySender with the specified function to get the current time in milliseconds.
        
        :param time_ms_function: A function that returns the current time in milliseconds
        :type time_ms_function: function
        """
        self.telemetry_time = telemetry_time

    def on_start_telemetry(self):
        """
        Called when telemetry is started. Can be used to initialize resources.
        """
        
        # Start time for telemetry run
        self.start_time = self.telemetry_time.time_ms()
    
    def on_stop_telemetry(self):
        """
        Called when telemetry is stopped. Can be used to clean up resources.
        """
        pass

    def get_current_time(self):
        """
        Get the current time in milliseconds since last reset.
        
        :return: The current time in milliseconds
        :rtype: int
        """
        return self.telemetry_time.time_diff(self.telemetry_time.time_ms(), self.start_time)
    
    def send_telemetry(self, channel, data):
        """
        Send numeric telemetry data for a channel with the given name.
        
        :param channel: The name of the channel to send data for
        :type channel: str
        :param data: The data to send
        :type data: float | int | string
        """
        raise NotImplementedError("send_telemetry method must be implemented by subclass")


class StdoutTelemetrySender(TelemetrySender):
    """
    Sends telemetry data directly to stdout without any additional processing or buffering.
    """

    def send_telemetry(self, channel, data):
        """
        Send telemetry data to stdout.
        
        :param channel: The name of the channel to send data for
        :type channel: str
        :param data: The data to send
        :type data: float | int | string
        """
        current_time = self.get_current_time()
        print(f"[{current_time}] Telemetry channel {channel} at: {data}")


class EncodedTelemetrySender(TelemetrySender):

    MAX_CHANNELS = 125

    """
    Sends telemetry data compacted into encoded ASCII and delimited with char(27) start and end characters.
    Consumers like XRPCode can extract and decode this data.

    Up to MAX_CHANNELS (125) channels are supported. When the first data point for a new channel is about to be sent, first send
    a metadata packet with the channel index and name. This is used to map the channel index to a name on the receiver.

    Data is encoded with [1 byte qualifier] [data].

    Qualifier == 127 is the start packet and means that this is a new telemetry run. There is no data.
    Data length is 0 bytes.

    Qualifier == 126 means this is a metadata packet. The data is a byte to indicate the channel index, then the channel name
    encoded as ASCII ending with null char(0).
    Data length has variable length.

    Qualifier == 125 means this is a stop packet. There is no data. This concludes the telemetry run.

    Qualifier <= 124 means this is a data packet. The data is first a byte to indicate the channel index, then a 4-byte-encoded
    timestamp in ms, then stringified data ending with null char(0).
    Data length has variable length.

    Data is buffered for a specified maximum number of bytes before sending batched data to the output.
    """

    def __init__(self, telemetry_time, max_buffer_size=256, send_function=print):
        """
        Create a new EncodedTelemetrySender with the specified maximum buffer size.
        
        :param max_buffer_size: The maximum number of bytes to buffer before sending data
        :type max_buffer_size: int
        """
        super().__init__(telemetry_time)
        self.max_buffer_size = max_buffer_size
        self.buffer = bytearray()
        self.send_function = send_function

        # An array of channel names, indexed by channel index. Maximum 255 channels, so max index is 254.
        self.registered_channels = []

        # Create start packet
        self._add_to_buffer(self.create_start_packet())

    def send_telemetry(self, channel, data):
        """
        Write metadata and/or data packets to the buffer. If the buffer would be exceeded, send the buffer by printing
        to serial, then clear buffer and write the new data packet to the buffer.

        :param channel: The name of the channel to send data for
        :type channel: str
        :param data: The numeric data to send. Assert this is numeric and cast to float, or raise ValueError
        :type data: int or float
        """
        try:
            float_data = float(data)
        except ValueError:
            print(f"Data must be numeric. Received: {data}")
            raise ValueError(f"Data must be numeric. Received: {data}")

        channel_index, is_newly_registered = self._get_or_register_channel(channel)
        
        # Prepare metadata packet if this is a new channel
        if is_newly_registered:
            metadata_packet = self._create_metadata_packet(channel_index, channel)
            self._add_to_buffer(metadata_packet)

        # Prepare data packet
        data_packet = self._create_data_packet(channel_index, float_data)
        print(f"Channel {channel} at {float_data} has packet {data_packet}")
        self._add_to_buffer(data_packet)

    def on_stop_telemetry(self):
        """
        Send the remaining buffer to the output.
        """

        # Create stop packet
        self._add_to_buffer(self.create_stop_packet())

        self._send_buffer()

    def _get_or_register_channel(self, channel):
        """
        Get the index of an existing channel or register a new one.

        :param channel: The name of the channel
        :type channel: str
        :return: The index of the channel, and whether it was newly registered
        :rtype: int, bool
        :raises ValueError: If the maximum number of channels (255) is reached
        """
        if channel in self.registered_channels:
            return self.registered_channels.index(channel), False
        if len(self.registered_channels) >= EncodedTelemetrySender.MAX_CHANNELS:
            print(f"Maximum number of channels ({EncodedTelemetrySender.MAX_CHANNELS}) reached")
            raise ValueError(f"Maximum number of channels ({EncodedTelemetrySender.MAX_CHANNELS}) reached")
        self.registered_channels.append(channel)
        return len(self.registered_channels) - 1, True

    def _create_metadata_packet(self, channel_index, channel_name):
        """
        Create a metadata packet for a new channel.

        :param channel_index: The index of the channel
        :type channel_index: int
        :param channel_name: The name of the channel
        :type channel_name: str
        :return: A bytearray containing the metadata packet
        :rtype: bytearray
        """
        packet = bytearray([126, channel_index])
        packet.extend(channel_name.encode('ascii'))
        packet.append(0)  # Null terminator
        return packet

    def _create_data_packet(self, channel_index, data):
        """
        Create a data packet for telemetry data.

        :param channel_index: The index of the channel
        :type channel_index: int
        :param data: The telemetry data
        :type data: float
        :return: A bytearray containing the data packet
        :rtype: bytearray
        """
        packet = bytearray([channel_index])
        packet.extend(uint_to_ascii(self.get_current_time()))
        packet.extend(str(data).encode('ascii'))   
        packet.append(0) # Null terminator
        return packet
    
    def create_start_packet(self):
        """
        Create a start packet to indicate the start of a new telemetry run. This is a single
        byte with the value 127.

        :return: A bytearray containing the start packet
        :rtype: bytearray
        """
        return bytearray([127])
    
    def create_stop_packet(self):
        """
        Create a stop packet to indicate the end of a telemetry run. This is a single
        byte with the value 125.

        :return: A bytearray containing the stop packet
        :rtype: bytearray
        """
        return bytearray([125])

    def _add_to_buffer(self, packet):
        """
        Add a packet to the buffer, sending the buffer if it would exceed the maximum size.

        :param packet: The packet to add to the buffer
        :type packet: bytearray
        """
        if len(self.buffer) + len(packet) > self.max_buffer_size:
            self._send_buffer()
        self.buffer.extend(packet)

    def _send_buffer(self):
        """
        Send the contents of the buffer to serial output and clear the buffer.
        """
        if self.buffer:

            # Get the size of the buffer as a 4-byte ASCII string
            buffer_size = uint_to_ascii(len(self.buffer))
        
            # Encode as start delimeter chr(27), size of buffer, then buffer
            send_buffer = bytearray([27])
            send_buffer.extend(buffer_size)
            send_buffer.extend(self.buffer)

            # Send the data over serial
            encoded_data = send_buffer.decode('ascii')
            self.send_function(encoded_data)

            # Clear the buffer
            self.buffer = bytearray()

# Encodes unsigned int to 4-char ASCII string
def uint_to_ascii(i):
    return struct.pack(">I", i)

# Decodes 4-char ASCII string to unsigned int
def ascii_to_uint(byte_array):
    return struct.unpack(">I", byte_array)[0]