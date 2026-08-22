# Interface to the SC18IM704 UART-to-I2C adapter

import serial
from settings import *

# I2C Clock Rates are set via a pair of registers - see datasheet 9.2.5 - these are the lower register values matching kHz speeds
I2C_SPEED_375 = 5  # fastest I2C speed supported
I2C_SPEED_208 = 9
I2C_SPEED_99 = 19  # this is the hardware default
I2C_SPEED_7_4 = 255

# >>>>> I2C Device Read/Write Operations  <<<<<<<<<<<<
class I2CDevice:
    def __init__(self, i2c_addr, adapter):
        self.i2c_addr = i2c_addr  # 7 bit address
        self.adapter = adapter

    def write(self, payload):
        """
        Sends START + ADDR_W + LENGTH + PAYLOAD + STOP  (NB this is the message to the interface, not the final I2C message, which is just the Addr + payload)
        :param payload: bytes to send
        :return:
        """
        m = b'S' + bytes([self.i2c_addr << 1, len(payload)]) + payload + b'P'
        self.adapter.serial.open()
        self.adapter.serial.write(m)
        self.adapter.serial.close()

    def write_reg(self, reg, value):
        """

        :param reg: typically set as hex literal
        :param value: value of register, integer 0-255
        :return:
        """
        self.write(bytes([reg, value]))

    def write_reg16(self, reg16, value, bigendian=True):
        """

        :param reg16: typically set as hex literal. 16 bit value
        :param value: value of register, integer 0-255
        :param bigendian: if True, the MSB of the command is sent first
        :return:
        """
        msb = reg16 >> 8
        lsb = reg16 & 0xff
        if bigendian:
            self.write(bytes([msb, lsb, value]))
        else:
            self.write(bytes([lsb, msb, value]))

    def write_cmd(self, cmd):
        """
        Just send single byte over I2C = slave device command
        :param cmd: typically set as hex literal
        :return:
        """
        self.write(bytes([cmd]))

    def write_cmd16(self, cmd16, bigendian=True):
        """
        Just send double byte over I2C = slave device command
        :param cmd16: typically set as hex literal
        :param bigendian: if True, the MSB of the command is sent first
        :return:
        """
        msb = cmd16 >> 8
        lsb = cmd16 & 0xff
        if bigendian:
            self.write(bytes([msb, lsb]))
        else:
            self.write(bytes([lsb, msb]))

    def write_read(self, write_payload, read_bytes=1):
        was_open = self.adapter.serial.is_open
        if not was_open:
            self.adapter.serial.open()
        m = b'S' + bytes([self.i2c_addr << 1, len(write_payload)]) + write_payload  # no STOP
        self.adapter.serial.write(m)
        m = b'S' + bytes([(self.i2c_addr << 1) + 1, read_bytes]) + b'P'
        self.adapter.serial.write(m)
        r = self.adapter.serial.read(read_bytes)
        if not was_open:
            self.adapter.serial.close()

        return r

    def read(self, read_len=1):
        """
        Basic read. Maybe there is no register to address, or the context of reading was previously set
        :param read_len:
        :return:
        """
        self.adapter.serial.open()

        m = b'S' + bytes([(self.i2c_addr << 1) + 1, read_len]) + b'P'
        self.adapter.serial.write(m)
        r = self.adapter.serial.read(read_len)

        self.adapter.serial.close()

        return r


    def read_reg(self, reg, read_len=1):
        """

        :param reg: integer, typically given as a hex literal
        :param read_len: optional number of bytes. slave device is assumed to auto-inc register
        :return:
        """
        return self.write_read(bytes([reg]), read_len)

    def read_reg16(self, reg16, read_len=1, bigendian=True):
        """

        :param reg16: 16 bit register, typically given as a hex literal
        :param read_len: optional number of bytes. slave device is assumed to auto-inc register
        :param bigendian: if True, the MSB of the command is sent first
        :return:
        """
        msb = reg16 >> 8
        lsb = reg16 & 0xff
        if bigendian:
            return self.write_read(bytes([msb, lsb]), read_len)
        else:
            return self.write_read(bytes([lsb, msb]), read_len)

    def read_mem_addr8(self, addr, read_len=1):
        """
        Read from a memory device with an 8 bit address. Functionally the same as read_reg() but included for consonance with the function name
        for a 16 bit address
        :param addr:
        :return:
        """
        return self.write_read(bytes([addr]), read_len)

    def read_reg_repeated(self, n_repeats, reg, read_len=1, convert_fn=None):
        """
        Just like read_reg, but opens the serial, performs n_repeats, then closes the serial
        (rather than opening and closing each time. This can double the max throughput.
        :param n_repeats:
        :return: list of returned bytes
        """
        r_list = list()
        self.adapter.serial.open()
        for i in range(n_repeats):
            if convert_fn is None:
                r_list.append(self.write_read(bytes([reg]), read_len))
            else:
                r_list.append(convert_fn(self.write_read(bytes([reg]), read_len)))
        self.adapter.serial.close()
        return r_list

    def dump_reg(self, reg_list):
        """
        Reads a set of registers (8 bit) and prints the values in hex and binary
        :param reg_list: a list of tuples, where the 1st of the tuples is the reg name and the second its address
        :return: None
        """
        self.adapter.serial.open()

        max_name_len = max([len(v[0]) for v in reg_list])  # used to ensure column alignment in output
        output_width = max_name_len + 27
        head_l = '=' * ((output_width - 15) // 2)
        head_r = '=' * (output_width - 15 - len (head_l))
        print(head_l, "Register Dump", head_r)
        for reg_name, reg in reg_list:
            reg_val = self.write_read(bytes([reg]))[0]
            print(f"{reg_name} (0x{reg:02x}): {' ' * (max_name_len - len(reg_name))}0x{reg_val:02x} = 0b{format_bin(reg_val)}")
        print('=' * output_width)
        print()
        self.adapter.serial.close()


class Adapter:
    def __init__(self, i2c_speed=None):
        """

        :param i2c_speed: see set_i2c_speed(). If None then the hardware default is used, which is documented as 0x13 ie 99kHz
        """
        self.serial = serial.Serial(PORT, BAUD, timeout=READ_TIMEOUT)
        self.serial.close()

        # Check if we can communicate on the requested baud rate. If not, presume that the device is freshly powered up, so will be at 9600
        # So start with that and change to the baud rate in settings
        if not self.check():
            print("Trying to change baud rate.")
            self.serial.close()
            self.serial.baudrate = 9600
            self.check()  # does open()
            brg_word = 7372800 // BAUD - 16
            brg0 = brg_word % 256  # internal reg 00
            brg1 = brg_word // 256  # internal reg 01. must be written second, which actually makes the change
            m = b'W' + bytes([0x00, brg0, 0x01, brg1]) + b'P'
            self.serial.open()
            self.serial.write(m)
            self.serial.close()
            self.serial.baudrate = BAUD
            # If things are still failing then the SC18IM704 must have already had its baud rate changed, but to different value
            if not self.check(do_print=False):
                raise Exception("Failed to match baud rate to SC18IM704 - power cycle it then try again")
        self.set_i2c_speed(i2c_speed)

    # >>>>>>>> SC18IM704 Internal <<<<<<<<<<<
    def check(self, do_print=True):
        # Get the SC18IM704 version string as a simple start-up test
        # Response should be 16 bytes long: "SC18IM704 1.0.2" + null terminator
        self.serial.open()
        self.serial.write(b'VP')
        r = self.serial.read(16)
        self.serial.close()
        if r != b'':
            if do_print:
                print(f"Interface: {r}")
            return True
        else:
            print(f"Failed to communicate (baud = {self.serial.baudrate})")
            return False

    def set_i2c_speed(self, i2c_speed):
        """
        Sets I2C clock rate (if param is not None) and then reads back current value
        :param i2c_speed: constant of form I2C_SPEED_* or None to skip setting and just read current value
        :return:
        """
        self.serial.open()
        if i2c_speed is not None:
            self.serial.write(b'W' + bytes([0x07, i2c_speed, 0x08, 0]) + b'P')
        self.serial.write(b'R' + bytes([0x07, 0x08]) + b'P')
        r = self.serial.read(2)
        clk_rate_khz = int(round(1875 / (r[0] + 256 * r[1]), 0))
        print(f"I2C Clock Rate = {clk_rate_khz}kHz")
        self.serial.close()

    # >>>>>>>> GPIO Operations <<<<<<<<<<
    def read_gpio(self):
        already_open = self.serial.is_open
        if not already_open:
            self.serial.open()
        self.serial.write(b'IP')
        r = self.serial.read(1)
        if not already_open:
            self.serial.close()
        return r[0]

    def check_gpio_bit(self, bit_index):
        gpios = self.read_gpio()
        return bool(gpios & (1<<bit_index))

# >>>>>>> misc
def format_hex(bytes_to_print, bytes_per_sep=1):
    return f"0x{bytes.hex(bytes_to_print, sep=' ', bytes_per_sep=bytes_per_sep)}"

def format_bin(byte_to_print):  # SINGLE byte arg
    # TODO make flexible split options
    bits_for_byte = "{:08b}".format(byte_to_print)
    return bits_for_byte[:4] + " " + bits_for_byte[4:]

def bytes_to_int16(raw, byteorder="little"):
    """
    Takes a bytes object and uses successive pairs in LH (byteorder="little") or HL (byteorder="big") order
    to prepare a list of signed integers.
    :param raw:
    :return:
    """
    int16 = list()
    for ix in range(0, len(raw), 2):
        int16.append(int.from_bytes(raw[ix:ix+2], byteorder=byteorder, signed=True))
    return int16
