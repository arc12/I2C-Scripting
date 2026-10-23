from crc import CRC8_x31

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.io import write_html, write_image
from os import path
from time import sleep
from interface import format_hex

# same for SCD40/1/3
ADDR_7BIT = 0x62

# SCD4x works with "commands" rather than registers. Incomplete set here:
# Basic commands - datasheet 3.6
CMD_START_PERIODIC = 0x21B1
CMD_STOP_PERIODIC = 0x3F86
CMD_READ_MEASUREMENT = 0xEC05
# Compensation (incomplete) - datasheet 3.7
CMD_SET_AMBIENT_PRESSURE = 0xE000
CMD_GET_AMBIENT_PRESSURE = 0xE000
CMD_SET_TEMP_OFFSET = 0x241D
CMD_GET_TEMP_OFFSET = 0x2318
# Calibration (incomplete) - datasheet 3.8
CMD_FORCED_CALIBRATION = 0x362F
CMD_SET_ASC_ENABLED = 0x2416
CMD_GET_ASC_ENABLED = 0x2313
# Low Power - datasheet 3.9
CMD_START_LP = 0x21AC
CMD_GET_DATA_READY_STATUS = 0xE4B8
# Advanced (incomplete) - datasheet 3.10
CMD_GET_SERIAL_NO = 0x3682
CMD_PERFORM_SELF_TEST = 0x3639
CMD_REINIT = 0x3646
# Single shot (incomplete) - datasheet 3.11
CMD_MEASURE_SINGLE_SHOT = 0x219D
CMD_POWER_DOWN = 0x36E0
CMD_WAKE_UP = 0x36F6

crc_machine = CRC8_x31()

def word_crc_check(bytes_with_crc, offset=0):
    digest, received = crc_machine.complete_digest(bytes_with_crc[offset:offset + 2]), bytes_with_crc[offset + 2]
    if digest != received:
        print(f"CRC fail: computed 0x{digest:X02} got 0x{received:X02}")
    return digest == received

def decode_serial(bytes_with_crc):
    """
    Takes all 9 bytes available from a CMD_GET_SERIAL_NO command and extracts the serial number while checking the CRCs
    :param bytes_with_crc:
    :return: 32 bit serial number or None if any CRC failed
    """

    sn = 0
    for chunk_index in range(0, 6, 3):
        if not word_crc_check(bytes_with_crc, offset=chunk_index):
            return None
        sn = (sn << 16) + (bytes_with_crc[chunk_index] << 8) + bytes_with_crc[chunk_index + 1]

    return sn

def raw_to_physical(raw_val):  # TODO add CRC like SFM3003
    """
    Takes 9 bytes of I2C response to CMD_READ_MEASUREMENT and returns a tuple for CO2/ppm, T/C, RH/%.
    DOES NOT perform CRC checks (which are single bytes with each raw reading)
    :param raw_val:
    :return:
    """
    co2 = (raw_val[0] << 8) + raw_val[1]
    temp_raw = (raw_val[3] << 8) + raw_val[4]
    rh_raw = (raw_val[6] << 8) + raw_val[7]
    temp = -45 + 175 * temp_raw / 65535
    rh = 100 * rh_raw / 65535

    return co2, temp, rh

def do_plots(df, run_type, run_code, save=False, window=None):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.co2, text=df.iteration, name="CO2"), secondary_y=False)
    if window is not None:
        fig.add_trace(go.Scatter(x=df.timestamp, y=df.co2.rolling(window).mean().round(1), text=df.iteration, name="CO2 MA", line={"dash": "dash", "width": 1}), secondary_y=False)
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.temp, text=df.iteration, name="T"), secondary_y=True)
    fig.update_layout(title_text=f"SCD4x {run_type} Run-code:{run_code}")
    fig.update_xaxes(title_text="Time", unifiedhovertitle_text=None)
    fig.update_yaxes(title_text="CO2/ppm", secondary_y=False)
    fig.update_yaxes(title_text="Temp/C", secondary_y=True)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(tickvals=df.timestamp, ticktext=df.time)
    fig.show()
    if save:
        write_html(fig, path.join("output_scd4x", f"{run_type} {run_code}.html"))
        write_image(fig, path.join("output_scd4x", f"{run_type} {run_code}.png"), format="png")

def print_config(dev):
    for cmd, label in [  # all responses word + CRC
        (CMD_GET_TEMP_OFFSET, "temp offset"),
        (CMD_GET_AMBIENT_PRESSURE, "ambient pressure"),
        (CMD_GET_ASC_ENABLED, "ASC enabled"),
        (0x202F, "sensor variant")
    ]:
        dev.write_cmd16(cmd)
        # dev.read_reg16(cmd)
        sleep(0.01)
        response = dev.read(3)
        if len(response) == 3:
            print(f"{label} (0x{cmd:02X}): {format_hex(response, 3)} (CRC OK={crc_machine.is_valid(response)})")
        else:
            print(f"{label}: NACK")

if __name__ == "__main__":
    print(raw_to_physical(bytes([0x01, 0xF4, 0x33, 0x66, 0x67, 0xA2, 0x5E, 0xB9, 0x3C])))