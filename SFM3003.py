ADDR_7BIT_CE = 0x2D

# commands
CMD_START_CONTINUOUS_AIR = 0x3608
CMD_STOP = 0x3FF9
CMD_CONFIGURE_AVERAGING = 0x366A  # follow by 1 byte, 0 argument (default) is average until read
CMD_SOFT_RESET = 0x0006
CMD_SLEEP = 0x3677
CMD_READ_IDENTIFIER = 0xE102  # after which read 18 bytes with 16 bit data + 8 bit CRC units

# scale factors. physical value = (raw output - offset) / scale-factor
# Those for the flow can be read out via I2C, which would be applicable for a gas mixture other than "air",
# but fixed values are given in the datasheet for:
SCALE_AIR_CE = 120  # SLM^-1
OFFSET_AIR_CE = -12288
SCALE_TEMP = 200  # C^-1
OFFSET_TEMP = 0

from crc import CRC8_x31
from interface import bytes_to_int16


def compute_flow(bytes_with_crc):
    """
    Returns flow in SFM, after checking CRC
    :param bytes_with_crc: two flow bytes + crc as read out following a continuous measurement command
    :return: SFM or None if CRC failed
    """
    flow = None

    crc_machine = CRC8_x31()

    if crc_machine.complete_digest(bytes_with_crc[:2]) == bytes_with_crc[2]:
        raw_flow = bytes_to_int16(bytes_with_crc[:2], byteorder="big")[0]
        flow = (raw_flow - OFFSET_AIR_CE) /  SCALE_AIR_CE
    return flow

def compute_flow_mps(flow_sfm):
    """
    Uses calibration equations given in International Journal of Speleology, 53 (1), 63-73
    to obtain a flow in metres per second from the SFM obtained by compute_flow()
    :param flow_sfm:
    :return:
    """
    # The paper gives a two-range conversion
    abs_flow_sfm = abs(flow_sfm)
    if abs_flow_sfm <= 6:  # <= ~1.2m/s - we'll most likely be in this range
        abs_flow_mps = -0.0243 * abs_flow_sfm * abs_flow_sfm + 0.3422 * abs_flow_sfm
    else:
        abs_flow_mps = -0.0014 * abs_flow_sfm * abs_flow_sfm + 0.1828 * abs_flow_sfm

    # restore sign
    return abs_flow_mps if flow_sfm > 0 else -abs_flow_mps

def compute_temp(bytes_with_crc):
    """
    Returns temp in C, after checking CRC
    :param bytes_with_crc: two flow bytes + crc = 2nd group of 3 bytes read out following a continuous measurement command
    :return: temp or None if CRC failed
    """
    flow = None

    crc_machine = CRC8_x31()

    if crc_machine.complete_digest(bytes_with_crc[:2]) == bytes_with_crc[2]:
        raw_flow = bytes_to_int16(bytes_with_crc[:2], byteorder="big")[0]
        flow = (raw_flow - OFFSET_TEMP) /  SCALE_TEMP
    return flow

def decode_serial(bytes_with_crc):
    """
    Takes all 18 bytes available from a CMD_READ_IDENTIFIER command and extracts the serial number (discards the product number), while checking the CRCs
    :param bytes_with_crc:
    :return: 64 bit serial number or None if any CRC failed
    """

    sn = 0

    crc_machine = CRC8_x31()

    for chunk_index in range(6, 16, 3):
        if crc_machine.complete_digest(bytes_with_crc[chunk_index:chunk_index + 2]) != bytes_with_crc[chunk_index + 2]:
            return None
        sn = (sn << 16) + (bytes_with_crc[chunk_index] << 8) + bytes_with_crc[chunk_index + 1]

    return sn