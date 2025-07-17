from interface import Adapter, I2CDevice, format_hex, bytes_to_int16
from SHT40 import *
from time import sleep

adapter = Adapter()
adapter.check()

dev = I2CDevice(ADDR_7BIT, adapter)

dev.write_cmd(CMD_READ_SERIAL)
raw = dev.read(6)
ser = decode_serial(raw)
if ser is None:
    raise  Exception("Failed CRC on reading Serial No")
print("Serial No: ", ser)

dev.write_cmd(CMD_MEAS_LP)
sleep(0.002)
raw = dev.read(6)
print(f"RH={compute_rh(raw[3:])}%, Temp={compute_temp(raw[:3])}C")