from interface import Adapter, I2CDevice, format_hex, bytes_to_int16
from MCP3426 import *
from time import sleep

adapter = Adapter()
adapter.check()

dev = I2CDevice(ADDR_7BIT, adapter)

dev.write(bytes([make_config(mode_continuous=False, sample_rate=CFG_SR_15)]))  # could I start a conversion here too?

while True:
    dev.write(bytes([make_config(ready=True, mode_continuous=False, sample_rate=CFG_SR_15)]))  # setting rdy starts one-shot conversion
    # could poll the rdy flag in status (see datasheet 5.2) but for now just wait a safe period
    sleep (0.1)  # sample rates are 240, 60, or 15 SPS
    data_cfg = dev.read(3)
    mv = bytes_to_int16(data_cfg[:2], byteorder="big")[0] * 0.0625 # 62.5mV per LSB in 16 bit (15SPS)
    print(format_hex(data_cfg), f"\t/RDY flag = {data_cfg[2] >> 7}")
    print(f"{mv}mV")
    sleep(1)