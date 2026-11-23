# SOMEWHAT INCOMPLETE - lacking FIFO, interrupt and threshold, NVM, drive strength
# does include low pass filter and over-sampling

# pin SDO controls the LSb of the device address. SDO must not be floating
ADDR_7BIT_0 = 0x46
ADDR_7BIT_1 = 0x47

# Limited declaration of registers for basic testing.
# Among other things, interrupts (incl thresholds and reference) and FIFO features are not included here
# Also offset (as I am planning on using the device in differential pairs and calibrating against the difference)
# = ASIC identification
REG_WHO_AM_I = 0x01  #  should be 0x50
# measurement results
REG_TEMP_XL = 0x1D
REG_TEMP_L = 0x1E
REG_TEMP_H = 0x1F
REG_PRESSURE_XL = 0x20
REG_PRESSURE_L = 0x21
REG_PRESSURE_H = 0x22
# status
REG_STATUS = 0x27  # flags, cleared on read. incl data_ready and POR complete + FIFO and range threshold
# LP filter, over-sampling, ODR
REG_DSP_CONFIG = 0x30
REG_IIR_CONFIG = 0x31
REG_OSR = 0x36
REG_ODR = 0x37  # includes power mode bits
# 0x38 is "effective OSR"
# odd-balls
REG_CMD = 0x7E  # incl soft (config) reset

# Bit patterns for register setting components
# Low pass filter coefficients for reg 0x31. Apply for both temp and pressure
IIR_BYPASSED = 0b000  # ie no filter
IIR_COEFF_1 = 0b001
IIR_COEFF_3 = 0b010
IIR_COEFF_7 = 0b011
IIR_COEFF_15 = 0b100
IIR_COEFF_31 = 0b101
IIR_COEFF_63 = 0b110
IIR_COEFF_127 = 0b111

# Over-sampling Rate (OSR). Apply for temp and pressure
OSR_X1 = 0b000
OSR_X2 = 0b001
OSR_X4 = 0b010
OSR_X8 = 0b011
OSR_X16 = 0b100
OSR_X32 = 0b101
OSR_X64 = 0b110
OSR_X128 = 0b111

# Output data rate (ODR) INCOMPLETE LIST!
ODR_0P125Hz = 0x1F
ODR_0P25Hz = 0x1E
ODR_0P5Hz = 0x1D
ODR_1Hz = 0x1C
ODR_2Hz = 0x1B
ODR_3Hz = 0x1A
ODR_4Hz = 0x19
ODR_5Hz = 0x18
# goes all they way up to 240Hz!

# power mode (used in reg 0x37)
MODE_STANDBY = 0b00
MODE_NORMAL = 0b01
MODE_FORCED = 0b10  # one-time measurement
MODE_NONSTOP = 0b11

odr_lut = {
    ODR_0P125Hz: 0.125,
    ODR_0P25Hz: 0.25,
    ODR_0P5Hz: 0.5,
    ODR_1Hz: 1.0,
    ODR_2Hz: 2.0,
    ODR_3Hz: 3.0,
    ODR_4Hz: 4.0,
    ODR_5Hz: 5.0
}

def odr_hz(odr_code):
    """
    Return the ODR in Hz for the passed (bit pattern) code
    :param odr_code:
    :return:
    """
    return odr_lut.get(odr_code, None)



def make_odr(pwr_mode=0, odr=ODR_1Hz, disable_deep_standby=False):  # deep standby is not available if ODR >=5Hz, LP filter used, + others - see 4.3.2
    reg_val = (odr << 2) + pwr_mode
    if disable_deep_standby:
        reg_val += 128
    return reg_val

def make_iir(p_filter_coeff=0, t_filter_coeff=0):
    return (p_filter_coeff << 3) + t_filter_coeff

# I don't understand most of the options so they are not included!!!!
# Doc says iir_flush_forced_en relates to FORCED mode in register desc but section on IIR says "e.g. when using FORCED"
def make_dsp_config(iir_flush_forced_en=0):
    return iir_flush_forced_en << 2

def make_osr(press_en=True, p_osr=0, t_osr=0):
    reg_val = (p_osr << 3) + t_osr
    if press_en:
        reg_val += 64
    return reg_val

def compute_pressure_hpa(press_xl, press_l, press_h):
    return ((press_h << 16) + (press_l << 8) + press_xl) / 64

def compute_pressure_hpa_reg(reg_vals):
    """Version which takes register values as a list in read-order (xl-l-h)"""
    return compute_pressure_hpa(reg_vals[0], reg_vals[1], reg_vals[2])

def compute_temp_c(temp_l, temp_h):  # ignore XL byte as the LSB is 1/65536 C
    return ((temp_h << 8) + temp_l) / 256  # LSB = 0.0039C

def compute_temp_c_reg(reg_vals):
    if len(reg_vals) == 3:
        return compute_temp_c(reg_vals[1], reg_vals[2])  # discard XL
    else:
        return compute_temp_c(reg_vals[0], reg_vals[1])
