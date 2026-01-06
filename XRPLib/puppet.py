"""
XRP Puppet Protocol (XPP) - Core Protocol Implementation

A bidirectional protocol for communicating with the XRP robot remotely.
Uses a Network Tables-like architecture with variable ID mapping.
"""

import struct
import sys
import time
from machine import Timer
from micropython import const

# Message framing constants
MSG_START_1 = const(0xAA)
MSG_START_2 = const(0x55)
MSG_END_1 = const(0x55)
MSG_END_2 = const(0xAA)
MAX_PAYLOAD_SIZE = const(251)

# Message type constants
MSG_TYPE_VAR_DEF = const(1)
MSG_TYPE_VAR_UPDATE = const(2)
MSG_TYPE_VAR_SUBSCRIBE = const(3)
MSG_TYPE_VAR_UNSUBSCRIBE = const(4)
MSG_TYPE_PROGRAM_START = const(5)
MSG_TYPE_PROGRAM_END = const(6)
MSG_TYPE_HEARTBEAT = const(7)

# Variable type constants
VAR_TYPE_INT = const(1)
VAR_TYPE_FLOAT = const(2)
VAR_TYPE_BOOL = const(3)

# Permission constants
PERM_READ_ONLY = const(1)
PERM_WRITE_ONLY = const(2)
PERM_READ_WRITE = const(3)

# First custom variable ID
FIRST_CUSTOM_VAR_ID = const(38)

# Mapping of standard variable names to IDs (1-37)
_STANDARD_VAR_IDS = {
    # Gamepad variables (1-19)
    '$gamepad.x1': 1,
    '$gamepad.y1': 2,
    '$gamepad.x2': 3,
    '$gamepad.y2': 4,
    '$gamepad.button_a': 5,
    '$gamepad.button_b': 6,
    '$gamepad.button_x': 7,
    '$gamepad.button_y': 8,
    '$gamepad.bumper_l': 9,
    '$gamepad.bumper_r': 10,
    '$gamepad.trigger_l': 11,
    '$gamepad.trigger_r': 12,
    '$gamepad.back': 13,
    '$gamepad.start': 14,
    '$gamepad.dpad_up': 15,
    '$gamepad.dpad_dn': 16,
    '$gamepad.dpad_l': 17,
    '$gamepad.dpad_r': 18,
    '$gamepad.enabled': 19,
    # IMU variables (20-25)
    '$imu.yaw': 20,
    '$imu.roll': 21,
    '$imu.pitch': 22,
    '$imu.acc_x': 23,
    '$imu.acc_y': 24,
    '$imu.acc_z': 25,
    # Encoder variables (26-29)
    '$encoder.left': 26,
    '$encoder.right': 27,
    '$encoder.3': 28,
    '$encoder.4': 29,
    # Current sensor variables (30-33)
    '$current.left': 30,
    '$current.right': 31,
    '$current.3': 32,
    '$current.4': 33,
    # Other sensor variables (34-37)
    '$rangefinder.distance': 34,
    '$reflectance.left': 35,
    '$reflectance.right': 36,
    '$voltage': 37,
}


class Puppet:
    """
    Core XRP Puppet Protocol implementation.
    Manages bidirectional communication, variable registry, and message handling.
    """
    
    _DEFAULT_PUPPET_INSTANCE = None
    
    @classmethod
    def get_default_puppet(cls):
        """
        Get the default XPP instance. This is a singleton.
        """
        if cls._DEFAULT_PUPPET_INSTANCE is None:
            cls._DEFAULT_PUPPET_INSTANCE = cls()
        return cls._DEFAULT_PUPPET_INSTANCE
    
    def __init__(self):
        """
        Initialize the XPP protocol handler.
        """
        # Variable registry: name -> (id, type, permissions, value, update_rate, last_sent_time)
        self._variables = {}
        self._variable_ids = {}  # id -> name (reverse mapping)
        self._next_var_id = FIRST_CUSTOM_VAR_ID  # Start at 38 for custom variables
        
        # Transport layer
        self._transport = None
        self._transport_type = None
        self._rx_buffer = bytearray()
        self._rx_state = 0  # 0=waiting for start, 1=reading length, 2=reading payload, 3=waiting for end
        
        # Packet tracking
        self.packets_sent = 0
        self.packets_received = 0
        self.packets_dropped = 0
        self._sequence_number = 0
        
        # Update rate management
        self._update_timer = Timer(-1)
        self._update_timer_running = False
        
        # Program state
        self._program_running = False
        
        # Initialize transport
        self._init_transport()
    
    def _init_transport(self):
        """
        Auto-detect and initialize transport (BLE or USB serial).
        """
        # Try BLE first
        try:
            from ble.blerepl import uart
            self._transport = uart
            self._transport_type = 'BLE'
            self._transport.set_data_callback(self._data_callback)
            return
        except (ImportError, AttributeError):
            pass
        
        # Fallback to USB serial
        try:
            # For USB serial, we'll use sys.stdin/sys.stdout or machine.UART
            # Check if we can use UART
            try:
                from machine import UART
                # Try to open UART for USB serial (typically UART(0))
                self._transport = UART(0, baudrate=115200)
                self._transport_type = 'USB'
                # For USB serial, we'll need to poll in a timer
                self._usb_poll_timer = Timer(-2)
                self._usb_poll_timer.init(period=10, mode=Timer.PERIODIC, 
                                         callback=lambda t: self._poll_usb())
                return
            except:
                # Last resort: use sys.stdin/stdout
                self._transport = sys
                self._transport_type = 'USB_STDIO'
                return
        except:
            pass
        
        raise RuntimeError("No transport available (BLE or USB serial)")
    
    def _poll_usb(self):
        """
        Poll USB serial for incoming data.
        """
        if self._transport_type == 'USB' and self._transport.any():
            data = self._transport.read(self._transport.any())
            if data:
                self._data_callback(data)
    
    def _data_callback(self, data):
        """
        Handle incoming data from transport layer.
        """
        if isinstance(data, (bytes, bytearray)):
            self._rx_buffer.extend(data)
        else:
            self._rx_buffer.append(data)
        
        self._process_rx_buffer()
    
    def _process_rx_buffer(self):
        """
        Process received data buffer, extracting complete messages.
        """
        while len(self._rx_buffer) >= 2:
            if self._rx_state == 0:  # Waiting for start sequence
                # Look for start sequence
                idx = -1
                for i in range(len(self._rx_buffer) - 1):
                    if self._rx_buffer[i] == MSG_START_1 and self._rx_buffer[i+1] == MSG_START_2:
                        idx = i
                        break
                
                if idx == -1:
                    # No start sequence found, clear buffer except last byte
                    if len(self._rx_buffer) > 1:
                        self._rx_buffer = self._rx_buffer[-1:]
                    return
                
                # Remove everything before start sequence
                if idx > 0:
                    self._rx_buffer = self._rx_buffer[idx:]
                
                # Found start, move to length
                self._rx_state = 1
                continue
            
            elif self._rx_state == 1:  # Reading type
                if len(self._rx_buffer) < 3:  # Need start(2) + type(1)
                    return
                msg_type = self._rx_buffer[2]
                self._rx_state = 2
                continue
            
            elif self._rx_state == 2:  # Reading length
                if len(self._rx_buffer) < 4:  # Need start(2) + type(1) + length(1)
                    return
                payload_len = self._rx_buffer[3]
                if payload_len > MAX_PAYLOAD_SIZE:
                    # Invalid length, reset
                    self._rx_buffer = self._rx_buffer[4:]
                    self._rx_state = 0
                    self.packets_dropped += 1
                    continue
                
                self._rx_state = 3
                continue
            
            elif self._rx_state == 3:  # Reading payload
                payload_len = self._rx_buffer[3]
                total_needed = 4 + payload_len + 2  # start(2) + type(1) + len(1) + payload + end(2)
                
                if len(self._rx_buffer) < total_needed:
                    return  # Wait for more data
                
                # Check end sequence
                end_idx = 4 + payload_len
                if (self._rx_buffer[end_idx] != MSG_END_1 or 
                    self._rx_buffer[end_idx + 1] != MSG_END_2):
                    # Invalid end sequence, reset
                    self._rx_buffer = self._rx_buffer[4:]
                    self._rx_state = 0
                    self.packets_dropped += 1
                    continue
                
                # Extract message type and payload data
                msg_type = self._rx_buffer[2]
                payload_data = bytes(self._rx_buffer[4:end_idx])
                self._rx_buffer = self._rx_buffer[total_needed:]
                self._rx_state = 0
                
                # Process message
                self.packets_received += 1
                self._handle_message(msg_type, payload_data)
                continue
    
    def _write_data(self, data):
        """
        Write data to transport layer.
        """
        if self._transport_type == 'BLE':
            self._transport.write_data(data)
        elif self._transport_type == 'USB':
            self._transport.write(data)
        elif self._transport_type == 'USB_STDIO':
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
    
    def _pack_message(self, msg_type, payload_data):
        """
        Pack a message with framing.
        Returns bytearray with complete message.
        Format: [START] [TYPE] [LENGTH] [PAYLOAD] [END]
        LENGTH includes payload_data length (not including TYPE byte)
        """
        payload_len = len(payload_data)
        if payload_len > MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload too large: {payload_len} > {MAX_PAYLOAD_SIZE}")
        
        msg = bytearray()
        msg.append(MSG_START_1)
        msg.append(MSG_START_2)
        msg.append(msg_type)
        msg.append(payload_len)  # Length of payload_data only
        msg.extend(payload_data)
        msg.append(MSG_END_1)
        msg.append(MSG_END_2)
        
        return msg
    
    def _send_message(self, msg_type, payload_data):
        """
        Send a message over the transport.
        """
        msg = self._pack_message(msg_type, payload_data)
        self._write_data(msg)
        self.packets_sent += 1
        self._sequence_number = (self._sequence_number + 1) % 256
    
    def _handle_message(self, msg_type, payload_data):
        """
        Handle incoming message based on type.
        
        :param msg_type: Message type byte
        :param payload_data: Message payload data (without type byte)
        """
        if msg_type == MSG_TYPE_VAR_DEF:
            self._handle_var_def(payload_data)
        elif msg_type == MSG_TYPE_VAR_UPDATE:
            self._handle_var_update(payload_data)
        elif msg_type == MSG_TYPE_VAR_SUBSCRIBE:
            self._handle_var_subscribe(payload_data)
        elif msg_type == MSG_TYPE_VAR_UNSUBSCRIBE:
            self._handle_var_unsubscribe(payload_data)
        elif msg_type == MSG_TYPE_PROGRAM_START:
            self._handle_program_start()
        elif msg_type == MSG_TYPE_PROGRAM_END:
            self._handle_program_end()
        elif msg_type == MSG_TYPE_HEARTBEAT:
            self._handle_heartbeat(payload_data)
    
    def _handle_var_def(self, payload):
        """
        Handle variable definition message.
        Format: name_len(1) name(name_len) type(1) permissions(1) var_id(1)
        """
        if len(payload) < 3:
            return
        
        name_len = payload[0]
        if len(payload) < 1 + name_len + 3:  # name_len + name + type + permissions + var_id
            return
        
        name = payload[1:1+name_len].decode('utf-8')
        var_type = payload[1+name_len]
        permissions = payload[1+name_len+1]
        var_id = payload[1+name_len+2]
        
        # If this is a standard variable, use the predefined ID instead
        if name in _STANDARD_VAR_IDS:
            var_id = _STANDARD_VAR_IDS[name]
        
        # Register the variable with the (corrected) ID
        if name not in self._variables:
            # Default value based on type
            if var_type == VAR_TYPE_INT:
                default_value = 0
            elif var_type == VAR_TYPE_FLOAT:
                default_value = 0.0
            elif var_type == VAR_TYPE_BOOL:
                default_value = False
            else:
                return
            
            self._variables[name] = (var_id, var_type, permissions, default_value, 0, 0)
            self._variable_ids[var_id] = name
            # Update next_var_id if needed (for custom variables only)
            if var_id >= self._next_var_id and name not in _STANDARD_VAR_IDS:
                self._next_var_id = var_id + 1
                if self._next_var_id > 255:
                    self._next_var_id = FIRST_CUSTOM_VAR_ID  # Wrap to start of custom range
    
    def _handle_var_update(self, payload):
        """
        Handle variable update message (batched format).
        Format: count(1) [var_id(1) type(1) value(type-dependent)] * count
        A count of 1 is equivalent to a single update.
        """
        if len(payload) < 1:
            return
        
        count = payload[0]
        offset = 1
        
        if count == 0 or count > 50:  # Sanity check
            return
        
        # Batched update format: count(1) [var_id(1) type(1) value] * count
        for i in range(count):
            if len(payload) < offset + 2:  # Need at least var_id(1) + type(1)
                break
            
            var_id = payload[offset]
            offset += 1
            var_type = payload[offset]
            offset += 1
            
            if var_id not in self._variable_ids:
                # Skip this update, but need to advance offset
                if var_type == VAR_TYPE_INT:
                    offset += 4
                elif var_type == VAR_TYPE_FLOAT:
                    offset += 4
                elif var_type == VAR_TYPE_BOOL:
                    offset += 1
                continue
            
            name = self._variable_ids[var_id]
            var_info = self._variables[name]
            
            # Unpack value based on type from message
            if var_type == VAR_TYPE_INT:
                if len(payload) < offset + 4:
                    break
                value = struct.unpack('<i', payload[offset:offset+4])[0]
                offset += 4
            elif var_type == VAR_TYPE_FLOAT:
                if len(payload) < offset + 4:
                    break
                value = struct.unpack('<f', payload[offset:offset+4])[0]
                offset += 4
            elif var_type == VAR_TYPE_BOOL:
                if len(payload) < offset + 1:
                    break
                value = bool(payload[offset])
                offset += 1
            else:
                continue  # Unknown type, skip
            
            # Update variable if we have write permission
            if var_info[2] in (PERM_WRITE_ONLY, PERM_READ_WRITE):
                self._variables[name] = (var_info[0], var_info[1], var_info[2], 
                                        value, var_info[4], var_info[5])
    
    def _handle_var_subscribe(self, payload):
        """
        Handle variable subscribe message.
        Format: var_id(1) rate(1) [rate is in Hz, 0 = on-demand]
        """
        if len(payload) < 2:
            return
        
        var_id = payload[0]
        rate = payload[1]
        
        if var_id not in self._variable_ids:
            return
        
        name = self._variable_ids[var_id]
        var_info = self._variables[name]
        
        # Update subscription rate
        self._variables[name] = (var_info[0], var_info[1], var_info[2], 
                                 var_info[3], rate, var_info[5])
        
        # Restart update timer if needed
        self._start_update_timer()
    
    def _handle_var_unsubscribe(self, payload):
        """
        Handle variable unsubscribe message.
        Format: var_id(1)
        """
        if len(payload) < 1:
            return
        
        var_id = payload[0]
        
        if var_id not in self._variable_ids:
            return
        
        name = self._variable_ids[var_id]
        var_info = self._variables[name]
        
        # Set rate to 0 (on-demand)
        self._variables[name] = (var_info[0], var_info[1], var_info[2], 
                                 var_info[3], 0, var_info[5])
    
    def _handle_program_start(self):
        """
        Handle program start message.
        Resends variable definitions for all custom variables.
        """
        self._program_running = True
        
        # Resend variable definitions for all custom variables
        for name, var_info in self._variables.items():
            # Only resend custom variables (not standard variables)
            if name not in _STANDARD_VAR_IDS:
                var_id, var_type, permissions, value, update_rate, last_sent = var_info
                self._send_var_def(name, var_type, permissions, var_id)
    
    def _handle_program_end(self):
        """
        Handle program end message.
        """
        self._program_running = False
    
    def _handle_heartbeat(self, payload_data):
        """
        Handle heartbeat message.
        
        :param payload_data: Heartbeat payload (packets_sent, packets_received, packets_dropped)
        """
        # Send heartbeat response
        self.send_heartbeat()
    
    def define_variable(self, name, var_type, permissions=PERM_READ_WRITE):
        """
        Define a new variable in the registry.
        
        :param name: Variable name (string)
        :param var_type: Variable type (VAR_TYPE_INT, VAR_TYPE_FLOAT, VAR_TYPE_BOOL)
        :param permissions: Access permissions (PERM_READ_ONLY, PERM_WRITE_ONLY, PERM_READ_WRITE)
        :return: Variable ID if new, None if already exists
        """
        if name in self._variables:
            return self._variables[name][0]  # Return existing ID
        
        # Check if this is a standard variable
        if name in _STANDARD_VAR_IDS:
            var_id = _STANDARD_VAR_IDS[name]
            # Standard variables are predefined - don't send VAR_DEF
            send_def = False
        else:
            # Custom variable - assign from pool
            var_id = self._next_var_id
            self._next_var_id += 1
            if self._next_var_id > 255:
                raise RuntimeError("Maximum number of custom variables exceeded")
            send_def = True  # Send VAR_DEF for custom variables
        
        # Default value based on type
        if var_type == VAR_TYPE_INT:
            default_value = 0
        elif var_type == VAR_TYPE_FLOAT:
            default_value = 0.0
        elif var_type == VAR_TYPE_BOOL:
            default_value = False
        else:
            raise ValueError(f"Invalid variable type: {var_type}")
        
        self._variables[name] = (var_id, var_type, permissions, default_value, 0, 0)
        self._variable_ids[var_id] = name
        
        # Only send variable definition for custom variables
        if send_def:
            self._send_var_def(name, var_type, permissions, var_id)
        
        return var_id
    
    def _send_var_def(self, name, var_type, permissions, var_id):
        """
        Send variable definition message.
        """
        name_bytes = name.encode('utf-8')
        payload = bytearray()
        payload.append(len(name_bytes))
        payload.extend(name_bytes)
        payload.append(var_type)
        payload.append(permissions)
        payload.append(var_id)  # 1 byte
        
        self._send_message(MSG_TYPE_VAR_DEF, payload)
    
    def set_variable(self, name, value):
        """
        Set a variable value and send update if subscribed.
        
        :param name: Variable name
        :param value: Variable value
        """
        if name not in self._variables:
            raise ValueError(f"Variable not defined: {name}")
        
        var_info = self._variables[name]
        var_type = var_info[1]
        
        # Type check
        if var_type == VAR_TYPE_INT and not isinstance(value, int):
            raise TypeError(f"Variable {name} expects int, got {type(value)}")
        elif var_type == VAR_TYPE_FLOAT and not isinstance(value, (int, float)):
            raise TypeError(f"Variable {name} expects float, got {type(value)}")
        elif var_type == VAR_TYPE_BOOL and not isinstance(value, bool):
            raise TypeError(f"Variable {name} expects bool, got {type(value)}")
        
        # Update value
        self._variables[name] = (var_info[0], var_info[1], var_info[2], 
                                value, var_info[4], var_info[5])
        
        # Send update if rate > 0 or if this is an on-demand update
        # (on-demand updates are sent immediately when set)
        if var_info[4] > 0 or var_info[4] == 0:
            self._send_var_update(name)
    
    def get_variable(self, name):
        """
        Get a variable value.
        
        :param name: Variable name
        :return: Variable value
        """
        if name not in self._variables:
            raise ValueError(f"Variable not defined: {name}")
        
        return self._variables[name][3]
    
    def _send_var_update(self, name):
        """
        Send single variable update message (uses batched format with count=1).
        For multiple updates, use _send_batched_var_updates().
        """
        if name not in self._variables:
            return
        
        var_info = self._variables[name]
        var_id = var_info[0]
        var_type = var_info[1]
        value = var_info[3]
        
        # Pack as batched update with count=1
        payload = bytearray()
        payload.append(1)  # count = 1
        payload.append(var_id)  # 1 byte
        payload.append(var_type)  # Include type byte
        
        if var_type == VAR_TYPE_INT:
            payload.extend(struct.pack('<i', value))
        elif var_type == VAR_TYPE_FLOAT:
            payload.extend(struct.pack('<f', value))
        elif var_type == VAR_TYPE_BOOL:
            payload.append(1 if value else 0)
        
        self._send_message(MSG_TYPE_VAR_UPDATE, payload)
        
        # Update last sent time
        current_time = time.ticks_ms()
        self._variables[name] = (var_info[0], var_info[1], var_info[2], 
                                var_info[3], var_info[4], current_time)
    
    def _send_batched_var_updates(self, names):
        """
        Send batched variable updates in a single message.
        
        :param names: List of variable names to send
        """
        if not names:
            return
        
        # Collect updates that are ready to send
        updates = []
        current_time = time.ticks_ms()
        
        for name in names:
            if name not in self._variables:
                continue
            
            var_info = self._variables[name]
            var_id, var_type, permissions, value, rate, last_sent = var_info
            
            # Check if we have read permission
            if permissions not in (PERM_READ_ONLY, PERM_READ_WRITE):
                continue
            
            # Check if rate > 0 and enough time has passed
            if rate > 0:
                period_ms = int(1000 / rate)
                if time.ticks_diff(current_time, last_sent) < period_ms:
                    continue  # Not ready yet
            
            updates.append((name, var_info))
        
        if not updates:
            return
        
        # Pack batched update: count(1) [var_id(1) type(1) value] * count
        payload = bytearray()
        payload.append(len(updates))  # count
        
        for name, var_info in updates:
            var_id = var_info[0]
            var_type = var_info[1]
            value = var_info[3]
            
            payload.append(var_id)  # 1 byte
            payload.append(var_type)
            
            if var_type == VAR_TYPE_INT:
                payload.extend(struct.pack('<i', value))
            elif var_type == VAR_TYPE_FLOAT:
                payload.extend(struct.pack('<f', value))
            elif var_type == VAR_TYPE_BOOL:
                payload.append(1 if value else 0)
            
            # Update last sent time
            self._variables[name] = (var_info[0], var_info[1], var_info[2], 
                                    var_info[3], var_info[4], current_time)
        
        self._send_message(MSG_TYPE_VAR_UPDATE, payload)
    
    def subscribe_variable(self, name, rate_hz):
        """
        Subscribe to a variable at a specific update rate.
        
        :param name: Variable name
        :param rate_hz: Update rate in Hz (0 = on-demand only)
        """
        if name not in self._variables:
            raise ValueError(f"Variable not defined: {name}")
        
        var_info = self._variables[name]
        var_id = var_info[0]
        
        # Update rate
        self._variables[name] = (var_info[0], var_info[1], var_info[2], 
                                var_info[3], rate_hz, var_info[5])
        
        # Send subscribe message
        payload = bytes([var_id, rate_hz])
        self._send_message(MSG_TYPE_VAR_SUBSCRIBE, payload)
        
        # Start update timer if needed
        self._start_update_timer()
    
    def _start_update_timer(self):
        """
        Start or restart the update timer based on active subscriptions.
        """
        # Find maximum update rate
        max_rate = 0
        for var_info in self._variables.values():
            if var_info[4] > max_rate:
                max_rate = var_info[4]
        
        if max_rate > 0 and not self._update_timer_running:
            # Start timer at max_rate Hz
            period_ms = int(1000 / max_rate)
            self._update_timer.init(period=period_ms, mode=Timer.PERIODIC,
                                   callback=lambda t: self._update_timer_callback())
            self._update_timer_running = True
        elif max_rate == 0 and self._update_timer_running:
            # Stop timer
            self._update_timer.deinit()
            self._update_timer_running = False
        elif max_rate > 0 and self._update_timer_running:
            # Update timer period if rate changed
            period_ms = int(1000 / max_rate)
            self._update_timer.deinit()
            self._update_timer.init(period=period_ms, mode=Timer.PERIODIC,
                                   callback=lambda t: self._update_timer_callback())
    
    def _update_timer_callback(self):
        """
        Timer callback to send variable updates at their specified rates.
        Batches all ready updates into a single message for efficiency.
        """
        current_time = time.ticks_ms()
        
        # Collect all variables that are ready to send
        ready_vars = []
        for name, var_info in self._variables.items():
            var_id, var_type, permissions, value, rate, last_sent = var_info
            
            # Only send if rate > 0 and enough time has passed
            if rate > 0:
                period_ms = int(1000 / rate)
                if time.ticks_diff(current_time, last_sent) >= period_ms:
                    # Check if we have read permission
                    if permissions in (PERM_READ_ONLY, PERM_READ_WRITE):
                        ready_vars.append(name)
        
        # Send all ready updates in a single batched message
        if ready_vars:
            self._send_batched_var_updates(ready_vars)
    
    def send_program_start(self):
        """
        Send program start message.
        """
        self._send_message(MSG_TYPE_PROGRAM_START, b'')
        self._program_running = True
    
    def send_program_end(self):
        """
        Send program end message.
        """
        self._send_message(MSG_TYPE_PROGRAM_END, b'')
        self._program_running = False
    
    def send_heartbeat(self):
        """
        Send heartbeat message.
        """
        # Include stats
        payload = struct.pack('<III', self.packets_sent, self.packets_received, 
                            self.packets_dropped)
        self._send_message(MSG_TYPE_HEARTBEAT, payload)
    
    def get_stats(self):
        """
        Get protocol statistics.
        
        :return: Dictionary with stats
        """
        return {
            'packets_sent': self.packets_sent,
            'packets_received': self.packets_received,
            'packets_dropped': self.packets_dropped,
            'transport_type': self._transport_type,
            'program_running': self._program_running
        }

