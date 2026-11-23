# Sets the device into continuous operation without fifo and periodically accesses XYZ g vales
# The HP filter and "ref mode" are toggled every 8 readings

from interface import Adapter, I2CDevice, format_hex, bytes_to_int16
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

# put into continuous operation
dev.write_reg(CTRL1, make_ctrl1(
    odr=2,  # 12.5Hz
    mode=0,  # LP mode
    lp_mode=0  # LP mode 1, 12 bit
))
# set +/-2g, minimal filter, low-noise disabled (these are fn and device defaults)
dev.write_reg(CTRL6, make_ctrl6())
dev.write_reg(CTRL7, make_ctrl7())  # various flags - HP_REF_MODE of current interest

def read_accel():
    accel_raw = dev.read_reg(0x28, 6)
    print(format_hex(accel_raw, bytes_per_sep=2))
    print(bytes_to_int16(accel_raw))

fds = False
i = 0
while True:
    read_accel()
    i += 1
    if i == 8:
        fds ^= True
        i = 0
        print("Change: HP Path Active & HP Ref Mode = ", fds)
        dev.write_reg(CTRL6, make_ctrl6(fds=fds))
        dev.write_reg(CTRL7, make_ctrl7(hp_ref_mode=fds))

    sleep(1)

