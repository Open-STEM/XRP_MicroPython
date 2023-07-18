from uctypes import BFUINT8, BF_POS, BF_LEN
from micropython import const

"""
	Possible I2C addresses
"""
LSM_ADDR_PRIMARY   = const(0x6B)
LSM_ADDR_SECONDARY = const(0x6A)

"""
	Register addresses
"""
LSM_REG_WHO_AM_I         = const(0x0F)
LSM_REG_CTRL1_XL         = const(0x10)
LSM_REG_CTRL2_G          = const(0x11)
LSM_REG_CTRL3_C          = const(0x12)
LSM_REG_OUT_TEMP_L       = const(0x20)
LSM_REG_OUT_TEMP_H       = const(0x21)
LSM_REG_OUTX_L_G         = const(0x22)
LSM_REG_OUTY_L_G         = const(0x24)
LSM_REG_OUTZ_L_G         = const(0x26)
LSM_REG_OUTX_L_A         = const(0x28)
LSM_REG_OUTY_L_A         = const(0x2A)
LSM_REG_OUTZ_L_A         = const(0x2C)

"""
	Bit field struct definitions of registers
"""
LSM_REG_LAYOUT_CTRL1_XL = {
    "ODR_XL"     : BFUINT8 | 4 << BF_POS | 4 << BF_LEN,
    "FS_XL"      : BFUINT8 | 2 << BF_POS | 2 << BF_LEN,
    "LPF2_XL_EN" : BFUINT8 | 1 << BF_POS | 1 << BF_LEN,
}
LSM_REG_LAYOUT_CTRL2_G = {
    "ODR_G" : BFUINT8 | 4 << BF_POS | 4 << BF_LEN,
    "FS_G"  : BFUINT8 | 1 << BF_POS | 3 << BF_LEN,
}
LSM_REG_LAYOUT_CTRL3_C = {
    "BOOT"      : BFUINT8 | 7 << BF_POS | 1 << BF_LEN,
    "BDU"       : BFUINT8 | 6 << BF_POS | 1 << BF_LEN,
    "H_LACTIVE" : BFUINT8 | 5 << BF_POS | 1 << BF_LEN,
    "PP_OD"     : BFUINT8 | 4 << BF_POS | 1 << BF_LEN,
    "SIM"       : BFUINT8 | 3 << BF_POS | 1 << BF_LEN,
    "IF_INC"    : BFUINT8 | 2 << BF_POS | 1 << BF_LEN,
    "SW_RESET"  : BFUINT8 | 0 << BF_POS | 1 << BF_LEN,
}

"""
	Dictionaries for possible register settings
"""
LSM_ODR = {
	"0Hz"    : 0x0,
	"12.5Hz" : 0x1,
	"26Hz"   : 0x2,
	"52Hz"   : 0x3,
	"104Hz"  : 0x4,
	"208Hz"  : 0x5,
	"416Hz"  : 0x6,
	"833Hz"  : 0x7,
	"1660Hz" : 0x8,
	"3330Hz" : 0x9,
	"6660Hz" : 0xA,
}
LSM_ACCEL_FS = {
	"2g"  : 0x0,
	"4g"  : 0x2,
	"8g"  : 0x3,
	"16g" : 0x1,
}
LSM_GYRO_FS = {
	"125dps"  : 0x1,
	"250dps"  : 0x0,
	"500dps"  : 0x2,
	"1000dps" : 0x4,
	"2000dps" : 0x6,
}

"""
    Other contants
"""
LSM_WHO_AM_I_VALUE      = 0x6C
LSM_MG_PER_LSB_2G       = 0.061
LSM_MDPS_PER_LSB_125DPS = 4.375