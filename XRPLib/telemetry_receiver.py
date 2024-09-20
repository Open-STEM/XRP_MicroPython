class TelemetryReceiver:
    """
    Class to parse and decode telemetry data received as serial input one character at a time.
    """

    def __init__(self):
        """
        Initialize the TelemetryReceiver.
        """
        self.buffer = ""
        self.in_packet = False
        self.metadata = {}  # Maps channel index to channel name
        self.data = {}      # Stores data by channel index

    def receive_char(self, char):
        """
        Receive a character from serial input and process it.
        
        :param char: A character received from the serial input
        :type char: str
        """
        if char == chr(28):  # Start of packet
            self.in_packet = True
            self.buffer = ""
        elif char == chr(29):  # End of packet
            if self.in_packet:
                self._process_packet(self.buffer)
                self.in_packet = False
        else:
            if self.in_packet:
                self.buffer += char

    def _process_packet(self, packet):
        """
        Process the decoded packet and handle it as metadata or data.

        :param packet: The packet string (decoded from the buffer)
        :type packet: str
        """
        packet_bytes = bytearray(packet.encode('ascii'))
        qualifier = packet_bytes[0]

        if qualifier == 127:  # Metadata packet
            channel_index = packet_bytes[1]
            channel_name = packet_bytes[2:].decode('ascii').rstrip('\x00')
            self.metadata[channel_index] = channel_name
            print(f"Metadata received - Channel Index: {channel_index}, Channel Name: {channel_name}")
        else:  # Data packet
            channel_index = packet_bytes[0]
            float_bytes = packet_bytes[1:9]  # Next 8 bytes are the float
            decoded_data = ascii_to_float(float_bytes)
            channel_name = self.metadata.get(channel_index, f"Unknown channel {channel_index}")
            self.data[channel_name] = decoded_data
            print(f"Data received - Channel: {channel_name}, Data: {decoded_data}")

def ascii_to_float(byte_array):
    # Reverse the encoding process
    normalized_f = sum((b & 0x7F) << (i * 7) for i, b in enumerate(byte_array))
    
    # Step 4: Map back to float range [-1e9, 1e9]
    f = ((normalized_f / (2**48 - 1)) * 2e9) - 1e9
    return f

