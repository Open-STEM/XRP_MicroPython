# LSM6DSO 3D accelerometer and 3D gyroscope seneor micropython drive
# ver: 1.0
# License: MIT
# Author: shaoziyang (shaoziyang@micropython.org.cn)
# v1.0 2019.7

from .imu_defs import *
from uctypes import struct, addressof
from machine import I2C, Pin, Timer, disable_irq, enable_irq
import time, math

class IMU():

    _DEFAULT_IMU_INSTANCE = None

    @classmethod
    def get_default_imu(cls):
        """
        Get the default XRP v2 IMU instance. This is a singleton, so only one instance of the drivetrain will ever exist.
        """

        if cls._DEFAULT_IMU_INSTANCE is None:
            cls._DEFAULT_IMU_INSTANCE = cls(
                scl_pin=19,
                sda_pin=18,
                addr=LSM_ADDR_PRIMARY
            )  
            cls._DEFAULT_IMU_INSTANCE.calibrate()
        return cls._DEFAULT_IMU_INSTANCE

    def __init__(self, scl_pin: int, sda_pin: int, addr):
        # I2C values
        self.i2c = I2C(id=1, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=400000)
        self.addr = addr

        # Transmit and recieve buffers
        self.tb = bytearray(1)
        self.rb = bytearray(1)

        # Vector of IMU measurements
        self.irq_v = [[0, 0, 0], [0, 0, 0]]

        # Power control
        self._power = True
        self._power_a = 0x10
        self._power_g = 0x10
        
        # Copies of registers. Bytes and structs share the same memory
        # addresses, so changing one changes the other
        self.reg_ctrl1_xl_byte   = bytearray(1)
        self.reg_ctrl2_g_byte    = bytearray(1)
        self.reg_ctrl3_c_byte    = bytearray(1)
        self.reg_ctrl1_xl_struct = struct(addressof(self.reg_ctrl1_xl_byte), LSM_REG_LAYOUT_CTRL1_XL)
        self.reg_ctrl2_g_struct  = struct(addressof(self.reg_ctrl2_g_byte), LSM_REG_LAYOUT_CTRL2_G)
        self.reg_ctrl3_c_struct  = struct(addressof(self.reg_ctrl3_c_byte), LSM_REG_LAYOUT_CTRL3_C)

        # Check if the IMU is connected
        if not self.is_connected():
            # TODO - do somehting intelligent here
            pass
        
        # Reset sensor to clear any previous configuration
        self.reset()
        
        # Enable block data update
        self._set_bdu()

        # Set default scale for each sensor
        self.acc_scale('16g')
        self.gyro_scale('2000dps')

        # Set default rate for each sensor
        self.acc_rate('208Hz')
        self.gyro_rate('208Hz')

        # Initialize offsets to zero
        self.gyro_offsets = [0,0,0]
        self.acc_offsets = [0,0,0]

        # Initialize integrators to zero
        self.running_pitch = 0
        self.running_yaw = 0
        self.running_roll = 0

        # Create timer
        self.update_timer = Timer(-1)


    """
        The following are private helper methods to read and write registers, as well as to convert the read values to the correct unit.
    """

    def _int16(self, d):
        return d if d < 0x8000 else d - 0x10000

    def _setreg(self, reg, dat):
        self.tb[0] = dat
        self.i2c.writeto_mem(self.addr, reg, self.tb)

    def _getreg(self, reg):
        self.i2c.readfrom_mem_into(self.addr, reg, self.rb)
        return self.rb[0]

    def _get2reg(self, reg):
        return self._getreg(reg) + self._getreg(reg+1) * 256

    def _r_w_reg(self, reg, dat, mask):
        self._getreg(reg)
        self.rb[0] = (self.rb[0] & mask) | dat
        self._setreg(reg, self.rb[0])

    def is_connected(self):
        """
        Checks whether the IMU is connected

        :return: True if WHO_AM_I value is correct, otherwise False
        :rtype: bool
        """
        who_am_i = self._getreg(LSM_REG_WHO_AM_I)
        return who_am_i == 0x6C

    def reset(self, wait_for_reset = True, wait_timeout_ms = 100):
        """
        Resets the IMU, and restores all registers to their default values

        :param wait_for_reset: Whether to wait for reset to complete
        :type wait_for_reset: bool
        :param wait_timeout_ms: Timeout in milliseconds when waiting for reset
        :type wait_timeout_ms: int
        :return: False if timeout occurred, otherwise True
        :rtype: bool
        """
        # Set BOOT and SW_RESET bits
        self.reg_ctrl3_c_byte = self._getreg(LSM_REG_CTRL3_C)
        self.reg_ctrl3_c_struct.BOOT = 1
        self.reg_ctrl3_c_struct.SW_RESET = 1
        self._setreg(LSM_REG_CTRL3_C, self.reg_ctrl3_c_byte)

        # Wait for reset to complete, if requested
        if wait_for_reset:
            # Loop with timeout
            t0 = time.ticks_ms()
            while time.ticks_ms() < (t0 + wait_timeout_ms):
                # Check if register has returned to default value (0x04)
                self.reg_ctrl3_c_byte = self._getreg(LSM_REG_CTRL3_C)
                if self.reg_ctrl3_c_byte == 0x04:
                    return True
            # Timeout occurred
            return False
        else:
            return True

    def _set_bdu(self, bdu = True):
        """
        Sets Block Data Update bit
        """
        self.reg_ctrl3_c_byte = self._getreg(LSM_REG_CTRL3_C)
        self.reg_ctrl3_c_struct.BDU = bdu
        self._setreg(LSM_REG_CTRL3_C, self.reg_ctrl3_c_byte)

    def _set_if_inc(self, if_inc = True):
        """
        Sets InterFace INCrement bit
        """
        self.reg_ctrl3_c_byte = self._getreg(LSM_REG_CTRL3_C)
        self.reg_ctrl3_c_struct.IF_INC = if_inc
        self._setreg(LSM_REG_CTRL3_C, self.reg_ctrl3_c_byte)

    def _mg(self, reg):
        return round(self._int16(self._get2reg(reg)) * LSM_MG_PER_LSB)

    def _mdps(self, reg):
        return round(self._int16(self._get2reg(reg)) * LSM_MDPS_PER_LSB)

    def _get_gyro_x_rate(self):
        """
            Individual axis read for the Gyroscope's X-axis, in mg
        """
        return self._mdps(LSM_REG_OUTX_L_G) - self.gyro_offsets[0]

    def _get_gyro_y_rate(self):
        """
            Individual axis read for the Gyroscope's Y-axis, in mg
        """
        return self._mdps(LSM_REG_OUTY_L_G) - self.gyro_offsets[1]

    def _get_gyro_z_rate(self):
        """
            Individual axis read for the Gyroscope's Z-axis, in mg
        """
        return self._mdps(LSM_REG_OUTZ_L_G) - self.gyro_offsets[2]

    def _get_gyro_rates(self):
        """
            Retrieves the array of readings from the Gyroscope, in mdps
            The order of the values is x, y, z.
        """
        self.irq_v[1][0] = self._get_gyro_x_rate()
        self.irq_v[1][1] = self._get_gyro_y_rate()
        self.irq_v[1][2] = self._get_gyro_z_rate()
        return self.irq_v[1]

    def _get_acc_gyro_rates(self):
        """
            Get the accelerometer and gyroscope values in mg and mdps in the form of a 2D array.
            The first row is the acceleration values, the second row is the gyro values.
            The order of the values is x, y, z.
        """
        self.get_acc_rates()
        self._get_gyro_rates()
        return self.irq_v
    
    """
        Public facing API Methods
    """

    def get_acc_x(self):
        """
        :return: The current reading for the accelerometer's X-axis, in mg
        :rtype: int
        """
        return self._mg(LSM_REG_OUTX_L_A) - self.acc_offsets[0]

    def get_acc_y(self):
        """
        :return: The current reading for the accelerometer's Y-axis, in mg
        :rtype: int
        """
        return self._mg(LSM_REG_OUTY_L_A) - self.acc_offsets[1]

    def get_acc_z(self):
        """
        :return: The current reading for the accelerometer's Z-axis, in mg
        :rtype: int
        """
        return self._mg(LSM_REG_OUTZ_L_A) - self.acc_offsets[2]
    
    def get_acc_rates(self):
        """
        :return: the list of readings from the Accelerometer, in mg. The order of the values is x, y, z.
        :rtype: list<int>
        """
        self.irq_v[0][0] = self.get_acc_x()
        self.irq_v[0][1] = self.get_acc_y()
        self.irq_v[0][2] = self.get_acc_z()
        return self.irq_v[0]
    
    def get_pitch(self):
        """
        Get the pitch of the IMU in degrees. Unbounded in range

        :return: The pitch of the IMU in degrees
        :rtype: float
        """
        return self.running_pitch
    
    def get_yaw(self):
        """
        Get the yaw (heading) of the IMU in degrees. Unbounded in range

        :return: The yaw (heading) of the IMU in degrees
        :rtype: float
        """
        return self.running_yaw
    
    def get_heading(self):
        """
        Get's the heading of the IMU, but bounded between [0, 360)

        :return: The heading of the IMU in degrees, bound between [0, 360)
        :rtype: float
        """
        return self.running_yaw % 360
    
    def get_roll(self):
        """
        Get the roll of the IMU in degrees. Unbounded in range

        :return: The roll of the IMU in degrees
        :rtype: float
        """
        return self.running_roll
    
    def reset_pitch(self):
        """
        Reset the pitch to 0
        """
        self.running_pitch = 0

    def reset_yaw(self):
        """
        Reset the yaw (heading) to 0
        """
        self.running_yaw = 0
    
    def reset_roll(self):
        """
        Reset the roll to 0
        """
        self.running_roll = 0

    def set_pitch(self, pitch):
        """
        Set the pitch to a specific angle in degrees

        :param pitch: The pitch to set the IMU to
        :type pitch: float
        """
        self.running_pitch = pitch

    def set_yaw(self, yaw):
        """
        Set the yaw (heading) to a specific angle in degrees

        :param yaw: The yaw (heading) to set the IMU to
        :type yaw: float
        """
        self.running_yaw = yaw

    def set_roll(self, roll):
        """
        Set the roll to a specific angle in degrees

        :param roll: The roll to set the IMU to
        :type roll: float
        """
        self.running_roll = roll

    def temperature(self):
        """
        Read the temperature of the LSM6DSO in degrees Celsius

        :return: The temperature of the LSM6DSO in degrees Celsius
        :rtype: float
        """
        # The LSM6DSO's temperature can be read from the OUT_TEMP_L register
        # We use OUT_TEMP_L+1 if OUT_TEMP_L cannot be read
        try:
            return self._int16(self._get2reg(LSM_REG_OUT_TEMP_L))/256 + 25
        except MemoryError:
            return self._temperature_irq()

    def _temperature_irq(self):
        # Helper function for temperature() to read the alternate temperature register
        self._getreg(LSM_REG_OUT_TEMP_L+1)
        if self.rb[0] & 0x80:
            self.rb[0] -= 256
        return self.rb[0] + 25

    def acc_scale(self, value=None):
        """
        Set the accelerometer scale in g. The scale can be:
        '2g', '4g', '8g', or '16g'
        Pass in no parameters to retrieve the current value
        """
        # Get register value
        self.reg_ctrl1_xl_byte = self._getreg(LSM_REG_CTRL1_XL)
        #  Check if the provided value is in the dictionary
        if value not in LSM_ACCEL_FS:
            # Return string representation of this value
            index = list(LSM_ACCEL_FS.values()).index(self.reg_ctrl1_xl_struct.FS_XL)
            return list(LSM_ACCEL_FS.keys())[index]
        else:
            # Set value as requested
            self.reg_ctrl1_xl_struct.FS_XL = LSM_ACCEL_FS[value]
            self._setreg(LSM_REG_CTRL1_XL, self.reg_ctrl1_xl_byte)

    def gyro_scale(self, value=None):
        """
        Set the gyroscope scale in dps. The scale can be:
        '125', '250', '500', '1000', or '2000'
        Pass in no parameters to retrieve the current value
        """
        # Get register value
        self.reg_ctrl2_g_byte = self._getreg(LSM_REG_CTRL2_G)
        #  Check if the provided value is in the dictionary
        if value not in LSM_GYRO_FS:
            # Return string representation of this value
            index = list(LSM_GYRO_FS.values()).index(self.reg_ctrl2_g_struct.FS_G)
            return list(LSM_GYRO_FS.keys())[index]
        else:
            # Set value as requested
            self.reg_ctrl2_g_struct.FS_G = LSM_GYRO_FS[value]
            self._setreg(LSM_REG_CTRL2_G, self.reg_ctrl2_g_byte)

    def acc_rate(self, value=None):
        """
        Set the accelerometer rate in Hz. The rate can be:
        '0Hz', '12.5Hz', '26Hz', '52Hz', '104Hz', '208Hz', '416Hz', '833Hz', '1660Hz', '3330Hz', '6660Hz'
        Pass in no parameters to retrieve the current value
        """
        # Get register value
        self.reg_ctrl1_xl_byte = self._getreg(LSM_REG_CTRL1_XL)
        #  Check if the provided value is in the dictionary
        if value not in LSM_ODR:
            # Return string representation of this value
            index = list(LSM_ODR.values()).index(self.reg_ctrl1_xl_struct.ODR_XL)
            return list(LSM_ODR.keys())[index]
        else:
            # Set value as requested
            self.reg_ctrl1_xl_struct.ODR_XL = LSM_ODR[value]
            self._setreg(LSM_REG_CTRL1_XL, self.reg_ctrl1_xl_byte)

    def gyro_rate(self, value=None):
        """
        Set the gyroscope rate in Hz. The rate can be:
        '0Hz', '12.5Hz', '26Hz', '52Hz', '104Hz', '208Hz', '416Hz', '833Hz', '1660Hz', '3330Hz', '6660Hz'
        Pass in no parameters to retrieve the current value
        """
        # Get register value
        self.reg_ctrl2_g_byte = self._getreg(LSM_REG_CTRL2_G)
        #  Check if the provided value is in the dictionary
        if value not in LSM_ODR:
            # Return string representation of this value
            index = list(LSM_ODR.values()).index(self.reg_ctrl1_xl_struct.ODR_G)
            return list(LSM_ODR.keys())[index]
        else:
            # Set value as requested
            self.reg_ctrl2_g_struct.ODR_G = LSM_ODR[value]
            self._setreg(LSM_REG_CTRL2_G, self.reg_ctrl2_g_byte)

            # Update timer frequency
            self.timer_frequency = int(value.rstrip('Hz'))
            self._start_timer()

    def power(self, on:bool=None):
        """
        Turn the LSM6DSO on or off.
        Pass in no parameters to retrieve the current value

        :param on: Whether to turn the LSM6DSO on or off, or None
        :type on: bool (or None)
        """
        if on is None:
            return self._power
        else:
            self._power = on
            if on:
                self._r_w_reg(LSM_REG_CTRL1_XL, self._power_a, 0x0F)
                self._r_w_reg(LSM_REG_CTRL2_G, self._power_g, 0x0F)
            else:
                self._power_a = self._getreg(LSM_REG_CTRL1_XL) & 0xF0
                self._power_g = self._getreg(LSM_REG_CTRL2_G) & 0xF0
                self._r_w_reg(LSM_REG_CTRL1_XL, 0, 0x0F)
                self._r_w_reg(LSM_REG_CTRL2_G, 0, 0x0F)

    def calibrate(self, calibration_time:float=1, vertical_axis:int= 2):
        """
        Collect readings for [calibration_time] seconds and calibrate the IMU based on those readings
        Do not move the robot during this time
        Assumes the board to be parallel to the ground. Please use the vertical_axis parameter if that is not correct

        :param calibration_time: The time in seconds to collect readings for
        :type calibration_time: float
        :param vertical_axis: The axis that is vertical. 0 for X, 1 for Y, 2 for Z
        :type vertical_axis: int
        """
        self._stop_timer()
        self.acc_offsets = [0,0,0]
        self.gyro_offsets = [0,0,0]
        avg_vals = [[0,0,0],[0,0,0]]
        num_vals = 0
        # Wait a bit for sensor to start measuring (data registers may default to something nonsensical)
        time.sleep(.1)
        start_time = time.ticks_ms()
        while time.ticks_ms() < start_time + calibration_time*1000:
            cur_vals = self._get_acc_gyro_rates()
            # Accelerometer averages
            avg_vals[0][0] += cur_vals[0][0]
            avg_vals[0][1] += cur_vals[0][1]
            avg_vals[0][2] += cur_vals[0][2]
            # Gyroscope averages
            avg_vals[1][0] += cur_vals[1][0]
            avg_vals[1][1] += cur_vals[1][1]
            avg_vals[1][2] += cur_vals[1][2]
            # Increment counter and wait for next loop
            num_vals += 1
            time.sleep(1 / self.timer_frequency)

        # Compute averages
        avg_vals[0][0] /= num_vals
        avg_vals[0][1] /= num_vals
        avg_vals[0][2] /= num_vals
        avg_vals[1][0] /= num_vals
        avg_vals[1][1] /= num_vals
        avg_vals[1][2] /= num_vals

        avg_vals[0][vertical_axis] -= 1000 #in mg

        self.acc_offsets = avg_vals[0]
        self.gyro_offsets = avg_vals[1]
        self._start_timer()

    def _start_timer(self):
        self.update_timer.init(freq=self.timer_frequency, callback=lambda t:self._update_imu_readings())

    def _stop_timer(self):
        self.update_timer.deinit()

    def _update_imu_readings(self):
        # Called every tick through a callback timer

        delta_pitch = self._get_gyro_x_rate() / 1000 / self.timer_frequency
        delta_roll = self._get_gyro_y_rate() / 1000 / self.timer_frequency
        delta_yaw = self._get_gyro_z_rate() / 1000 / self.timer_frequency

        state = disable_irq()
        self.running_pitch += delta_pitch
        self.running_roll += delta_roll
        self.running_yaw += delta_yaw
        enable_irq(state)