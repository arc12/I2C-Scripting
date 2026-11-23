# Uses the MCP3425 ADC and a gated heater circuit (controlled by GPIO bit 0) to measure TGS2611 voltage divider output over a prolonged period of time.
# ADC running single-ended and configured with zero gain and at 15 SPS (which gives 16 bit precision).
# Data ready checked against the ready flag after a nominal 1/15s delay

from interface import Adapter, I2CDevice, format_hex, bytes_to_int16
from MCP342x import *
from time import sleep, time
from statistics import stdev, mean

adapter = Adapter()
adapter.check()

heater_active_high = True  # GPIO state to turn heater on. MIC2005A-1YM5 is active high, as is AP2112 etc LDO.
heater_duration_m = 5  # minutes
off_duration_m = 5
n_samples = 5  # number of ADC conversions. done at configured sample rate
n_measurements = 10  # number of on/off iterations

dev = I2CDevice(ADDR_7BIT, adapter)

try:
    iteration = 1
    while True:
        print(f"\n>> Iteration #{iteration}")
        print("Turning heater on")
        adapter.write_gpio(bytes([1 if heater_active_high else 0]))
        wait_dur = heater_duration_m * 60
        print(f"Waiting {wait_dur}s")
        sleep(wait_dur)

        burst = read_burst(dev, n_samples, CFG_SR_15, CFG_GAIN_1)
        mean_mv = mean(burst)
        sd_mv = stdev(burst)
        print(f"{mean_mv}mV (sd={sd_mv}mV)")

        print("Turning heater off")
        adapter.write_gpio(bytes([0 if heater_active_high else 1]))
        if iteration == n_measurements:
            break
        wait_dur = off_duration_m * 60
        print(f"Waiting {wait_dur}s")
        sleep(wait_dur)

        iteration += 1
finally:
    # attempt to turn heater off if exception (e.g. kbd interrupt) mid-cycle
    adapter.write_gpio(bytes([0 if heater_active_high else 1]))

print("END")

# TODO add save to CSV and make plot (with run-code)