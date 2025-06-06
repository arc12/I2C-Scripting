ADDR_7BIT = 0x68

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