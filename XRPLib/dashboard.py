from .encoded_motor import EncodedMotor
from .rangefinder import Rangefinder
from .imu import IMU
from .reflectance import Reflectance
from .puppet import Puppet, VAR_TYPE_INT, VAR_TYPE_FLOAT, PERM_READ_ONLY

from machine import Timer, ADC, Pin
from micropython import const
import time


class Dashboard:

    _DEFAULT_DASHBOARD_INSTANCE = None

    # Variable type constants
    VAR_TYPE_FLOAT = const(2)

    # Permission constants
    PERM_READ_ONLY = const(1)
    PERM_WRITE_ONLY = const(2)

    # Backward compatibility constants
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

    # Mapping from old index to XPP variable names
    _VAR_NAMES = {
        YAW: '$imu.yaw',
        ROLL: '$imu.roll',
        PTICH: '$imu.pitch',
        ACCX: '$imu.acc_x',
        ACCY: '$imu.acc_y',
        ACCZ: '$imu.acc_z',
        ENCL: '$encoder.left',
        ENCR: '$encoder.right',
        ENC3: '$encoder.3',
        ENC4: '$encoder.4',
        CURRL: '$current.left',
        CURRR: '$current.right',
        CURR3: '$current.3',
        CURR4: '$current.4',
        DIST: '$rangefinder.distance',
        REFL: '$reflectance.left',
        REFR: '$reflectance.right',
        VOLTAGE: '$voltage',
    }

    @classmethod
    def get_default_dashboard(cls):
        """
        Get the default XRP dashboard instance. This is a singleton, so only one instance of the dashboard sensor will ever exist.
        """
        if cls._DEFAULT_DASHBOARD_INSTANCE is None:
            cls._DEFAULT_DASHBOARD_INSTANCE = cls()
        return cls._DEFAULT_DASHBOARD_INSTANCE

    def __init__(self):
        """
        Manages communication with dashboard data going to a remote computer via XPP protocol.
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

        # Get XPP instance
        self._puppet = Puppet.get_default_puppet()
        
        # Register all sensor variables
        self._register_variables()
        
        # Create timer for periodic updates
        self.update_timer = Timer(-1)
        self._update_rate = 3  # Default 3 Hz

    def _register_variables(self):
        """
        Register all sensor variables with XPP.
        """
        # IMU variables (float)
        for var_name in ['$imu.yaw', '$imu.roll', '$imu.pitch', 
                        '$imu.acc_x', '$imu.acc_y', '$imu.acc_z']:
            self._puppet.define_variable(var_name, VAR_TYPE_FLOAT, PERM_READ_ONLY)
        
        # Encoder variables (int)
        for var_name in ['$encoder.left', '$encoder.right', '$encoder.3', '$encoder.4']:
            self._puppet.define_variable(var_name, VAR_TYPE_INT, PERM_READ_ONLY)
        
        # Current sensor variables (int)
        for var_name in ['$current.left', '$current.right', '$current.3', '$current.4']:
            self._puppet.define_variable(var_name, VAR_TYPE_INT, PERM_READ_ONLY)
        
        # Other sensor variables (float)
        for var_name in ['$rangefinder.distance', '$reflectance.left', 
                        '$reflectance.right', '$voltage']:
            self._puppet.define_variable(var_name, VAR_TYPE_FLOAT, PERM_READ_ONLY)

    def sendIntValue(self, index, value):
        """
        Send an integer value (backward compatibility method).
        Now uses XPP protocol.
        """
        if index not in self._VAR_NAMES:
            return
        
        var_name = self._VAR_NAMES[index]
        try:
            self._puppet.set_variable(var_name, value)
        except:
            pass  # Variable might not be registered yet

    def sendFloatValue(self, index, value):
        """
        Send a float value (backward compatibility method).
        Now uses XPP protocol.
        """
        if index not in self._VAR_NAMES:
            return
        
        var_name = self._VAR_NAMES[index]
        try:
            self._puppet.set_variable(var_name, value)
        except:
            pass  # Variable might not be registered yet

    def _dashboard_update(self):
        """
        Update all sensor variables with current readings.
        """
        # IMU data
        self._puppet.set_variable('$imu.yaw', self.imu.get_yaw())
        self._puppet.set_variable('$imu.roll', self.imu.get_roll())
        self._puppet.set_variable('$imu.pitch', self.imu.get_pitch())
        self._puppet.set_variable('$imu.acc_x', self.imu.get_acc_x())
        self._puppet.set_variable('$imu.acc_y', self.imu.get_acc_y())
        self._puppet.set_variable('$imu.acc_z', self.imu.get_acc_z())
        
        # Encoder data
        self._puppet.set_variable('$encoder.left', self.left_motor.get_position_counts())
        self._puppet.set_variable('$encoder.right', self.right_motor.get_position_counts())
        self._puppet.set_variable('$encoder.3', self.motor_three.get_position_counts())
        self._puppet.set_variable('$encoder.4', self.motor_four.get_position_counts())
        
        # Current sensor data
        self._puppet.set_variable('$current.left', self.CurrLADC.read_u16())
        self._puppet.set_variable('$current.right', self.CurrRADC.read_u16())
        self._puppet.set_variable('$current.3', self.Curr3ADC.read_u16())
        self._puppet.set_variable('$current.4', self.Curr4ADC.read_u16())
        
        # Other sensors
        self._puppet.set_variable('$rangefinder.distance', self.rangefinder.distance())
        self._puppet.set_variable('$reflectance.left', self.reflectance.get_left())
        self._puppet.set_variable('$reflectance.right', self.reflectance.get_right())
        
        # Voltage
        voltage = self.VoltageADC.read_u16() / (1024*64/14)
        self._puppet.set_variable('$voltage', voltage)

    def start(self, rate_hz=3):
        """
        Start sending dashboard packets to the remote computer at the specified rate.
        
        :param rate_hz: Update rate in Hz (default: 3)
        :type rate_hz: int
        """
        self._update_rate = rate_hz
        
        # Subscribe all variables at the specified rate
        for var_name in self._VAR_NAMES.values():
            try:
                self._puppet.subscribe_variable(var_name, rate_hz)
            except:
                pass  # Variable might not be registered yet
        
        # Also use timer for backward compatibility
        period_ms = int(1000 / rate_hz)
        self.update_timer.init(period=period_ms, mode=Timer.PERIODIC, 
                               callback=lambda t: self._dashboard_update())

    def stop(self):
        """
        Stop sending dashboard data packets.
        """
        # Unsubscribe from all variables
        for var_name in self._VAR_NAMES.values():
            try:
                self._puppet.subscribe_variable(var_name, 0)
            except:
                pass
        
        # Stop timer
        self.update_timer.deinit()

    def set_value(self, name, value, rate_hz=3):   #name is the variable name, value is the value to set
        """
        Define a variable and subscribe to it at the specified rate.
        name: the variable name (string)
        value: the value to set (float)
        rate_hz: the update rate in Hz (int)
        """
        self._puppet.define_variable(name, VAR_TYPE_FLOAT, PERM_READ_ONLY)
        try:
            self._puppet.subscribe_variable(name, rate_hz)
        except:
            pass
        self._puppet.set_variable(name, value)

    def get_value(self, name):
        """
        Get the value of a variable.
        name: the variable name (string)
        """
        self._puppet.define_variable(name, VAR_TYPE_FLOAT, PERM_WRITE_ONLY)
        return self._puppet.get_variable(name)