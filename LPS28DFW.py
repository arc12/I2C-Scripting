# pin 2, SA0 controls the LSb of the device address
ADDR_7BIT_0 = 0x5C
ADDR_7BIT_1 = 0x5D

# Limited declaration of registers for basic testing.
# Among other things, interrupts (incl thresholds and reference) and FIFO features are not included here
# Also offset (as I am planning on using the device in differential pairs and calibrating against the difference)
REG_WHO_AM_I = 0x0F  # should be 0xBF
CTRL_REG1 = 0x10
CTRL_REG2 = 0x11
# CTRL_REG3 = 0x12
# CTRL_REG4 = 0x13
REG_STATUS = 0x27
# measurement results
REG_PRESSURE_XL = 0x28
REG_PRESSURE_L = 0x29
REG_PRESSURE_H = 0x2A
REG_TEMP_L = 0x2B
REG_TEMP_H = 0x2C

# Bit patterns for register setting components
ODR_ONESHOT = 0b0000  # default
ODR_1Hz = 0b0001
ODR_4Hz = 0b0010
ODR_10Hz = 0b0011
ODR_25Hz = 0b0100
ODR_50Hz = 0b0101
ODR_75Hz = 0b0110
ODR_100Hz = 0b0111
ODR_200Hz = 0b1000

AVG_4 = 0b000  # default
AVG_8 = 0b001
AVG_16 = 0b010
AVG_32 = 0b011
AVG_64 = 0b100
AVG_128 = 0b101
AVG_512 = 0b111

FS_MODE_1260hPa = 0
FS_MODE_4060hPa = 1


def fs_divisor(fs_mode):
    """Divisor for raw register value according to the fs-mode setting (ctrl reg 2)"""
    return 4096 if fs_mode == 0 else 2048


def make_ctrl1(odr=0, avg=0):  # always specify odr since the hardware default is power-down
    return (odr << 3) + avg

def make_ctrl2(boot=0, fs_mode=0, lp_filter_mode=0, lp_filter_en=0, bdu_mode=0, sw_reset=0, one_shot_trigger=0):
    return (boot << 7) + (fs_mode << 6) + (lp_filter_mode << 5) + (lp_filter_en << 4) + (bdu_mode << 3) + (sw_reset << 2) + one_shot_trigger

def compute_pressure_hpa(press_xl, press_l, press_h, fs_mode):
    return ((press_h << 16) + (press_l << 8) + press_xl) / fs_divisor(fs_mode)

def compute_pressure_hpa_reg(reg_vals, fs_mode):
    """Version which takes register values as a list in read-order (xl-l-h)"""
    return compute_pressure_hpa(reg_vals[0], reg_vals[1], reg_vals[2], fs_mode)

def compute_temp_c(temp_l, temp_h):
    return ((temp_h << 8) + temp_l) / 100

def compute_temp_c_reg(reg_vals):
    return compute_temp_c(reg_vals[0], reg_vals[1])

def decode_status_available(status):
    """
    Is unread data available?
    :param status: value of REG_STATUS
    :return: tuple of booleans for temp and pressure
    """
    return (status & 1) > 0, (status & 2) > 0

def decode_status_overrun(status):
    """
    Has unread data been over-written
    :param status: value of REG_STATUS
    :return: tuple of booleans for pressure and temp
    """
    return (status & 0b010000) > 0, (status & 0b100000) > 0