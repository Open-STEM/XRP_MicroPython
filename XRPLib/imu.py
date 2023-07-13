# LSM6DSO 3D accelerometer and 3D gyroscope seneor micropython drive
# ver: 1.0
# License: MIT
# Author: shaoziyang (shaoziyang@micropython.org.cn)
# v1.0 2019.7

from machine import I2C, Pin, Timer, disable_irq, enable_irq
import time, math

LSM6DSO_WHO_AM_I = 0x0F
LSM6DSO_CTRL1_XL = 0x10
LSM6DSO_CTRL2_G = 0x11
LSM6DSO_CTRL3_C = 0x12
LSM6DSO_CTRL6_C = 0x15
LSM6DSO_CTRL8_XL = 0x17
LSM6DSO_STATUS = 0x1E
LSM6DSO_OUT_TEMP_L = 0x20
LSM6DSO_OUTX_L_G = 0x22
LSM6DSO_OUTY_L_G = 0x24
LSM6DSO_OUTZ_L_G = 0x26
LSM6DSO_OUTX_L_A = 0x28
LSM6DSO_OUTY_L_A = 0x2A
LSM6DSO_OUTZ_L_A = 0x2C

"""
    Options for accelerometer and gyroscope scale factors
"""
LSM6DSO_SCALEA = ('2g', '16g', '4g', '8g')
LSM6DSO_SCALEG = ('250', '125', '500', '', '1000', '', '2000')
LSM6DSO_ODRA = ('0', '12.5', '26', '52', '104', '208', '416', '833', '1660', '3330', '6660')
LSM6DSO_ODRG = ('0', '12.5', '26', '52', '104', '208', '416', '833', '1660', '3330', '6660')

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
                addr=0x6B
            )  
            cls._DEFAULT_IMU_INSTANCE.calibrate()
        return cls._DEFAULT_IMU_INSTANCE

    def __init__(self, scl_pin: int, sda_pin: int, addr):
        self.i2c = I2C(id=1, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=400000)
        self.addr = addr
        self.tb = bytearray(1)
        self.rb = bytearray(1)
        self.oneshot = False
        self.irq_v = [[0, 0, 0], [0, 0, 0]]
        self._power = True
        self._power_a = 0x10
        self._power_g = 0x10

        # Check WHO_AM_I register to verify IMU is connected
        foo = self._getreg(LSM6DSO_WHO_AM_I)
        if foo != 0x6C:
            # Getting here indicates sensor isn't connected
            # TODO - do somehting intelligent here
            pass
        
        # Set SW_RESET and BOOT bits to completely reset the sensor
        self._setreg(LSM6DSO_CTRL3_C, 0x81)
        # Wait for register to return to default value, with timeout
        t0 = time.ticks_ms()
        timeout_ms = 100
        while True:
            foo = self._getreg(LSM6DSO_CTRL3_C)
            if (foo == 0x04) or (time.ticks_ms() > (t0 + timeout_ms)):
                break
        
        # BDU=1 IF_INC=1
        self._setreg(LSM6DSO_CTRL3_C, 0x44)
        self._setreg(LSM6DSO_CTRL8_XL, 0)
        # scale=2G
        self._scale_a = 0
        self._scale_g = 0
        self._scale_a_c = 1
        self._scale_g_c = 1
        self.acc_scale('16g')
        self.gyro_scale('2000')
        self.acc_rate('208')
        self.gyro_rate('208')

        self.gyro_offsets = [0,0,0]
        self.acc_offsets = [0,0,0]

        self.update_time = 0.005
        self.gyro_pitch_bias = 0
        self.adjusted_pitch = 0

        self.gyro_pitch_running_total = 0

        self.running_pitch = 0
        self.running_yaw = 0
        self.running_roll = 0

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

    def _mg(self, reg):
        return round(self._int16(self._get2reg(reg)) * 0.061 * self._scale_a_c)

    def _mdps(self, reg):
        return round(self._int16(self._get2reg(reg)) * 4.375 * self._scale_g_c)

    def _get_gyro_x_rate(self):
        """
            Individual axis read for the Gyroscope's X-axis, in mg
        """
        return self._mdps(LSM6DSO_OUTX_L_G) - self.gyro_offsets[0]

    def _get_gyro_y_rate(self):
        """
            Individual axis read for the Gyroscope's Y-axis, in mg
        """
        return self._mdps(LSM6DSO_OUTY_L_G) - self.gyro_offsets[1]

    def _get_gyro_z_rate(self):
        """
            Individual axis read for the Gyroscope's Z-axis, in mg
        """
        return self._mdps(LSM6DSO_OUTZ_L_G) - self.gyro_offsets[2]

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
        return self._mg(LSM6DSO_OUTX_L_A) - self.acc_offsets[0]

    def get_acc_y(self):
        """
        :return: The current reading for the accelerometer's Y-axis, in mg
        :rtype: int
        """
        return self._mg(LSM6DSO_OUTY_L_A) - self.acc_offsets[1]

    def get_acc_z(self):
        """
        :return: The current reading for the accelerometer's Z-axis, in mg
        :rtype: int
        """
        return self._mg(LSM6DSO_OUTZ_L_A) - self.acc_offsets[2]
    
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
            return self._int16(self._get2reg(LSM6DSO_OUT_TEMP_L))/256 + 25
        except MemoryError:
            return self._temperature_irq()

    def _temperature_irq(self):
        # Helper function for temperature() to read the alternate temperature register
        self._getreg(LSM6DSO_OUT_TEMP_L+1)
        if self.rb[0] & 0x80:
            self.rb[0] -= 256
        return self.rb[0] + 25

    def acc_scale(self, dat=None):
        """
        Set the accelerometer scale. The scale can be '2g', '4g', '8g', or '16g'.
        Pass in no parameters to retrieve the current value
        """
        if dat is None:
            return LSM6DSO_SCALEA[self._scale_a]
        else:
            if type(dat) is str:
                if not dat in LSM6DSO_SCALEA: return
                self._scale_a = LSM6DSO_SCALEA.index(dat)
                self._scale_a_c = int(dat.rstrip('g'))//2
            else:
                return self._r_w_reg(LSM6DSO_CTRL1_XL, self._scale_a<<2, 0xF3)

    def gyro_scale(self, dat=None):
        """
        Set the gyroscope scale. The scale can be '125', '250', '500', '1000', or '2000'.
        Pass in no parameters to retrieve the current value
        """
        if (dat is None) or (dat == ''):
            return LSM6DSO_SCALEG[self._scale_g]
        else:
            if type(dat) is str:
                if not dat in LSM6DSO_SCALEG: return
                self._scale_g = LSM6DSO_SCALEG.index(dat)
                self._scale_g_c = int(dat)//125
            else: return
            self._r_w_reg(LSM6DSO_CTRL2_G, self._scale_g<<1, 0xF1)

    def acc_rate(self, dat=None):
        """
        Set the accelerometer rate. The rate can be '0', '12.5', '26', '52', '104', '208', '416', '833', '1660', '3330', '6660'.
        Pass in no parameters to retrieve the current value
        """
        if (dat is None) or (type(dat) is not str) or (dat not in LSM6DSO_ODRA):
            reg_val = self._getreg(LSM6DSO_CTRL1_XL)
            return (reg_val >> 4) & 0x04
        else:
            reg_val = LSM6DSO_ODRA.index(dat) << 4
            return self._r_w_reg(LSM6DSO_CTRL1_XL, reg_val, 0xF0)

    def gyro_rate(self, dat=None):
        """
        Set the gyroscope rate. The rate can be '0', '12.5', '26', '52', '104', '208', '416', '833', '1660', '3330', '6660'.
        Pass in no parameters to retrieve the current value
        """
        if (dat is None) or (type(dat) is not str) or (dat not in LSM6DSO_ODRG):
            reg_val = self._getreg(LSM6DSO_CTRL2_G)
            return (reg_val >> 4) & 0x04
        else:
            reg_val = LSM6DSO_ODRG.index(dat) << 4
            return self._r_w_reg(LSM6DSO_CTRL2_G, reg_val, 0xF0)

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
                self._r_w_reg(LSM6DSO_CTRL1_XL, self._power_a, 0x0F)
                self._r_w_reg(LSM6DSO_CTRL2_G, self._power_g, 0x0F)
            else:
                self._power_a = self._getreg(LSM6DSO_CTRL1_XL) & 0xF0
                self._power_g = self._getreg(LSM6DSO_CTRL2_G) & 0xF0
                self._r_w_reg(LSM6DSO_CTRL1_XL, 0, 0x0F)
                self._r_w_reg(LSM6DSO_CTRL2_G, 0, 0x0F)

    def calibrate(self, calibration_time:float=1, vertical_axis:int= 2, update_time:int=5):
        """
        Collect readings for [calibration_time] seconds and calibrate the IMU based on those readings
        Do not move the robot during this time
        Assumes the board to be parallel to the ground. Please use the vertical_axis parameter if that is not correct

        :param calibration_time: The time in seconds to collect readings for
        :type calibration_time: float
        :param vertical_axis: The axis that is vertical. 0 for X, 1 for Y, 2 for Z
        :type vertical_axis: int
        :param update_time: The time in milliseconds between each update of the IMU
        :type update_time: int
        """
        self.update_timer.deinit()
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
            time.sleep(update_time / 1000)

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
        self.update_timer.init(period=update_time, callback=lambda t:self._update_imu_readings())
        self.update_time = update_time/1000


    def _update_imu_readings(self):
        # Called every tick through a callback timer

        delta_pitch = self._get_gyro_x_rate()*self.update_time / 1000
        delta_roll = self._get_gyro_y_rate()*self.update_time / 1000
        delta_yaw = self._get_gyro_z_rate()*self.update_time / 1000

        state = disable_irq()
        self.running_pitch += delta_pitch
        self.running_roll += delta_roll
        self.running_yaw += delta_yaw
        enable_irq(state)