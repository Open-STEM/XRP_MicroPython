import time, struct


class TelemetrySender:
    """
    Abstract class for sending telemetry data to a telemetry receiver. Must implement the send_telemetry method.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """
        Reset telemetry run. All metadata for telemetry channels is reset.
        """
        self.start_time = time.ticks_ms()

    def get_current_time(self):
        """
        Get the current time in milliseconds since last reset.
        
        :return: The current time in milliseconds
        :rtype: int
        """
        return time.ticks_diff(time.ticks_ms(), self.start_time)
    
    def send_telemetry(self, channel, data):
        """
        Send numeric telemetry data for a channel with the given name.
        
        :param channel: The name of the channel to send data for
        :type channel: str
        :param data: The numeric data to send
        :type data: float
        """
        raise NotImplementedError("send_telemetry method must be implemented by subclass")
    
    def on_stop_telemetry(self):
        """
        Called when telemetry is stopped. Can be used to clean up resources.
        """
        pass


class StdoutTelemetrySender(TelemetrySender):
    """
    Sends telemetry data directly to stdout without any additional processing or buffering.
    """

    def send_telemetry(self, channel, data):
        """
        Send telemetry data to stdout.
        
        :param channel: The name of the channel to send data for
        :type channel: str
        :param data: The numeric data to send
        :type data: float
        """
        current_time = self.get_current_time()
        print(f"[{current_time}] Telemetry channel {channel} at: {data}")


class EncodedTelemetrySender(TelemetrySender):
    """
    Sends telemetry data compacted into encoded ASCII and delimited with char(28) start and char(29) end characters.
    Consumers like XRPCode can extract and decode this data.

    Up to 127 channels are supported. When the first data point for a new channel is about to be sent, first send
    a metadata packet with the channel index and name. This is used to map the channel index to a name on the receiver.

    Data is encoded with [1 byte qualifier] [data].

    Qualifier == 127 means this is a metadata packet. The data is a byte to indicate the channel index, then the channel name
    encoded as ASCII ending with null char(0).

    Qualifier < 127 means this is a data packet. The data is first a byte to indicate the channel index, then a 4-byte-encoded
    float value.

    Data is buffered for a specified maximum number of bytes before sending batched data to the output.
    """

    def __init__(self, max_buffer_size=256):
        """
        Create a new EncodedTelemetrySender with the specified maximum buffer size.
        
        :param max_buffer_size: The maximum number of bytes to buffer before sending data
        :type max_buffer_size: int
        """
        super().__init__()
        self.max_buffer_size = max_buffer_size
        self.buffer = bytearray()

        # An array of channel names, indexed by channel index. Maximum 255 channels, so max index is 254.
        self.registered_channels = []

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

        channel_index = self._get_or_register_channel(channel)
        
        # Prepare metadata packet if this is a new channel
        if channel_index == len(self.registered_channels) - 1:
            metadata_packet = self._create_metadata_packet(channel_index, channel)
            self._add_to_buffer(metadata_packet)

        # Prepare data packet
        data_packet = self._create_data_packet(channel_index, float_data)
        self._add_to_buffer(data_packet)

    def on_stop_telemetry(self):
        """
        Send the remaining buffer to the output.
        """
        self._send_buffer()

    def _get_or_register_channel(self, channel):
        """
        Get the index of an existing channel or register a new one.

        :param channel: The name of the channel
        :type channel: str
        :return: The index of the channel
        :rtype: int
        :raises ValueError: If the maximum number of channels (255) is reached
        """
        if channel in self.registered_channels:
            return self.registered_channels.index(channel)
        if len(self.registered_channels) >= 255:
            print("Maximum number of channels (255) reached")
            raise ValueError("Maximum number of channels (255) reached")
        self.registered_channels.append(channel)
        return len(self.registered_channels) - 1

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
        packet = bytearray([127, channel_index])
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
        packet.extend(float_to_ascii(data))
        return packet

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
        
            encoded_data = chr(28) + self.buffer.decode('ascii') + chr(29)

            print(encoded_data)  # Send to serial and clear buffer
            self.buffer = bytearray()

def float_to_ascii(f):
    # Step 1: Normalize the float (Assume f is between -1e9 and 1e9, adjust as needed)
    normalized_f = int(((f + 1e9) / 2e9) * (2**48 - 1))  # Maps f to [0, 2^48-1]
    
    # Step 2: Pack it into 8 bytes (big-endian)
    byte_array = bytearray((normalized_f >> (i * 7)) & 0x7F for i in range(8))
    
    return byte_array

def ascii_to_float(byte_array):
    # Reverse the encoding process
    normalized_f = sum((b & 0x7F) << (i * 7) for i, b in enumerate(byte_array))
    
    # Step 4: Map back to float range [-1e9, 1e9]
    f = ((normalized_f / (2**48 - 1)) * 2e9) - 1e9
    return f