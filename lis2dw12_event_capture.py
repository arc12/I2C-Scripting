# Runs at a 1600Hz ODR and loops as fast as possible (~6ms) in Python reading values, with a threshold value which determines "capture".
# Uses HP filter and runs in high performance mode (14 bit precision)
# See also: lis2dw12_event_fifo.py

from time import time
from interface import Adapter, I2CDevice, bytes_to_int16
from LIS2DW12 import *
import csv
from os import makedirs, path

# setup params
n_records = 100  # no of readings to capture
n_lead = 10  # no of readings prior to reaching the threshold which are retained
threshold = 1000  # absolute integer value of X/Y/Z (before conversion to mg) for capture trigger
threshold_axis = 2  # 0-2 decodes XYZ, being the axis to check against the threshold
hp_ref = False  # whether to use the HP filter in "reference" mode
n_captures = 10  # no of times to repeat capture, saving each into a separate csv file

makedirs("lis2dw12 capture", exist_ok=True)
adapter = Adapter()

dev = I2CDevice(ADDR_7BIT, adapter)

# put into continuous operation
dev.write_reg(CTRL1, make_ctrl1(
    odr=9,  # 1600Hz
    mode=1  # HP mode
))
mg_scale = 0.244 / 4  # LSB is 0.244g and raw value is right-aligned 14 bit value
def to_mg(val):
    return round(val * mg_scale, 1)

dev.write_reg(CTRL6, make_ctrl6(fds=True))  # set +/-2g, hp filter, low-noise disabled
dev.write_reg(CTRL7, make_ctrl7(hp_ref_mode=hp_ref))

print(f"Threshold = {to_mg(threshold)}mg")
for n_capture in range(n_captures):
    print(f"Capture {n_capture + 1} /  {n_captures}")
    results = [[0, 0, 0]] * n_records

    dev.adapter.serial.open()

    ix = 0
    start_ix = 0  # index in results which is the start of the "lead" (NOT the trigger index)
    triggered = False
    t0 = None  # trigger time, for computing mean record interval
    while True:
        xyz = bytes_to_int16(dev.write_read(bytes([0x28]), 6))  # returns list
        results[ix] = xyz
        if abs(xyz[threshold_axis]) >= threshold and not triggered:
            start_ix = (n_records + ix - n_lead + 1) % n_records
            triggered = True
            t0 = time()
        ix = (ix + 1) % n_records
        if ix == start_ix and triggered:
            break
    interval_ms = (time() - t0) * 1000 / (n_records - n_lead)

    dev.adapter.serial.close()

    print(f"Record interval = {interval_ms:.1f}ms")

    with open(path.join("lis2dw12 capture", f"capture_{n_capture+1}{'_hp_ref' if hp_ref else ''}.csv"), 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["tims_ms", "x_mg", "y_mg", "z_mg"])
        for i in range(n_records):
            ix = (start_ix + i) % n_records
            t = round(interval_ms * i, 1)
            writer.writerow([t, to_mg([ix][0]), to_mg(results[ix][1]), to_mg(results[ix][2])])

    for axis in range(3):
        abs_vals = [abs(xyz[axis]) for xyz in results]
        print(f"Axis {'xyz'[axis]}: max abs value = {to_mg(max(abs_vals))}mg")