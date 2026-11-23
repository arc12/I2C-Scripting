# Waits for a tap event (reads the TAP_SRC register - no hardware interrupt) then, after a short delay, reads in the FIFO (32 slots) and plots the x,y,z impulse.
# An alternative approach would be to use the "continuous to FIFO" operation mode, but this would collect 32 samples after the tap event then stop
#   filling the FIFO. ie if left to run its course, we would lose the measurements leading up to the tap detection
# See also: lis2dw12_event_capture.py

from time import time, sleep

from interface import Adapter, I2CDevice, bytes_to_int16, format_bin
from LIS2DW12 import *
import csv
from os import makedirs, path

import pandas as pd
import plotly.express as px

# SETUP PARAMS
gpio_int1 = 2  # GPIO connected to INT1
# A. ODR and tap detection
# tap threshold
tap_ths = 1  # 1LSB of threshold = 1/32 of full scale reading, ie 2/32g for smallest scale = 62.5mg. 0 disables!
# MAX duration of over-threshold to qualify as tap
shock = 3  # 0 = default = 4 samples (duration 4/ODR), 1lsb = 8 samples. Max 3.
# output data rate. NB determines duration which FIFO represents too.
odr = 8
# B. Other
# performance/power mode
lp_mode = None  # 0  # this is the LP_MODE selection. Set to None for high-performance mode. Get 12 bits if == 0 (this is "lp mode 1" in the datasheet) otherwise 14
filter_type = 1  # 0 = low pass (default), 1 = high pass
hp_ref = True  # whether to use the HP filter in "reference" mode. Default false
# C. Treated as constants
# +/- 2g full scale

# derived - generally for helpful display
tap_ths_mg = tap_ths * 2000 / 32
odr_freq = odr_to_hz(odr, lp_mode is not None)
shock_dur = (4 if shock == 0 else 8 * shock) / odr_freq

# D. Sampling
read_fifo_delay = 28 / odr_freq - 0.05  # seconds to wait after receiving tap event before reading FIFO
n_captures = 100  # no of times to repeat capture, saving each into a separate csv file
# E. Plotting
# whether to plot relative to the first (oldest) slot in the FIFO (for each of xyz)
plot_relative = False
plot_range = 500  # mg +/- on plot

makedirs("lis2dw12 capture", exist_ok=True)
adapter = Adapter()

dev = I2CDevice(ADDR_7BIT, adapter)

# setup the FIFO
dev.write_reg(FIFO_CTRL, make_fifo_ctrl(FIFO_MODE_CONTINUOUS))
# set up tap and interrupt.
dev.write_reg(TAP_THS_X, make_tap_ths_x(ths_x=tap_ths))
dev.write_reg(TAP_THS_Y, make_tap_ths_y(ths_y=tap_ths))
dev.write_reg(TAP_THS_Z, make_tap_ths_z(en_x=True, en_y=True, en_z=True, ths_z=tap_ths))  # enabling all axes.
# max duration to qualify as a tap.
dev.write_reg(INT_DUR, make_int_dur(shock=shock, quiet=0))
# enable int to INT1
dev.write_reg(CTRL4_INT1_PAD_CTRL, make_ctrl4(int1_single_tap=True))
dev.write_reg(CTRL7, make_ctrl7(interrupts=True, hp_ref_mode=hp_ref))
dev.write_reg(CTRL3, make_ctrl3(latch_int=True))


# set +/-2g, hp filter, low-noise disabled
dev.write_reg(CTRL6, make_ctrl6(fds=filter_type))

# start operation. For tap detection, app note recommends >=400Hz ODR.
# However: even 12.5Hz seems fairly reliable, depending on the impulse. I suspect it would be fine for drip counting
#           which means a sleep/wake mode, where sleep ODR=12.5Hz, should work, although it looks like sleep is practically the same as odr=2, mode=0, lp_mode=0
# 12.5Hz ODR + mode=0, lp_mode=0 and low_noise=0 should use 1uA. cf 1.5uA @ 25Hz and only 3uA at 50Hz. 1.5uA -> 13mAh per year.
if lp_mode is None:
    dev.write_reg(CTRL1, make_ctrl1(odr=odr, mode=1))
else:
    dev.write_reg(CTRL1, make_ctrl1(odr=odr, mode=0, lp_mode=lp_mode))

dev.adapter.serial.close()

dev.dump_reg([("CTRL1", CTRL1),
              ("CTRL3", CTRL3),
              ("CTRL4_INT1_PAD_CTRL", CTRL4_INT1_PAD_CTRL),
              ("CTRL6", CTRL6),
              ("CTRL7", CTRL7),
              ("INT_DUR", INT_DUR),
              ("FIFO_CTRL", FIFO_CTRL),
              ("TAP_THS_X", TAP_THS_X),
              ("TAP_THS_X", TAP_THS_Y),
              ("TAP_THS_X", TAP_THS_Z)
              ])

print(f"ODR={odr_freq}Hz")

for n_capture in range(n_captures):
    print(f"Capture {n_capture + 1} /  {n_captures}")
    results = list()

    dev.adapter.serial.open()

    # wait for interrupt
    while not adapter.check_gpio_bit(gpio_int1):
        pass

    # specified delay
    sleep(max(read_fifo_delay, 0))

    # empty FIFO
    for i in range(0, 32):
        xyz = bytes_to_int16(dev.write_read(bytes([0x28]), 6))  # returns list
        results.append(xyz)

    # reading the interrupt source register resets the interrupt latch (incl pin)
    print("Tap Src: ", format_bin(dev.read_reg(TAP_SRC)[0]))

    dev.adapter.serial.close()

    # with open(path.join("lis2dw12 capture", f"fifo_capture_{n_capture+1}{'_hp_ref' if hp_ref else ''}.csv"), 'w', newline='') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(["index", "x_mg", "y_mg", "z_mg"])
    #     for i in range(32):
    #         writer.writerow([i, raw_to_mg(results[i][0]), raw_to_mg(results[i][1]), raw_to_mg(results[i][2])])

    for axis in range(3):
        abs_vals = [abs(xyz[axis]) for xyz in results]
        print(f"Axis {'xyz'[axis]}: max abs value = {raw_to_mg(max(abs_vals))}mg")

    df = pd.DataFrame(results, columns=["x", "y", "z"]).apply(lambda x: raw_to_mg(x))
    if plot_relative:
        df = df - df.iloc[0]
    df["time_s"] = [i / odr_freq for i in range(0, 32)]

    title = f"ODR={odr_freq}Hz Threshold={tap_ths_mg}mg Max shock={shock_dur}s"
    if lp_mode is None:
        title += " HP mode"
    else:
        title += f" LP mode {lp_mode + 1}"
    if filter_type == 0:
        title += " Low pass filter"
    else:
        title += " High pass filter"
        if hp_ref:
            title += "(ref mode)"

    fig = px.line(df, x="time_s", y=["x", "y", "z"], title=title, range_y=(-plot_range, plot_range))
    fig.add_hline(y=tap_ths_mg, line_width=0.5, line_dash="dash", line_color="green")
    fig.add_hline(y=-tap_ths_mg, line_width=0.5, line_dash="dash", line_color="green")
    fig.show()

    sleep(1)