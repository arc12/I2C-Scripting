# Single tap detection - experiment with ODR and modes + tap threshold and duration
# Tap creates an interrupt on INT1, which is configured to be latched.
# Python loops, polling the Adapter GPIO, which should be connected to the LIS2DW12 interrupt lines. Latched interrupt is then reset

from interface import Adapter, I2CDevice, format_bin
from LIS2DW12 import *
from time import sleep

adapter = Adapter()
adapter.check()

dev = I2CDevice(ADDR_7BIT, adapter)

# Basic presence test; the WHO_AM_I register should return fixed 0x44.
val = dev.read_reg(0x0F)
if val[0] == 0x44:
    print("Device found OK")
else:
    raise Exception("Device not found!")

# set up tap and interrupt.
ths = 1  # 1LSB of threshold = 1/32 of full scale reading, ie 2/32g for smallest scale = 62.5mg
dev.write_reg(TAP_THS_X, make_tap_ths_x(ths_x=ths))
dev.write_reg(TAP_THS_Y, make_tap_ths_y(ths_y=ths))
dev.write_reg(TAP_THS_Z, make_tap_ths_z(en_x=True, en_y=True, en_z=True, ths_z=ths))  # enabling all axes.
# max duration to qualify as a tap. default is 4/ODR
dev.write_reg(INT_DUR, make_int_dur(shock=0))
# enable int to INT1
dev.write_reg(CTRL4_INT1_PAD_CTRL, make_ctrl4(int1_single_tap=True))
dev.write_reg(CTRL7, make_ctrl7(interrupts=True))
dev.write_reg(CTRL3, make_ctrl3(latch_int=True))

# put into continuous operation. App note recommends >=400Hz ODR.
# However: even 12.5Hz seems fairly reliable, depending on the impulse. I suspect it would be fine for drip counting
#           which means a sleep/wake mode, where sleep ODR=12.5Hz, should work, although it looks like sleep is practically the same as odr=2, mode=0, lp_mode=0
# 12.5Hz ODR + mode=0, lp_mode=0 and low_noise=0 should use 1uA. cf 1.5uA @ 25Hz and only 3uA at 50Hz. 1.5uA -> 13mAh per year.
dev.write_reg(CTRL1, make_ctrl1(
    # odr=7,  # 200Hz in LP mode, 400Hz in HP mode
    # odr=4,  # 50Hz
    odr=3,  # 2 = 12.5Hz
    mode=0,  # LP mode
    lp_mode=0  # LP mode 1, 12 bit
))

while True:
    while not adapter.check_gpio_bit(4):
        pass
    print("Tap Src: ", format_bin(dev.read_reg(TAP_SRC)[0]))  # reading the interrupt source register resets the interrupt latch (incl pin)
    sleep(1)