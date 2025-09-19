from interface import Adapter, I2CDevice, format_hex, bytes_to_int16
from LPS28DFW import *
from time import sleep

adapter = Adapter()
adapter.check()

# Access devices with the selectable address used - differential pressure
dev0 = I2CDevice(ADDR_7BIT_0, adapter)
dev1 = I2CDevice(ADDR_7BIT_1, adapter)

# re-assert defaults in case of re-run
dev0.write_reg(CTRL_REG1, make_ctrl1())
dev1.write_reg(CTRL_REG1, make_ctrl1())

while True:

    # Read each device in turn - see oneshot script for general comments
    p0_sum = 0
    p1_sum = 0
    n_samples = 5
    for rep in range(n_samples):
        # start both
        dev0.write_reg(CTRL_REG2, make_ctrl2(one_shot_trigger=1))
        dev1.write_reg(CTRL_REG2, make_ctrl2(one_shot_trigger=1))

        # wait for the 2nd one to finish
        n = 0
        while (n < 10) and (dev1.read_reg(REG_STATUS) == 0):
            sleep(0.0005)
            n += 1

        p0_sum += compute_pressure_hpa_reg(dev0.read_reg(REG_PRESSURE_XL, 3), fs_mode=0)
        p1_sum += compute_pressure_hpa_reg(dev1.read_reg(REG_PRESSURE_XL, 3), fs_mode=0)

    print(f"Mean Difference = {(p0_sum-p1_sum) /  n_samples:.2f}hPa")
    sleep(1)
