# Typical pattern for meterological measurements, ie:
# - no requirement for frequent measurement
# - highest resolutions not required
# - IIR LP filter is desirable to accommodate wind effects
# - specifically for Andi's GH gas platform, very low current not important due to gas measurements having orders of magnitude greater power draw.
#   => allow it to run in NORMAL mode (ie continuous sampling) rather than FORCED

from interface import Adapter, I2CDevice, format_hex, bytes_to_int16
from BMP580 import *
from time import sleep

adapter = Adapter()
adapter.check()

dev = I2CDevice(ADDR_7BIT_0, adapter)

whoami = dev.read_reg(REG_WHO_AM_I)
print(f"WHO_AM_I should report 0x50. Received: {format_hex(whoami)}")

# No oversampling with 1/8s ODR
run_code = "A"
odr = ODR_0P125Hz
osr = OSR_X1  # temp and pressure
# A - no filter
f_code = "BP"
iir_filter_t = IIR_BYPASSED
iir_filter_p = IIR_BYPASSED
# B - filter coeff of 15 means that the measurement will get to ~96% of a step change in 50 samples (ie ~6s)
# f_code = "15"
# iir_filter_t = IIR_COEFF_15
# iir_filter_p = IIR_COEFF_15
# C - filter coeff of 31 means that the measurement will get to ~96% of a step change in 100 samples (ie ~12s)
# f_code = "31"
# iir_filter_t = IIR_COEFF_31
# iir_filter_p = IIR_COEFF_31
# D - filter coeff of 127 means that the measurement will get to ~96% of a step change in 400 samples (ie ~48s)
# f_code = "127"
# iir_filter_t = IIR_COEFF_31
# iir_filter_p = IIR_COEFF_31

#
measurement_interval_s = 60
measurement_number = 10

# default at power on is being in standby and re-assert defaults in case of re-run
dev.write_reg(REG_IIR_CONFIG, make_iir(iir_filter_p, iir_filter_t))
dev.write_reg(REG_OSR, make_osr(osr, osr))
dev.write_reg(REG_ODR, make_odr(pwr_mode=MODE_NORMAL, odr=odr))
# this forces a flush of the IIR filter, which is also done on a STANDBY->NORMAL transition (I'm doing this to guarantee the initial state for testing)
# NB THIS MIGHT NOT WORK - maybe have to force a STANDBY before NORMAL - TEST!!!!!!!!!!!!!!!!
dev.write_reg(REG_DSP_CONFIG, make_dsp_config(iir_flush_forced_en=True))

try:
    for rep in range(measurement_number):
        p_registers = dev.read_reg(REG_PRESSURE_XL, 3)  # auto-increments
        t_registers = dev.read_reg(REG_TEMP_L, 2)  # ignoring XL
        p = compute_pressure_hpa_reg(p_registers)
        t = compute_temp_c_reg(t_registers)
        print(f"Pressure={p:.2f}hPa \tTemp={t:.3f}C")

finally:
    # put back into standby (mostly for PPK testing)
    dev.write_reg(REG_ODR, make_odr(pwr_mode=MODE_STANDBY, odr=odr))

# TODO save to CSV and generate plots