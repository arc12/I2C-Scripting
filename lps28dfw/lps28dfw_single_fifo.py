from interface import Adapter, I2CDevice, format_bin, format_hex
from LPS28DFW import *
from time import sleep

adapter = Adapter()
adapter.check()

dev = I2CDevice(ADDR_7BIT_1, adapter)

# Run the device with chosen ODR into a 128 slot FIFO, set to stop when full, periodically checking the status to determine when the FIFO is full.
# Then show the output referenced to the mean value.
# Intended to explore the dynamic effects of wind gusts.

fs_mode = 0  # 0 = full scale mode 1260hPa
odr = ODR_4Hz
fifo_size = 16

whoami = dev.read_reg(REG_WHO_AM_I)
print(f"WHO_AM_I should report 0xb4. Received: {format_hex(whoami)}")

# First check the existing setup. If we're at power-on then there will be some setup to do. Otherwise skip it (thinking of MCU work reduction)
dev.write_reg(CTRL_REG2, make_ctrl2(fs_mode=fs_mode))
dev.write_reg(FIFO_WTM_REG, fifo_size)  # fifo "watermark" can be any value up to 128; does not have to be 2^n
dev.write_reg(FIFO_CTRL_REG, make_fifo_ctrl())  # reset the FIFO - sends 0 to byte. This is required, simply doing the next line only works 1st time after reset
dev.write_reg(FIFO_CTRL_REG, make_fifo_ctrl(stop_on_wtm=1, fifo_mode=1))  # enable watermark and set FIFO mode
dev.write_reg(CTRL_REG1, make_ctrl1(odr=odr, avg=AVG_512))

print("Started")
# Allow some time for the fifo to fill up (4s given setup above). If we dont wait, any unfilled slots give a pressure of 2048hPa in mode 0, 4096 in mode 1
sleep(fifo_size / odr_hz(odr))
fifo_status = 0
while fifo_status == 0:
    fifo_status = dev.read_reg(FIFO_STATUS2)[0] & 0xE0
    print(f"FIFO_STATUS2 = {format_bin(fifo_status)}")
    sleep(1)

# Pressure FIFO readout is different registers to plain last reading as used for one-shot
# LSB = 1/4096hPa in fs_mode == 0, ie a shade over 0.024Pa
pressures = list()
for i in range(fifo_size):
    p_registers = dev.read_reg(FIFO_DATA_OUT_PRESS_XL, 3)  # auto-increments to L and H bytes
    pressures.append(100 * compute_pressure_hpa_reg(p_registers, fs_mode=fs_mode))

import statistics
mean_pressure = statistics.mean(pressures)
sd_pressures = statistics.stdev(pressures)
min_pressure = min(pressures)
max_pressure = max(pressures)
print(f"Mean = {mean_pressure:.2f}Pa, SD={sd_pressures:.2f}Pa, Range=({min_pressure:.2f}, {max_pressure:.2f})")

rel_pressures = [round(p - min_pressure, 1) for p in pressures]  # round for printing
print("Normalised pressures (to mean):\n", rel_pressures)

import plotly.express as px
fig = px.line(y=rel_pressures)
fig.show()