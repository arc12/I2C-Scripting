from interface import Adapter, I2CDevice, format_hex, bytes_to_int16
from LPS28DFW import *
from time import sleep

adapter = Adapter()
adapter.check()

dev = I2CDevice(ADDR_7BIT_0, adapter)

# Let the device run continuously with the FIFO set to "dynamic-stream" mode, which should allow the master to read the latest N measurements at any time.
# Settings are to match a possible still-well setting, where a series of several readings (not so many) over a few seconds would be acquired.
# These are: ODR of 4Hz and a FIFO size of 16 measurements. The extent of per-measurement averaging is low, given the number of repeats (and in moving
# water, environmental noise is likely to exceed sensor pressure noise by orders of magnitude).
# Other choices might be better, according to the frequency of the environmental noise. Maybe some practical tests with higher ODR and larger FIFO???

# Averaging effects (sensor in air on bench):
# FS_MODE = 0
# - avg = 0 (4 samples, 5uA) - sd = 0.04 to 0.05
# FS_MODE = 1 !!!
# - avg = 0 (4 samples, 5uA) - sd = 0.07 to 0.12 typical
# - avg = 1 (8 samples, 6uA) - sd = 0.06 to 0.08 typical
# - avg = 2 (16 samples, 9uA) - sd = 0.05 to 0.06
# - avg = 4 (64 samples. 20uA) - sd = 0.045 to 0.05
# Conclude: given 1hPa equiv 1cm water, avg=0 only giving sd of around 1mm depth, which seems perfectly fine.

fs_mode = 0  # 0 = full scale mode 1260hPa

# First check the existing setup. If we're at power-on then there will be some setup to do. Otherwise skip it (thinking of MCU work reduction)
reg1 = dev.read_reg(CTRL_REG1, 1)[0]
if reg1 == 0:
    print("Sensor needs setup")
    dev.write_reg(CTRL_REG2, make_ctrl2(fs_mode=fs_mode))  # reassert default of full-scale at 1260hPa. For some environments, may need 4060hPa FS
    dev.write_reg(FIFO_WTM_REG, 16)  # fifo "watermark"
    dev.write_reg(FIFO_CTRL_REG, make_fifo_ctrl(stop_on_wtm=1, fifo_mode=2))  # enable watermark and set continuous mode
    dev.write_reg(CTRL_REG1, make_ctrl1(odr=2, avg=0))  # 4Hz, x4 sampling average => 5uA running consumption. 1Hz would give 2.5uA
    # Allow some time for the fifo to fill up (4s given setup above). If we dont wait, any unfilled slots give a pressure of 2048hPa in mode 0, 4096 in mode 1
    sleep(4)

# Temperature does not have a FIFO (of course)
t_registers = dev.read_reg(REG_TEMP_L, 2)
temp = compute_temp_c_reg(t_registers)
# Pressure FIFO readout is different registers to plain last reading as used for one-shot
pressures = list()
for i in range(16):
    p_registers = dev.read_reg(FIFO_DATA_OUT_PRESS_XL, 3)  # auto-increments to L and H bytes
    # print(format_hex(p_registers, 2))
    pressures.append(round(compute_pressure_hpa_reg(p_registers, fs_mode=fs_mode), 2))  # round just for nicer printing below

# Once read, the slots get reset, so we need to wait for the FIFO to re-fill before re-reading. Old values DO NOT remain, slots refill with 0x7fffff

import statistics
print(pressures)
print(f"Mean = {statistics.mean(pressures):.2f}hPa, SD={statistics.stdev(pressures):.3f}hPa")
