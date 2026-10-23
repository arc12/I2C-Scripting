# Periodic with changing atmos pressure (simulated steps)
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

# reinit and temp offset must be in idle
dev.write_cmd16(CMD_STOP_PERIODIC)
sleep(0.5)  # 500ms cmd processing period
dev.write_cmd16(CMD_SET_TEMP_OFFSET, parameters=crc_machine.append_crc(bytes([0, 0])))
# dev.write_cmd16(CMD_REINIT)
sleep(0.03)

# check offset
dev.write_cmd16(0x2318)
sleep(0.01)
print("Raw temp offset", format_hex(dev.read(3)))

# "burn-in"
print("Burn-in - wait!")
dev.write_cmd16(CMD_START_PERIODIC)
sleep(30)
# clear buffer
dev.write_cmd16(CMD_READ_MEASUREMENT)
dev.read(9)

# run code used to emit CSV file
run_code = "A"


# Perform a series of wake + start, read values, stop. Use data-ready polling for new values (available 5s intervals)
results = list()
n_per_loop = 12  # number of readings  in inner loop - 5s delay for each
n_iterations = 2
iteration = 0
start_pressure = 100000
del_pressure = 20000  # per iteration
while iteration < n_iterations:
    print(f"\n{run_code} >> {strftime('%H:%M:%S', localtime(time()))} <<")
    p = start_pressure + del_pressure * iteration
    p_msb, p_lsb = p // 25600, (p // 100) % 256
    # this can be used whether or not the periodic measurements are running
    dev.write_cmd16(CMD_SET_AMBIENT_PRESSURE, parameters=crc_machine.append_crc(bytes([p_msb, p_lsb])))

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
        results.append([p, ts, strftime('%H:%M:%S', localtime(time())), co2, round(temp, 3), round(rh, 1)])
        # TODO add catch if CRC fail
        print(f"{co2}ppm, {temp:.3f}C, {rh:.1f}% (waited {ts - t0:.2f}s)")

        n+=1

    iteration += 1
    if iteration < n_iterations:
        results.append([None] * 6)  # cause gaps in plot.

dev.write_cmd16(CMD_STOP_PERIODIC)
sleep(0.5)  # 500ms cmd processing period

run_type = "Pressure"
df = pd.DataFrame(results, columns=["iteration", "timestamp", "time", "co2", "temp", "rh"])
df.to_csv(path.join("output_scd4x", f"{run_type} {run_code}.csv"))

do_plots(df, run_type, run_code, save=True)

