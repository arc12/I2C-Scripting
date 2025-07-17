ADDR_7BIT = 0x44

# commands
CMD_MEAS_HP = 0xFD  # start high repeatability measurement - typ 6.9ms, max 8.3ms
CMD_MEAS_MP = 0xF6  # start medium repeatability measurement - typ 3.7ms, max 4.5ms
CMD_MEAS_LP = 0xE0  # start low repeatability measurement - typ 1.3ms, max 1.6ms
CMD_READ_SERIAL = 0x89  # serial no
CMD_SOFT_RESET = 0x94  # soft reset max time 1ms
# heater activation commands omitted

from crc import CRC8_x31

def compute_rh(bytes_with_crc):
    """
    Checks CRC and then computes RH
    :param bytes_with_crc: three bytes comprising the 16 bits of raw count data + 8 bits CRC in the order obtained via I2C
    :return: RH or None if CRC failed
    """
    rh = None

    crc_machine = CRC8_x31()
    if crc_machine.complete_digest(bytes_with_crc[:2]) == bytes_with_crc[2]:
        rh = round(-6 + 125 * (bytes_with_crc[1] + bytes_with_crc[0] * 256) / 65535, 1)
    return rh

def compute_temp(bytes_with_crc):
    """
    Checks CRC and then computes temp
    :param bytes_with_crc: three bytes comprising the 16 bits of raw count data + 8 bits CRC in the order obtained via I2C
    :return: RH or None if CRC failed
    """
    temp = None

    crc_machine = CRC8_x31()
    if crc_machine.complete_digest(bytes_with_crc[:2]) == bytes_with_crc[2]:
        temp = round(-45 + 175 * (bytes_with_crc[1] + bytes_with_crc[0] * 256) / 65535, 2)
    return temp

def decode_serial(bytes_with_crc):
    """
    Checks serial against CRC
    :param bytes_with_crc: All 6 bytes of the response to the read serial command, which comprises two groups of (2 bytes + crc)
    :return: Serial as hex string or None if CRC fails
    """
    ser = None
    if len(bytes_with_crc) == 0:
        raise Exception("Zero bytes passed to decode_serial()")
    crc_machine = CRC8_x31()
    if crc_machine.complete_digest(bytes_with_crc[:2]) == bytes_with_crc[2]:
        if crc_machine.complete_digest(bytes_with_crc[3:5]) == bytes_with_crc[5]:
            # actual byte ordering in serial no is not known!
            ser = hex(((bytes_with_crc[4] * 256 + bytes_with_crc[3]) * 256 + bytes_with_crc[1]) * 256 + bytes_with_crc[0])
    return ser