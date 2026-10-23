# Reads settable parameters, giving raw hex values incl CRC
from interface import Adapter, I2CDevice, format_bin, format_hex
from SCD4x import *
from time import sleep

adapter = Adapter()
adapter.check()

dev = I2CDevice(ADDR_7BIT, adapter)

dev.write_cmd16(CMD_GET_SERIAL_NO)
raw = dev.read(9)
ser = decode_serial(raw)
if ser is None:
    raise  Exception("Failed CRC on reading Serial No")
print("Serial No: ", ser)

# it appears that after POR, the ambient pressure returns as 0000. A manual set followed by a read gives expected value
# p = 101000
# p_msb, p_lsb = p // 25600, (p // 100) % 256
# dev.write_cmd16(CMD_SET_AMBIENT_PRESSURE, parameters=crc_machine.append_crc(bytes([p_msb, p_lsb])))
# sleep(0.1)

print_config(dev)