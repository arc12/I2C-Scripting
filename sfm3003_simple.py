from interface import Adapter, I2CDevice, format_bin, format_hex, bytes_to_int16, I2C_SPEED_7_4, I2C_SPEED_99, I2C_SPEED_375
from SFM3003 import *
from time import sleep, time, localtime, strftime

adapter = Adapter()
adapter.check()

adapter.set_i2c_speed(I2C_SPEED_99)

dev = I2CDevice(ADDR_7BIT_CE, adapter)

dev.write_cmd16(CMD_READ_IDENTIFIER)
raw = dev.read(18)
ser = decode_serial(raw)
if ser is None:
    raise  Exception("Failed CRC on reading Serial No")
print("Serial No: ", ser)  # digits are yywwnnnnnn, where yy = year, ww = week in year, nnnnnn = sequential within week

# Check the temperature from start. May be best way to get an air temp, minimising the heating effect inherent in the method
# Datasheet says 12ms delay before 1st reading available + another 18ms until readings stabilised after start continuous measurements
# The internal sampling interval is ~0.5ms.
# OBSERVATION: there is about a 0.2C rise between the first available reading and the stabilised temp, which occurs about 20ms later
# t0 = time()
# t = t0
# dev.write_cmd16(CMD_START_CONTINUOUS_AIR)
# # sleep(0.005)
# while t - t0 < 0.1:
#     t = time()
#     raw = dev.read(6)
#     print(f"{(t - t0) * 1000}ms, Temp = {compute_temp(raw[3:]):.2f}C")
#
# dev.write_cmd16(CMD_STOP)
#
# exit(0)


# Perform a series of wake + start, read values, stop, sleep, with wait periods in between.
# The internal sampling interval is ~0.5ms
while (True):
    print(f"\n>> {strftime('%H:%M:%S', localtime(time()))} <<")
    dev.write_cmd16(CMD_START_CONTINUOUS_AIR)
    sleep(0.03)  # 30ms warm up time before good measurements available

    # perform a dummy read to remove the warm-up average
    raw = dev.read(9)  # do I need 9 bytes?
    print(format_hex(raw, 3))

    sleep(0.05)  # allow an averaging period of 100 samples. Exponential smoothing kicks in after 64ms.

    raw = dev.read(9)  # raw flow + temp
    print(format_hex(raw, 3))

    print(f"Status word: 0b{format_bin(raw[6])} {format_bin(raw[7])}")

    dev.write_cmd16(CMD_STOP)  # this is required before any commands can be sent (not allowed during continuous measurement)
    sleep(0.1)  # a bit of time to measure current consumption in stopped state

    flow_slm = compute_flow(raw[:3])
    print(f"Flow = {flow_slm:.2f} SFM = {compute_flow_mps(flow_slm):.2f}m/s, Temp = {compute_temp(raw[3:]):.2f}C")
    dev.write_cmd16(CMD_SLEEP)
    sleep(1)

    # wake-up requires a valid I2C address with the R/W bit low (write)
    # the doc says wakeup should take about 16ms but it also says the sensor should be polled.
    dev.write_cmd16(CMD_READ_IDENTIFIER)
    sleep(0.02)
