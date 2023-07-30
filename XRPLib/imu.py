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

        # Initialize member variables
        self._reset_member_variables()

        # Transmit and recieve buffers
        self.tb = bytearray(1)
        self.rb = bytearray(1)

        # Copies of registers. Bytes and structs share the same memory
        # addresses, so changing one changes the other
        self.reg_ctrl1_xl_byte   = bytearray(1)
        self.reg_ctrl2_g_byte    = bytearray(1)
        self.reg_ctrl3_c_byte    = bytearray(1)
        self.reg_ctrl1_xl_bits   = struct(addressof(self.reg_ctrl1_xl_byte), LSM_REG_LAYOUT_CTRL1_XL)
        self.reg_ctrl2_g_bits    = struct(addressof(self.reg_ctrl2_g_byte), LSM_REG_LAYOUT_CTRL2_G)
        self.reg_ctrl3_c_bits    = struct(addressof(self.reg_ctrl3_c_byte), LSM_REG_LAYOUT_CTRL3_C)

        # Create timer
        self.update_timer = Timer(-1)

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

    """
        The following are private helper methods to read and write registers, as well as to convert the read values to the correct unit.
    """

    def _reset_member_variables(self):
        # Vector of IMU measurements
        self.irq_v = [[0, 0, 0], [0, 0, 0]]

        # Sensor offsets
        self.gyro_offsets = [0,0,0]
        self.acc_offsets = [0,0,0]

        # Scale factors when ranges are changed
        self._acc_scale_factor = 1
        self._gyro_scale_factor = 1

        # Angles
        self.pitch = 0
        self.yaw = 0
        self.roll = 0
        self.pitchComputed = True
        self.yawComputed = True
        self.rollComputed = True

        # Madgwick values
        self.beta = 0.1
        self.q = [1, 0, 0, 0]

    def _int16(self, d):
        return d if d < 0x8000 else d - 0x10000

    def _setreg(self, reg, dat):
        self.tb[0] = dat
        self.i2c.writeto_mem(self.addr, reg, self.tb)

    def _getreg(self, reg):
        self.i2c.readfrom_mem_into(self.addr, reg, self.rb)
        return self.rb[0]

    def _getregs(self, reg, num_bytes):
        rx_buf = bytearray(num_bytes)
        self.i2c.readfrom_mem_into(self.addr, reg, rx_buf)
        return rx_buf

    def _get2reg(self, reg):
        return self._getreg(reg) + self._getreg(reg+1) * 256

    def _r_w_reg(self, reg, dat, mask):
        self._getreg(reg)
        self.rb[0] = (self.rb[0] & mask) | dat
        self._setreg(reg, self.rb[0])

    def _set_bdu(self, bdu = True):
        """
        Sets Block Data Update bit
        """
        self.reg_ctrl3_c_byte[0] = self._getreg(LSM_REG_CTRL3_C)
        self.reg_ctrl3_c_bits.BDU = bdu
        self._setreg(LSM_REG_CTRL3_C, self.reg_ctrl3_c_byte[0])

    def _set_if_inc(self, if_inc = True):
        """
        Sets InterFace INCrement bit
        """
        self.reg_ctrl3_c_byte[0] = self._getreg(LSM_REG_CTRL3_C)
        self.reg_ctrl3_c_bits.IF_INC = if_inc
        self._setreg(LSM_REG_CTRL3_C, self.reg_ctrl3_c_byte[0])

    def _raw_to_mg(self, raw):
        return self._int16((raw[1] << 8) | raw[0]) * LSM_MG_PER_LSB_2G * self._acc_scale_factor

    def _raw_to_mdps(self, raw):
        return self._int16((raw[1] << 8) | raw[0]) * LSM_MDPS_PER_LSB_125DPS * self._gyro_scale_factor
    
    """
        Public facing API Methods
    """

    def is_connected(self):
        """
        Checks whether the IMU is connected

        :return: True if WHO_AM_I value is correct, otherwise False
        :rtype: bool
        """
        who_am_i = self._getreg(LSM_REG_WHO_AM_I)
        return who_am_i == LSM_WHO_AM_I_VALUE

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
        # Stop timer
        self._stop_timer()

        # Reset member variables
        self._reset_member_variables()

        # Set BOOT and SW_RESET bits
        self.reg_ctrl3_c_byte[0] = self._getreg(LSM_REG_CTRL3_C)
        self.reg_ctrl3_c_bits.BOOT = 1
        self.reg_ctrl3_c_bits.SW_RESET = 1
        self._setreg(LSM_REG_CTRL3_C, self.reg_ctrl3_c_byte[0])

        # Wait for reset to complete, if requested
        if wait_for_reset:
            # Loop with timeout
            t0 = time.ticks_ms()
            while time.ticks_ms() < (t0 + wait_timeout_ms):
                # Check if register has returned to default value (0x04)
                self.reg_ctrl3_c_byte[0] = self._getreg(LSM_REG_CTRL3_C)
                if self.reg_ctrl3_c_byte[0] == 0x04:
                    return True
            # Timeout occurred
            return False
        else:
            return True

    def get_acc_x(self):
        """
        :return: The current reading for the accelerometer's X-axis, in mg
        :rtype: int
        """
        # Burst read data registers
        raw_bytes = self._getregs(LSM_REG_OUTX_L_A, 2)

        # Convert raw data to mg's
        return self._raw_to_mg(raw_bytes[0:2]) - self.acc_offsets[0]

    def get_acc_y(self):
        """
        :return: The current reading for the accelerometer's Y-axis, in mg
        :rtype: int
        """
        # Burst read data registers
        raw_bytes = self._getregs(LSM_REG_OUTY_L_A, 2)

        # Convert raw data to mg's
        return self._raw_to_mg(raw_bytes[0:2]) - self.acc_offsets[1]

    def get_acc_z(self):
        """
        :return: The current reading for the accelerometer's Z-axis, in mg
        :rtype: int
        """
        # Burst read data registers
        raw_bytes = self._getregs(LSM_REG_OUTZ_L_A, 2)

        # Convert raw data to mg's
        return self._raw_to_mg(raw_bytes[0:2]) - self.acc_offsets[2]
    
    def get_acc_rates(self):
        """
        :return: the list of readings from the Accelerometer, in mg. The order of the values is x, y, z.
        :rtype: list<int>
        """
        # Burst read data registers
        raw_bytes = self._getregs(LSM_REG_OUTX_L_A, 6)

        # Convert raw data to mg's
        self.irq_v[0][0] = self._raw_to_mg(raw_bytes[0:2]) - self.acc_offsets[0]
        self.irq_v[0][1] = self._raw_to_mg(raw_bytes[2:4]) - self.acc_offsets[1]
        self.irq_v[0][2] = self._raw_to_mg(raw_bytes[4:6]) - self.acc_offsets[2]

        return self.irq_v[0]

    def get_gyro_x_rate(self):
        """
            Individual axis read for the Gyroscope's X-axis, in mg
        """
        # Burst read data registers
        raw_bytes = self._getregs(LSM_REG_OUTX_L_G, 2)

        # Convert raw data to mdps
        return self._raw_to_mdps(raw_bytes[0:2]) - self.gyro_offsets[0]

    def get_gyro_y_rate(self):
        """
            Individual axis read for the Gyroscope's Y-axis, in mg
        """
        # Burst read data registers
        raw_bytes = self._getregs(LSM_REG_OUTY_L_G, 2)

        # Convert raw data to mdps
        return self._raw_to_mdps(raw_bytes[0:2]) - self.gyro_offsets[1]

    def get_gyro_z_rate(self):
        """
            Individual axis read for the Gyroscope's Z-axis, in mg
        """
        # Burst read data registers
        raw_bytes = self._getregs(LSM_REG_OUTZ_L_G, 2)

        # Convert raw data to mdps
        return self._raw_to_mdps(raw_bytes[0:2]) - self.gyro_offsets[2]

    def get_gyro_rates(self):
        """
            Retrieves the array of readings from the Gyroscope, in mdps
            The order of the values is x, y, z.
        """
        # Burst read data registers
        raw_bytes = self._getregs(LSM_REG_OUTX_L_G, 6)

        # Convert raw data to mdps
        self.irq_v[1][0] = self._raw_to_mdps(raw_bytes[0:2]) - self.gyro_offsets[0]
        self.irq_v[1][1] = self._raw_to_mdps(raw_bytes[2:4]) - self.gyro_offsets[1]
        self.irq_v[1][2] = self._raw_to_mdps(raw_bytes[4:6]) - self.gyro_offsets[2]

        return self.irq_v[1]

    def get_acc_gyro_rates(self):
        """
            Get the accelerometer and gyroscope values in mg and mdps in the form of a 2D array.
            The first row is the acceleration values, the second row is the gyro values.
            The order of the values is x, y, z.
        """
        # Burst read data registers
        raw_bytes = self._getregs(LSM_REG_OUTX_L_G, 12)

        # Convert raw data to mg's and mdps
        self.irq_v[0][0] = self._raw_to_mg(raw_bytes[6:8]) - self.acc_offsets[0]
        self.irq_v[0][1] = self._raw_to_mg(raw_bytes[8:10]) - self.acc_offsets[1]
        self.irq_v[0][2] = self._raw_to_mg(raw_bytes[10:12]) - self.acc_offsets[2]
        self.irq_v[1][0] = self._raw_to_mdps(raw_bytes[0:2]) - self.gyro_offsets[0]
        self.irq_v[1][1] = self._raw_to_mdps(raw_bytes[2:4]) - self.gyro_offsets[1]
        self.irq_v[1][2] = self._raw_to_mdps(raw_bytes[4:6]) - self.gyro_offsets[2]

        return self.irq_v
    
    def get_pitch(self):
        """
        Get the pitch of the IMU in degrees. Unbounded in range

        :return: The pitch of the IMU in degrees
        :rtype: float
        """
        if self.pitchComputed == False:
            self.pitch = math.asin(-2 * (self.q[1]*self.q[3] - self.q[0]*self.q[2])) * 57.23
            self.pitchComputed = True
        return self.pitch

    def get_yaw(self):
        """
        Get the yaw (heading) of the IMU in degrees. Unbounded in range

        :return: The yaw (heading) of the IMU in degrees
        :rtype: float
        """
        if self.yawComputed == False:
            self.yaw = math.atan2(self.q[1]*self.q[2] + self.q[0]*self.q[3], 0.5 - self.q[2]*self.q[2] - self.q[3]*self.q[3]) * 57.23
            self.yawComputed = True
        return self.yaw
    
    def get_heading(self):
        """
        Get's the heading of the IMU, but bounded between [0, 360)

        :return: The heading of the IMU in degrees, bound between [0, 360)
        :rtype: float
        """
        return self.get_yaw() % 360
    
    def get_roll(self):
        """
        Get the roll of the IMU in degrees. Unbounded in range

        :return: The roll of the IMU in degrees
        :rtype: float
        """
        if self.rollComputed == False:
            self.roll = math.atan2(self.q[0]*self.q[1] + self.q[2]*self.q[3], 0.5 - self.q[1]*self.q[1] - self.q[2]*self.q[2]) * 57.23
            self.rollComputed = True
        return self.roll

    def reset_angles(self):
        """
        Reset all angles to 0
        """
        self.q = [1, 0, 0, 0]

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
        self.reg_ctrl1_xl_byte[0] = self._getreg(LSM_REG_CTRL1_XL)
        #  Check if the provided value is in the dictionary
        if value not in LSM_ACCEL_FS:
            # Return string representation of this value
            index = list(LSM_ACCEL_FS.values()).index(self.reg_ctrl1_xl_bits.FS_XL)
            return list(LSM_ACCEL_FS.keys())[index]
        else:
            # Set value as requested
            self.reg_ctrl1_xl_bits.FS_XL = LSM_ACCEL_FS[value]
            self._setreg(LSM_REG_CTRL1_XL, self.reg_ctrl1_xl_byte[0])
            # Update scale factor for converting raw data
            self._acc_scale_factor = int(value.rstrip('g')) // 2

    def gyro_scale(self, value=None):
        """
        Set the gyroscope scale in dps. The scale can be:
        '125', '250', '500', '1000', or '2000'
        Pass in no parameters to retrieve the current value
        """
        # Get register value
        self.reg_ctrl2_g_byte[0] = self._getreg(LSM_REG_CTRL2_G)
        #  Check if the provided value is in the dictionary
        if value not in LSM_GYRO_FS:
            # Return string representation of this value
            index = list(LSM_GYRO_FS.values()).index(self.reg_ctrl2_g_bits.FS_G)
            return list(LSM_GYRO_FS.keys())[index]
        else:
            # Set value as requested
            self.reg_ctrl2_g_bits.FS_G = LSM_GYRO_FS[value]
            self._setreg(LSM_REG_CTRL2_G, self.reg_ctrl2_g_byte[0])
            # Update scale factor for converting raw data
            self._gyro_scale_factor = int(value.rstrip('dps')) // 125

    def acc_rate(self, value=None):
        """
        Set the accelerometer rate in Hz. The rate can be:
        '0Hz', '12.5Hz', '26Hz', '52Hz', '104Hz', '208Hz', '416Hz', '833Hz', '1660Hz', '3330Hz', '6660Hz'
        Pass in no parameters to retrieve the current value
        """
        # Get register value
        self.reg_ctrl1_xl_byte[0] = self._getreg(LSM_REG_CTRL1_XL)
        #  Check if the provided value is in the dictionary
        if value not in LSM_ODR:
            # Return string representation of this value
            index = list(LSM_ODR.values()).index(self.reg_ctrl1_xl_bits.ODR_XL)
            return list(LSM_ODR.keys())[index]
        else:
            # Set value as requested
            self.reg_ctrl1_xl_bits.ODR_XL = LSM_ODR[value]
            self._setreg(LSM_REG_CTRL1_XL, self.reg_ctrl1_xl_byte[0])

    def gyro_rate(self, value=None):
        """
        Set the gyroscope rate in Hz. The rate can be:
        '0Hz', '12.5Hz', '26Hz', '52Hz', '104Hz', '208Hz', '416Hz', '833Hz', '1660Hz', '3330Hz', '6660Hz'
        Pass in no parameters to retrieve the current value
        """
        # Get register value
        self.reg_ctrl2_g_byte[0] = self._getreg(LSM_REG_CTRL2_G)
        #  Check if the provided value is in the dictionary
        if value not in LSM_ODR:
            # Return string representation of this value
            index = list(LSM_ODR.values()).index(self.reg_ctrl1_xl_bits.ODR_G)
            return list(LSM_ODR.keys())[index]
        else:
            # Set value as requested
            self.reg_ctrl2_g_bits.ODR_G = LSM_ODR[value]
            self._setreg(LSM_REG_CTRL2_G, self.reg_ctrl2_g_byte[0])

            # Update timer frequency
            self.timer_frequency = int(value.rstrip('Hz'))
            self.timer_period = 1 / self.timer_frequency
            self._start_timer()

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
            cur_vals = self.get_acc_gyro_rates()
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

    def _invSqrt(self, x):
        return x ** -0.5

    def _update_imu_readings(self):
        # Called every tick through a callback timer
        # Function converted to Python from https://github.com/arduino-libraries/MadgwickAHRS

        # Get IMU measurements
        cur_vals = self.get_acc_gyro_rates()

        # Acceleration, from mg's to g's
        ax = cur_vals[0][0] * 0.001
        ay = cur_vals[0][1] * 0.001
        az = cur_vals[0][2] * 0.001
        
        # Rotation rate, from mdps to rad/sec
        gx = cur_vals[1][0] * 0.0000174533
        gy = cur_vals[1][1] * 0.0000174533
        gz = cur_vals[1][2] * 0.0000174533
    
        # Rate of change of quaternion from gyroscope
        qDot1 = 0.5 * (-self.q[1] * gx - self.q[2] * gy - self.q[3] * gz)
        qDot2 = 0.5 * (self.q[0] * gx + self.q[2] * gz - self.q[3] * gy)
        qDot3 = 0.5 * (self.q[0] * gy - self.q[1] * gz + self.q[3] * gx)
        qDot4 = 0.5 * (self.q[0] * gz + self.q[1] * gy - self.q[2] * gx)

        # Compute feedback only if accelerometer measurement valid (avoids NaN in accelerometer normalisation)
        if(not ((ax == 0) and (ay == 0) and (az == 0))):
            # Norm`alise accelerometer measurement
            recipNorm = self._invSqrt(ax * ax + ay * ay + az * az)
            ax *= recipNorm
            ay *= recipNorm
            az *= recipNorm

            # Auxiliary variables to avoid repeated arithmetic
            _2q0 = 2 * self.q[0]
            _2q1 = 2 * self.q[1]
            _2q2 = 2 * self.q[2]
            _2q3 = 2 * self.q[3]
            _4q0 = 4 * self.q[0]
            _4q1 = 4 * self.q[1]
            _4q2 = 4 * self.q[2]
            _8q1 = 8 * self.q[1]
            _8q2 = 8 * self.q[2]
            q0q0 = self.q[0] * self.q[0]
            q1q1 = self.q[1] * self.q[1]
            q2q2 = self.q[2] * self.q[2]
            q3q3 = self.q[3] * self.q[3]

            # Gradient decent algorithm corrective step
            s0 = _4q0 * q2q2 + _2q2 * ax + _4q0 * q1q1 - _2q1 * ay
            s1 = _4q1 * q3q3 - _2q3 * ax + 4 * q0q0 * self.q[1] - _2q0 * ay - _4q1 + _8q1 * q1q1 + _8q1 * q2q2 + _4q1 * az
            s2 = 4 * q0q0 * self.q[2] + _2q0 * ax + _4q2 * q3q3 - _2q3 * ay - _4q2 + _8q2 * q1q1 + _8q2 * q2q2 + _4q2 * az
            s3 = 4 * q1q1 * self.q[3] - _2q1 * ax + 4 * q2q2 * self.q[3] - _2q2 * ay
            recipNorm = self._invSqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3) # normalise step magnitude
            s0 *= recipNorm
            s1 *= recipNorm
            s2 *= recipNorm
            s3 *= recipNorm

            # Apply feedback step
            qDot1 -= self.beta * s0
            qDot2 -= self.beta * s1
            qDot3 -= self.beta * s2
            qDot4 -= self.beta * s3

        # Integrate rate of change of quaternion to yield quaternion
        self.q[0] += qDot1 * self.timer_period
        self.q[1] += qDot2 * self.timer_period
        self.q[2] += qDot3 * self.timer_period
        self.q[3] += qDot4 * self.timer_period

        # Normalise quaternion
        recipNorm = self._invSqrt(self.q[0] * self.q[0] + self.q[1] * self.q[1] + self.q[2] * self.q[2] + self.q[3] * self.q[3])
        self.q[0] *= recipNorm
        self.q[1] *= recipNorm
        self.q[2] *= recipNorm
        self.q[3] *= recipNorm
        
        # Update RPY flags
        self.pitchComputed = False
        self.yawComputed = False
        self.rollComputed = False