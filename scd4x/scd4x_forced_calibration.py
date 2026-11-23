# Perform a forced calibration. Note datasheet 3.8.1
from interface import Adapter, I2CDevice
from SCD4x import *

adapter = Adapter()
adapter.check()

dev = I2CDevice(ADDR_7BIT, adapter)

dev.write_cmd16(CMD_GET_SERIAL_NO)
raw = dev.read(9)
ser = decode_serial(raw)
if ser is None:
    raise  Exception("Failed CRC on reading Serial No")
print("Serial No: ", ser)

forced_calibration(dev, 400)


