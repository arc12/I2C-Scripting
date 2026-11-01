# Trial run model for LP (30s sampling). Basically a specific case of the "_periodic" with an initial forced calibration

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
dev.write_cmd16(CMD_SET_ASC_ENABLED, parameters=crc_machine.append_crc(bytes([0, 0])))  # disable ASC
sleep(0.01)
# dev.write_cmd16(CMD_SET_TEMP_OFFSET, parameters=crc_machine.append_crc(bytes([0, 0])))  # temp offset zero
dev.write_cmd16(CMD_SET_TEMP_OFFSET, parameters=crc_machine.append_crc(bytes([2, 0x32])))  # temp offset 1.5C
# dev.write_cmd16(CMD_REINIT)
sleep(0.03)

# check offsets/ASC
print_config(dev)

# run code used to emit CSV file
run_code = "XY"

n_readings = 120  # number of readings after FSC. /2 to get minutes

results = list()

if forced_calibration(dev, 400, periodic_mode=CMD_START_LP, warmup_time_s=180):
    print(f"\n{run_code} >> {strftime('%H:%M:%S', localtime(time()))} <<")
    # SHOULD REALLY allow another ~3m burn-in period here if a temp offset is in effect, as it appears to be applied progressively after the START
    # but we actually have some remnant heating from the pre-FSC warm-up. IF, however T/RH not used prob just throw away 1st reading.
    dev.write_cmd16(CMD_START_LP)
    iteration = 0
    while iteration < n_readings:
        t0 = time()
        sleep(29)
        ready = False
        while not ready and time() - t0 < 31:
            sleep(0.5)  # was 0.1 to get more precise delay timings
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
        ts = round(time(), 0)

        dev.write_cmd16(CMD_READ_MEASUREMENT)
        co2, temp, rh = raw_to_physical(dev.read(9))
        results.append([iteration, ts, strftime('%H:%M:%S', localtime(ts)), co2, round(temp, 3), round(rh, 1)])
        # TODO add catch if CRC fail
        print(f"{co2}ppm, {temp:.3f}C, {rh:.1f}% (waited {ts - t0:.2f}s)")

        iteration+=1

    dev.write_cmd16(CMD_STOP_PERIODIC)

    df = pd.DataFrame(results, columns=["iteration", "timestamp", "time", "co2", "temp", "rh"])
    df.to_csv(path.join("output_scd4x", f"Trial LP {run_code}.csv"))

    do_plots(df, "Trial LP", run_code, save=True, window=10)

