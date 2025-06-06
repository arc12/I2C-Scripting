from interface import Adapter, I2CDevice, format_hex, bytes_to_int16
from DEVICE_STUFF import *
from time import sleep

adapter = Adapter()
adapter.check()

dev = I2CDevice(ADDR_7BIT, adapter)