from machine import I2C, Pin, Timer, disable_irq, enable_irq
import time, math
import qwiic_i2c
from qwiic_lsm6dso import QwiicLSM6DSO

acc_fs = {
    # Accelerometer full scale range values
    '2g': QwiicLSM6DSO.FS_XL_2g,
    '16g': QwiicLSM6DSO.FS_XL_16g,
    '4g' : QwiicLSM6DSO.FS_XL_4g,
    '8g' : QwiicLSM6DSO.FS_XL_8g 
}

gyro_fs = {
    # Gyroscope full scale range values
    '125' : QwiicLSM6DSO.FS_G_125dps,
    '250' : QwiicLSM6DSO.FS_G_250dps,
    '500' : QwiicLSM6DSO.FS_G_500dps,
    '1000' : QwiicLSM6DSO.FS_G_1000dps,
    '2000' : QwiicLSM6DSO.FS_G_2000dps
}

imu_odr = {
    # Accelerometer and gyroscope output data rate values
    '0Hz' : QwiicLSM6DSO.ODR_DISABLE,
    '12.5Hz' : QwiicLSM6DSO.ODR_12_5Hz,
    '26Hz' : QwiicLSM6DSO.ODR_26Hz,
    '52Hz' : QwiicLSM6DSO.ODR_52Hz,
    '104Hz' : QwiicLSM6DSO.ODR_104Hz,
    '208Hz' : QwiicLSM6DSO.ODR_208Hz,
    '416Hz' : QwiicLSM6DSO.ODR_416Hz,
    '833Hz' : QwiicLSM6DSO.ODR_833Hz,
    '1660Hz' : QwiicLSM6DSO.ODR_1660Hz,
    '3330Hz' : QwiicLSM6DSO.ODR_3330Hz,
    '6660Hz' : QwiicLSM6DSO.ODR_6660Hz
}

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
            )  
            cls._DEFAULT_IMU_INSTANCE.calibrate()
        return cls._DEFAULT_IMU_INSTANCE

    def __init__(self, scl_pin: int, sda_pin: int):

        self._i2c_driver = qwiic_i2c.getI2CDriver(sda = 18, scl = 19, freq = 400000)
        self._imu = QwiicLSM6DSO(i2c_driver=self._i2c_driver)

        self.update_timer = Timer(-1)

    """
        Public facing API Methods
    """

    def acc_scale(self, value=None):
        """
        Set the accelerometer scale in g. The scale can be:
        '2g', '4g', '8g', or '16g'
        Pass in no parameters to retrieve the current value
        """
        if value is None:
            return self._imu.get_accel_full_scale()
        elif value not in gyro_fs:
            raise False
        return self._imu.set_gyro_range(gyro_fs[value])

    def gyro_scale(self, value=None):
        """
        Set the gyroscope scale in dps. The scale can be:
        '125', '250', '500', '1000', or '2000'
        Pass in no parameters to retrieve the current value

        :param value: The scale to set the gyroscope to
        :type value: str
        :return: The current gyroscope scale, or False if the value is invalid
        """
        if value is None:
            return self._imu.get_gyro_range()
        elif value not in gyro_fs:
            raise False
        return self._imu.set_gyro_range(gyro_fs[value])

    def acc_rate(self, value=None):
        """
        Set the accelerometer rate in Hz. The rate can be:
        '0Hz', '12.5Hz', '26Hz', '52Hz', '104Hz', '208Hz', '416Hz', '833Hz', '1660Hz', '3330Hz', '6660Hz'
        Pass in no parameters to retrieve the current value
        """
        if value is None:
            return self._imu.get_accel_data_rate()
        elif value not in imu_odr:
            raise False
        return self._imu.set_accel_data_rate(imu_odr[value])

    def gyro_rate(self, value=None):
        """
        Set the gyroscope rate in Hz. The rate can be:
        '0Hz', '12.5Hz', '26Hz', '52Hz', '104Hz', '208Hz', '416Hz', '833Hz', '1660Hz', '3330Hz', '6660Hz'
        Pass in no parameters to retrieve the current value
        """
        if value is None:
            return self._imu.get_gyro_data_rate()
        elif value not in imu_odr:
            raise False
        return self._imu.set_gyro_data_rate(imu_odr[value])

    def is_connected(self):
        """
        Checks whether the IMU is connected

        :return: True if WHO_AM_I value is correct, otherwise False
        :rtype: bool
        """
        return self._imu.is_connected()

    def reset(self):
        """
        Resets the IMU, and restores all registers to their default values
        Requires recalibration after reset

        :return: True if reset was successful, otherwise False
        :rtype: bool

        """
        # Stop the update timer
        self._stop_timer()
        # Reset angle integrators
        self.running_pitch = 0
        self.running_yaw = 0
        self.running_roll = 0
        # Reset registers to default values
        self._imu.begin()
        # Change the accelerometer and gyroscope scales and data rates to the default values for the XRP
        self.acc_scale('2g')
        self.gyro_scale('125')
        self.acc_rate('416Hz')
        self.gyro_rate('416Hz')
        return 

    def get_acc_x(self):
        """
        :return: The current reading for the accelerometer's X-axis, in terms of g
        :rtype: int
        """
        return self._imu.read_float_accel_x() - self._offsets[0]

    def get_acc_y(self):
        """
        :return: The current reading for the accelerometer's Y-axis, in terms of g
        :rtype: int
        """
        return self._imu.read_float_accel_y() - self._offsets[1]

    def get_acc_z(self):
        """
        :return: The current reading for the accelerometer's Z-axis, in terms of g
        :rtype: int
        """
        return self._imu.read_float_accel_z() - self._offsets[2]
    
    def get_acc_rates(self):
        """
        :return: the list of readings from the Accelerometer, in terms of g. The order of the values is x, y, z.
        :rtype: tuple[int]
        """
        return tuple(map(lambda a,b: a-b, self._imu.read_float_accel_all(), self._offsets[0:3]))

    def get_gyro_x_rate(self):
        """
            Individual axis read for the Gyroscope's X-axis, in dps
        """
        return self._imu.read_float_gyro_x() - self._offsets[3]

    def get_gyro_y_rate(self):
        """
            Individual axis read for the Gyroscope's Y-axis, in dps
        """
        return self._imu.read_float_gyro_y() - self._offsets[4]

    def get_gyro_z_rate(self):
        """
            Individual axis read for the Gyroscope's Z-axis, in dps
        """
        return self._imu.read_float_gyro_z() - self.offsets[5]

    def get_gyro_rates(self):
        """
            :return: the list of readings from the Gyroscope, in dps. The order of the values is x, y, z.
            :rtype: tuple[int]
        """
        return self._imu.read_float_gyro_all()

    def get_acc_gyro_rates(self):
        """
            Get the accelerometer and gyroscope values in terms of g and dps in a single tuple.
            Lists the acceleration values, then the gyro values.
            The order of the values is accX, accY, accZ, gyroX, gyroY, gyroZ.
        """
        return tuple(map(lambda a,b: a-b, self._imu.read_float_accel_gyro_all(), self._offsets))
    
    def get_pitch(self):
        """
        Get the pitch of the IMU in degrees. Unbounded in range

        :return: The pitch of the IMU in degrees
        :rtype: float
        """
        return self._imu.calc_gyro(self.running_pitch)
    
    def get_yaw(self):
        """
        Get the yaw (heading) of the IMU in degrees. Unbounded in range

        :return: The yaw (heading) of the IMU in degrees
        :rtype: float
        """
        return self._imu.calc_gyro(self.running_yaw)
    
    def get_heading(self):
        """
        Get's the heading of the IMU, but bounded between [0, 360)

        :return: The heading of the IMU in degrees, bound between [0, 360)
        :rtype: float
        """
        return self._imu.calc_gyro(self.running_yaw) % 360
    
    def get_roll(self):
        """
        Get the roll of the IMU in degrees. Unbounded in range

        :return: The roll of the IMU in degrees
        :rtype: float
        """
        return self._imu.calc_gyro(self.running_roll)
    
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
        self.running_pitch = int(pitch / self._imu.gyro_raw_to_dps)

    def set_yaw(self, yaw):
        """
        Set the yaw (heading) to a specific angle in degrees

        :param yaw: The yaw (heading) to set the IMU to
        :type yaw: float
        """
        self.running_yaw = int(yaw / self._imu.gyro_raw_to_dps)

    def set_roll(self, roll):
        """
        Set the roll to a specific angle in degrees

        :param roll: The roll to set the IMU to
        :type roll: float
        """
        self.running_roll = int(roll / self._imu.gyro_raw_to_dps)

    def temperature(self):
        """
        Read the temperature of the LSM6DSO in degrees Celsius

        :return: The temperature of the LSM6DSO in degrees Celsius
        :rtype: float
        """
        return self._imu.read_temp_c()

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
        self._offsets = 0,0,0,0,0,0
        avg_vals = [0,0,0,0,0,0]
        num_vals = 0
        # Wait a bit for sensor to start measuring (data registers may default to something nonsensical)
        time.sleep(.1)
        start_time = time.ticks_ms()
        while time.ticks_ms() < start_time + calibration_time*1000:
            cur_vals = self.get_acc_gyro_rates()
            # Accelerometer averages
            avg_vals[0] += cur_vals[0]
            avg_vals[1] += cur_vals[1]
            avg_vals[2] += cur_vals[2]
            # Gyroscope averages
            avg_vals[3] += cur_vals[3]
            avg_vals[4] += cur_vals[4]
            avg_vals[5] += cur_vals[5]
            # Increment counter and wait for next loop
            num_vals += 1
            self.timer_frequency = 100
            time.sleep(1 / self.timer_frequency)

        # Compute averages
        avg_vals[0] /= num_vals
        avg_vals[1] /= num_vals
        avg_vals[2] /= num_vals
        avg_vals[3] /= num_vals
        avg_vals[4] /= num_vals
        avg_vals[5] /= num_vals

        avg_vals[vertical_axis+3] -= 1000 #in mg

        self.acc_offsets = avg_vals[0]
        self.gyro_offsets = avg_vals[1]
        self._start_timer()

    def _start_timer(self):
        self.update_timer.init(freq=self.timer_frequency, callback=lambda t:self._update_imu_readings())

    def _stop_timer(self):
        self.update_timer.deinit()

    def _update_imu_readings(self):
        # Called every tick through a callback timer
        raw = self._imu.read_raw_gyro_all()

        # Isolate the axis and convert to signed int
        gyroX = raw[0] | (raw[1] << 8)
        if gyroX >= 32768:
            gyroX -= 65536
        gyroY = raw[2] | (raw[3] << 8)
        if gyroY >= 32768:
            gyroY -= 65536
        gyroZ = raw[4] | (raw[5] << 8)
        if gyroZ >= 32768:
            gyroZ -= 65536

        state = disable_irq()
        self.running_pitch += gyroX
        self.running_roll += gyroY
        self.running_yaw += gyroZ
        enable_irq(state)