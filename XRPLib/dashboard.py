from .encoded_motor import EncodedMotor
from .rangefinder import Rangefinder
from .imu import IMU
from .reflectance import Reflectance

from ble.blerepl import uart
from machine import Timer, ADC, Pin
from micropython import const
import struct
import time


class Dashboard:

    _DEFAULT_DASHBOARD_INSTANCE = None

    YAW = const(0)
    ROLL = const(1)
    PTICH = const(2)
    ACCX = const(3)
    ACCY = const(4)
    ACCZ = const(5)
    ENCL = const(6)
    ENCR = const(7)
    ENC3 = const(8)
    ENC4 = const(9)
    CURRR = const(10)
    CURRL = const(11)
    CURR3 = const(12)
    CURR4 = const(13)
    DIST = const(14)
    REFL = const(15)
    REFR = const(16)
    VOLTAGE = const(17)

    @classmethod
    def get_default_dashboard(cls):
            """
            Get the default XRP dashboard instance. This is a singleton, so only one instance of the dashboard sensor will ever exist.
            """
            if cls._DEFAULT_DASHBOARD_INSTANCE is None:
                cls._DEFAULT_DASHBOARD_INSTANCE = cls()
                cls._DEFAULT_DASHBOARD_INSTANCE.__init__()
            return cls._DEFAULT_DASHBOARD_INSTANCE

    def __init__(self):
        """
        Manages communication with dashboard data goting to a remote computer via bluetooth

        """
        self.left_motor = EncodedMotor.get_default_encoded_motor(index=1)
        self.right_motor = EncodedMotor.get_default_encoded_motor(index=2)
        self.motor_three = EncodedMotor.get_default_encoded_motor(index=3)
        self.motor_four = EncodedMotor.get_default_encoded_motor(index=4)
        self.imu = IMU.get_default_imu()
        self.rangefinder = Rangefinder.get_default_rangefinder()
        self.reflectance = Reflectance.get_default_reflectance()
        self.VoltageADC = ADC(Pin('BOARD_VIN_MEASURE'))
        self.CurrLADC = ADC(Pin('ML_CUR'))
        self.CurrRADC = ADC(Pin('MR_CUR'))
        self.Curr3ADC = ADC(Pin('M3_CUR'))
        self.Curr4ADC = ADC(Pin('M4_CUR'))

        # Create timer
        self.update_timer = Timer(-1)

    def sendIntValue(self, index, value):
        data = bytearray([0x45, 3, 0, 0, 0])
        data[3] = index
        data[4] = value
        uart.write_data(data)

    def sendFloatValue(self, index, value):
        data = bytearray([0x45, 6, 1, 0, 0, 0, 0 ,0])
        data[3] = index
        data[4:] = struct.pack('<f', value)
        uart.write_data(data)  

    def _dashboard_update(self):
        self.sendFloatValue(self.YAW, self.imu.get_yaw())
        self.sendFloatValue(self.ROLL, self.imu.get_roll())
        self.sendFloatValue(self.PTICH, self.imu.get_pitch())
        self.sendFloatValue(self.ACCX, self.imu.get_acc_x())
        self.sendFloatValue(self.ACCY, self.imu.get_acc_y())
        self.sendFloatValue(self.ACCZ, self.imu.get_acc_z())
        self.sendIntValue(self.ENCL, self.left_motor.get_position_counts())
        self.sendIntValue(self.ENCR, self.right_motor.get_position_counts())
        self.sendIntValue(self.ENC3, self.motor_three.get_position_counts())
        self.sendIntValue(self.ENC4, self.motor_four.get_position_counts())
        self.sendIntValue(self.CURRL, self.CurrLADC.read_u16())
        self.sendIntValue(self.CURRR, self.CurrRADC.read_u16())
        self.sendIntValue(self.CURR3, self.Curr3ADC.read_u16())
        self.sendIntValue(self.CURR4, self.Curr4ADC.read_u16())
        self.sendFloatValue(self.DIST, self.rangefinder.distance())
        self.sendFloatValue(self.REFL,self.reflectance.get_left())
        self.sendFloatValue(self.REFR,self.reflectance.get_right())
        voltage = self.VoltageADC.read_u16() / (1024*64/14)
        self.sendFloatValue(self.VOLTAGE, voltage)

    def start(self):
        """
        Start sending dashboard packets to the remote computer at 3 updates per second
        """    
        # Start the timer in PERIODIC mode with a 300ms period
        self.update_timer.init(freq=3, callback=lambda t:self._dashboard_update())

    def stop(self):
        """
        Signals the remote computer to stop sending gamepad data packets. 
        """
        self.update_timer.deinit()


