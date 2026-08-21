# ADDR_7BIT = 0x19  # SA0 left floating (internal pull-up)
ADDR_7BIT = 0x18  # SA0 to GND

# Registers
CTRL1 = 0x20
CTRL3 = 0x22
CTRL4_INT1_PAD_CTRL = 0x23
CTRL6 = 0x25
CTRL7 = 0x3F
INT_DUR = 0x33
TAP_THS_X = 0x30
TAP_THS_Y = 0x31
TAP_THS_Z = 0x32
TAP_SRC = 0x39
FIFO_CTRL = 0x2E

# FIFO modes
FIFO_MODE_BYPASS = 0b000
FIFO_MODE_FIFO = 0b001
FIFO_MODE_CONTINUOUS = 0b110
FIFO_MODE_CONTINUOUS2FIFO = 0b011
FIFO_MODE_BYPASS2CONTINUOUS = 0b100

# functions to compose register values from components
# the components are always NOT bit-shifted when passed
# return values are all integers limited to byte range

def make_ctrl1(odr, mode=0, lp_mode=0):  # always specify odr since the hardware default is power-down
    return (odr << 4) + (mode << 2) + lp_mode

def make_ctrl3(self_test=0, pp_od=0, latch_int=0, int_active_hi=0, slp_mode_sel=0, slp_mode_1=0):
    return (self_test << 6) + (pp_od << 5) + (latch_int << 4) + (int_active_hi << 3) + (slp_mode_sel << 1) + slp_mode_1

def make_ctrl4(int1_6d=0, int1_single_tap=0, int1_wu=0, int1_ff=0, int1_double_tap=0, int1_diff=0, int1_fth=0, int1_drdy=0):
    return (int1_6d << 7) + (int1_single_tap << 6) + (int1_wu << 5) + (int1_ff << 4) + (int1_double_tap << 3) + (int1_diff << 2) + (int1_fth << 1) + int1_drdy

def make_ctrl6(bw_flt=0, full_scale=0, fds=0, low_noise=0):
    return (bw_flt << 6) + (full_scale << 4) + (fds << 3) + (low_noise << 2)

def make_ctrl7(drdy_pulsed=0, int2_on_int1=0, interrupts=0, usr_off_on_out=0, usr_off_on_wu=0, usr_off_w=0, hp_ref_mode=0, lpass_on6d=0):  # defaults are as hardware
    return (drdy_pulsed << 7) + (int2_on_int1 << 6) + (interrupts << 5) + (usr_off_on_out << 4) + (usr_off_on_wu << 3) + (usr_off_w << 2) + (hp_ref_mode << 1) + lpass_on6d

def make_tap_ths_x(en_4d=0, ths_6d=0, ths_x=0):
    return (en_4d << 7) + (ths_6d << 5) + ths_x

def make_tap_ths_y(tap_prio=0, ths_y=0):
    return (tap_prio << 5) + ths_y

def make_tap_ths_z(en_x=0, en_y=0, en_z=0, ths_z=0):
    return (en_x << 7) + (en_y << 6) + (en_z << 5) + ths_z

def make_fifo_ctrl(fifo_mode=0, fifo_threshold=31):
    return (fifo_mode << 5) + fifo_threshold

def make_int_dur(latency=0, quiet=0, shock=0):  # tap durations
    """

    :param latency:
    :param quiet:
    :param shock: Maximum duration of over-threshold event to qualify as a tap. 1LSB = 8/ODR, 0 = 4/ODR
    :return:
    """
    return (latency << 4) + (quiet << 2) + shock

def odr_to_hz(odr, in_lp_mode=False):
    if odr == 0:
        return 0
    elif odr == 1:
        return 1.6 if in_lp_mode else 12.5
    elif 2 <= odr <= 6:
        return 12.5 * 2 ** (odr - 2)
    elif 7 <= odr <=9:
        return 200 if in_lp_mode else 12.5 * 2 ** (odr - 2)

def raw_to_mg(raw_val, is_12_bit=False):  # also rounds to 1dp
    # LSB is 0.244g and raw value is right-aligned 14 bit value
    mg_scale = 0.976 if is_12_bit else 0.244 / 4
    return round(raw_val * mg_scale, 1)

if __name__ == "__main__":
    print(bytes.hex(make_ctrl1(4, 1, 1)))

