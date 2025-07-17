from interface import Adapter, I2CDevice, format_hex, bytes_to_int16
from LPS28DFW import *
from time import sleep

adapter = Adapter()
adapter.check()

dev = I2CDevice(ADDR_7BIT_0, adapter)

whoami = dev.read_reg(REG_WHO_AM_I)
print(f"WHO_AM_I should report 0xb4. Received: {format_hex(whoami)}")

# default at power on is being in standby waiting for either a one-shot trigger or continuous to be turned on.
# Do a one-shot then poll for completion. This is leaving the default averaging setting, which is 4x over-sampling, and 1260hPa range
dev.write_reg(CTRL_REG1, make_ctrl1())  # re-assert defaults in case of re-run
print("----- x4 -----")
for rep in range(10):
    dev.write_reg(CTRL_REG2, make_ctrl2(one_shot_trigger=1))
    # I infer from the datasheet that the above settings should have about 2ms delay before data is available
    n = 0
    while (n < 10) and (dev.read_reg(REG_STATUS) == 0):
        sleep(0.0005)
        n += 1
    # print (f"{n} wait loops")

    p_registers = dev.read_reg(REG_PRESSURE_XL, 3)  # auto-increments
    t_registers = dev.read_reg(REG_TEMP_L, 2)

    print(f"Pressure={compute_pressure_hpa_reg(p_registers, fs_mode=0):.2f}hPa \tTemp={compute_temp_c_reg(t_registers)}C")

dev.write_reg(CTRL_REG1, make_ctrl1(avg=AVG_16))
print("----- x16 -----")
for rep in range(10):
    dev.write_reg(CTRL_REG2, make_ctrl2(one_shot_trigger=1))
    # I infer from the datasheet that the above settings should have about 2ms delay before data is available
    n = 0
    while (n < 10) and (dev.read_reg(REG_STATUS) == 0):
        sleep(0.0005)
        n += 1
    # print (f"{n} wait loops")

    p_registers = dev.read_reg(REG_PRESSURE_XL, 3)  # auto-increments
    t_registers = dev.read_reg(REG_TEMP_L, 2)

    print(f"Pressure={compute_pressure_hpa_reg(p_registers, fs_mode=0):.2f}hPa \tTemp={compute_temp_c_reg(t_registers)}C")