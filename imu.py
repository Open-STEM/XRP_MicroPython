# LSM6DSO 3D accelerometer and 3D gyroscope seneor micropython drive
# ver: 1.0
# License: MIT
# Author: shaoziyang (shaoziyang@micropython.org.cn)
# v1.0 2019.7

from machine import I2C,Pin
import time

LSM6DSO_CTRL1_XL = const(0x10)
LSM6DSO_CTRL2_G = const(0x11)
LSM6DSO_CTRL3_C = const(0x12)
LSM6DSO_CTRL6_C = const(0x15)
LSM6DSO_CTRL8_XL = const(0x17)
LSM6DSO_STATUS = const(0x1E)
LSM6DSO_OUT_TEMP_L = const(0x20)
LSM6DSO_OUTX_L_G = const(0x22)
LSM6DSO_OUTY_L_G = const(0x24)
LSM6DSO_OUTZ_L_G = const(0x26)
LSM6DSO_OUTX_L_A = const(0x28)
LSM6DSO_OUTY_L_A = const(0x2A)
LSM6DSO_OUTZ_L_A = const(0x2C)

"""
    Options for accelerometer and gyroscope scale factors
"""
LSM6DSO_SCALEA = ('2g', '16g', '4g', '8g')
LSM6DSO_SCALEG = ('250', '125', '500', '', '1000', '', '2000')

class IMU():
    def __init__(self, scl_pin:int=19, sda_pin:int=18, addr = 0x6B):
        self.i2c = I2C(id=1, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=400000)
        self.addr = addr
        self.tb = bytearray(1)
        self.rb = bytearray(1)
        self.oneshot = False
        self.irq_v = [[0, 0, 0], [0, 0, 0]]
        self._power = True
        self._power_a = 0x10
        self._power_g = 0x10
        # ODR_XL=1 FS_XL=0
        self._setreg(LSM6DSO_CTRL1_XL, 0x10)
        # ODR_G=1 FS_125=1
        self._setreg(LSM6DSO_CTRL2_G, 0x12)
        # BDU=1 IF_INC=1
        self._setreg(LSM6DSO_CTRL3_C, 0x44)
        self._setreg(LSM6DSO_CTRL8_XL, 0)
        # scale=2G
        self._scale_a = 0
        self._scale_g = 0
        self._scale_a_c = 1
        self._scale_g_c = 1
        self.acc_scale('2g')
        self.gyro_scale('125')


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

    """
        Public facing API Methods
    """

    def acc_x(self):
        """
            Individual axis read for the Accelerometer's X-axis, in mg
        """
        return self._mg(LSM6DSO_OUTX_L_A)

    def acc_y(self):
        """
            Individual axis read for the Accelerometer's Y-axis, in mg
        """
        return self._mg(LSM6DSO_OUTY_L_A)

    def acc_z(self):
        """
            Individual axis read for the Accelerometer's Z-axis, in mg
        """
        return self._mg(LSM6DSO_OUTZ_L_A)

    def gyro_x(self):
        """
            Individual axis read for the Gyroscope's X-axis, in mg
        """
        return self._mdps(LSM6DSO_OUTX_L_G)

    def gyro_y(self):
        """
            Individual axis read for the Gyroscope's Y-axis, in mg
        """
        return self._mdps(LSM6DSO_OUTY_L_G)

    def gyro_z(self):
        """
            Individual axis read for the Gyroscope's Z-axis, in mg
        """
        return self._mdps(LSM6DSO_OUTZ_L_G)

    def get_acc(self):
        """
            Retrieves the array of readings from the Accelerometer, in mg
            The order of the values is x, y, z.
        """
        self.irq_v[0][0] = self.acc_x()
        self.irq_v[0][1] = self.acc_y()
        self.irq_v[0][2] = self.acc_z()
        return self.irq_v[0]

    def get_gyro(self):
        """
            Retrieves the array of readings from the Gyroscope, in mdps
            The order of the values is x, y, z.
        """
        self.irq_v[1][0] = self.gyro_x()
        self.irq_v[1][1] = self.gyro_y()
        self.irq_v[1][2] = self.gyro_z()
        return self.irq_v[1]

    def get(self):
        """
            Get the accelerometer and gyroscope values in mg and mdps in the form of a 2D array.
            The first row is the acceleration values, the second row is the gyro values.
            The order of the values is x, y, z.
        """
        self.get_acc()
        self.get_gyro()
        return self.irq_v

    def temperature(self):
        """
            Read the temperature of the LSM6DSO in degrees Celsius
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
            Set the accelerometer scale. The scale can be 2, 4, 8, 16.
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
            Set the gyroscope scale. The scale can be 125, 250, 500, 1000, 2000.
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

    def power(self, on:bool=None):
        """
            Turn the LSM6DSO on or off.
            Pass in no parameters to retrieve the current value
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

#lsm = IMU()
#while(True):
#    print("%i\t%i\t%i\t%i\t%i\t%i\t%i" % (lsm.acc_x(), lsm.acc_y(), lsm.acc_z(), lsm.gyro_x(), lsm.gyro_y(), lsm.gyro_z(), lsm.temperature()))
#    time.sleep(0.1)
