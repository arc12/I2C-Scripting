from time import sleep, time
from interface import bytes_to_int16

ADDR_7BIT = 0x68  # should apply to both MCP3425/6

# MCP3426 has only one writable register - a single byte which should follow any device addr with R/W bit low
# I2C reads similarly have no register address to send, simply read 2 bytes after sending addr with R/W bit high
# To read the config register, read a 3rd byte (after conversion data)
# READ the datasheet concerning 16/15/14 bit formatting of the conversion data

def make_config(ready=0, channel=0, mode_continuous=1, sample_rate=0, gain=0):
    return (ready << 7) + (channel << 5) + (mode_continuous << 4) + (sample_rate << 2) + gain

CFG_CHANNEL_1 = 0
CFG_CHANNEL_2 = 1
CFG_SR_240 = 0  # 240 SPS -> 12 bit
CFG_SR_60 = 1  # 60 SPS -> 14 bit
CFG_SR_15 = 2  # 15 SPS -> 12 bit
CFG_GAIN_1 = 0
CFG_GAIN_2 = 1
CFG_GAIN_4 = 2
CFG_GAIN_8 = 3

sps_lookup = {
    CFG_SR_240: 240,
    CFG_SR_60: 60,
    CFG_SR_15: 15
}

mv_per_lsb = {
    CFG_SR_240: 1.0,
    CFG_SR_60: 0.250,
    CFG_SR_15: 0.0625  # 62.5mV per LSB in 16 bit (15SPS)
}

def read_mv_with_wait(dev, sample_rate, gain):
    # nominal delay followed by polling the rdy flag in status (see datasheet 5.2)
    # note that 15 SPS is nominal and the actual data rate range is 11-20.5 SPS, including auto-calibration, according to the data sheet
    sleep(1.0 / sps_lookup[sample_rate])
    while True:
        data_cfg = dev.read(3)
        if len(data_cfg) != 3:
            print("No data!")
            return None
        if data_cfg[2] & 0x70 == 0:  # ready flag (bit 7) is 1 until data ready
            break

    return bytes_to_mv(data_cfg, sample_rate, gain)

def read_oneshot(dev, sample_rate=0, gain=0):
    dev.write(bytes([make_config(ready=True, mode_continuous=False, sample_rate=CFG_SR_15, gain=gain)]))  # setting rdy starts one-shot conversion
    t_rdy_0 = time()
    mv = read_mv_with_wait(dev, sample_rate, gain)
    print(f"Waited {time() - t_rdy_0:.3f}s")

    return mv

    # print(format_hex(data_cfg), f"\t/RDY flag = {data_cfg[2] >> 7}")

def read_burst(dev, n_samples, sample_rate=0, gain=0):
    """
    Starts continuous running at the specified sample rate and reads n_samples before putting the ADC into one-shot mode
    (but a 0 written to /RDY bit, so I believe a 1-shot conversion will not occur)
    :param dev:
    :param n_samples:
    :param sample_rate:
    :param gain:
    :return: list of readings
    """
    results = list()
    n_read = 0

    dev.write(bytes([make_config(ready=False, mode_continuous=True, sample_rate=CFG_SR_15, gain=gain)]))
    t_rdy_0 = time()
    while n_read < n_samples:
        results.append(read_mv_with_wait(dev, sample_rate, gain))
        n_read += 1

    print(f"Waited {(time() - t_rdy_0) /  n_samples:.3f}s")

    dev.write(bytes([make_config(ready=False, mode_continuous=False, sample_rate=CFG_SR_15, gain=gain)]))

    return results


def bytes_to_mv(data, sample_rate, gain):
    """
    PRESUMES only positive input voltages (ie single end with In- grounded.
    :param data:
    :param sample_rate:
    :param gain:
    :return:
    """
    factor = mv_per_lsb[sample_rate] / 2**gain
    return bytes_to_int16(data[:2], byteorder="big")[0] * factor