from time import time
from interface import Adapter, I2CDevice, bytes_to_int16
from LIS2DW12 import *

adapter = Adapter()

dev = I2CDevice(ADDR_7BIT, adapter)

# put into continuous operation
dev.write_reg(CTRL1, make_ctrl1(
    odr=4,
    mode=0,  # LP mode
    lp_mode=0  # LP mode 1, 12 bit
))
# set +/-2g, minimal filter, low-noise disabled (these are fn and device defaults)
dev.write_reg(CTRL6, make_ctrl6())
dev.write_reg(CTRL7, make_ctrl7())  # various flags - HP_REF_MODE of current interest

n_loops = 100
t0=time()
results = dev.read_reg_repeated(n_loops, 0x28, 6, convert_fn=bytes_to_int16)  # 3 axis
print(f"Loop duration @ {adapter.serial.baudrate} baud = {(time() - t0)/n_loops*1000:.1f}ms")
