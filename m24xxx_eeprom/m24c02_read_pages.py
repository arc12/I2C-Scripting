# Read a whole page (16 bytes) from M24C02 device
# This is a complicated case because the most significant 2 address bit actually appear in the I2C device address

from interface import Adapter, I2CDevice, format_hex, bytes_to_int16
from M24C02 import *

adapter = Adapter()
adapter.check()

dev = I2CDevice(ADDR_7BIT, adapter)

for page_to_read in range(16):   # index to 16 byte chunk
    mem_addr = page_to_read << 4
    print(f"Page {page_to_read}, starts @ 0x{mem_addr:02x}")
    page_data = dev.read_mem_addr8(mem_addr, 16)
    print(page_data)
    print(format_hex(page_data))
    print()