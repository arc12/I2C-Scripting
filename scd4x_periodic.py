from interface import Adapter, I2CDevice, format_bin, format_hex
from SCD4x import *
from time import sleep, time, localtime, strftime

from os import makedirs, path
import pandas as pd

makedirs("output_scd4x", exist_ok=True)

adapter = Adapter()
adapter.check()

dev = I2CDevice(ADDR_7BIT, adapter)

dev.write_cmd16(CMD_GET_SERIAL_NO)
raw = dev.read(9)
ser = decode_serial(raw)
if ser is None:
    raise  Exception("Failed CRC on reading Serial No")
print("Serial No: ", ser)

# NB: for real use, as a manual calibration step:
# - ASC should be turned off (if not already off), temp offset to zerp, then persist to EEPROM
# - FSC completed.
# (temp offset handled at MCU level)

# reinit and temp offset must be in idle
dev.write_cmd16(CMD_STOP_PERIODIC)
sleep(0.5)  # 500ms cmd processing period
dev.write_cmd16(CMD_SET_ASC_ENABLED, parameters=crc_machine.append_crc(bytes([0, 0])))  # disable ASC
sleep(0.01)
dev.write_cmd16(CMD_SET_TEMP_OFFSET, parameters=crc_machine.append_crc(bytes([0, 0])))  # temp offset zero
# dev.write_cmd16(CMD_REINIT)
sleep(0.03)

# check offsets/ASC
print_config(dev)

# run code used to emit CSV file
run_code = "C3"

# Perform a series of wake + start, read values, stop. Use data-ready polling for new values (available 5s intervals)
results = list()
n_per_loop = 120  # number of readings  in inner loop - 5s delay for each
n_iterations = 1
inter_iteration_delay = 0
iteration = 0
while iteration < n_iterations:
    print(f"\n{run_code} >> {strftime('%H:%M:%S', localtime(time()))} <<")
    dev.write_cmd16(CMD_START_PERIODIC)  # observe readings to be "off" for a couple of minutes. ? due to device temp offset being progressively applied (see old ESP8266 notes)

    n = 0
    while n < n_per_loop:
        t0 = time()
        sleep(4)
        ready = False
        while not ready and time() - t0 < 6:
            sleep(0.1)
            dev.write_cmd16(CMD_GET_DATA_READY_STATUS)
            sleep(0.0015)  # 1ms command exec max time
            raw_ready = dev.read(3)
            if len(raw_ready) == 3:
                if not word_crc_check(raw_ready):
                    raise Exception("Failed CRC for CMD_GET_DATA_READY_STATUS")
                ready = not (raw_ready[0] & 0x07) + raw_ready[1] == 0  # If the least significant 11 bits of word[0] are 0 then data not ready else ready
            else:
                print("Probably a NACK checking data ready status, loop and try again")

        if not ready:
            raise Exception("Timed out on CMD_GET_DATA_READY_STATUS")
        ts = time()

        dev.write_cmd16(CMD_READ_MEASUREMENT)
        co2, temp, rh = raw_to_physical(dev.read(9))
        results.append([iteration, ts, strftime('%H:%M:%S', localtime(time())), co2, round(temp, 3), round(rh, 1)])
        # TODO add catch if CRC fail
        print(f"{co2}ppm, {temp:.3f}C, {rh:.1f}% (waited {ts - t0:.2f}s)")

        n+=1

    sleep(inter_iteration_delay)
    # u = input("Repeat? enter 'y'")
    # if u != "y":
    #     break
    iteration += 1
    if iteration < n_iterations:
        results.append([None] * 6)  # cause gaps in plot.

dev.write_cmd16(CMD_STOP_PERIODIC)
sleep(0.5)  # 500ms cmd processing period

df = pd.DataFrame(results, columns=["iteration", "timestamp", "time", "co2", "temp", "rh"])
# df.to_csv(path.join("output_scd4x", f"Periodic {run_code}.csv"))

do_plots(df, "Periodic", run_code, save=True, window=6)

