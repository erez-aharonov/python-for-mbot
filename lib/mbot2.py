import serial
import pandas as pd
import struct
import sys
from time import sleep
import re
import traceback
from lib.music import tones_table
from time import sleep


class Robot:
    def __init__(self, port="/dev/ttyUSB0", baud_rate=115200, debug=False):
        self._robot = serial.Serial(port, baud_rate)
        self._debug = debug
        sleep(0.05)

    def request_line_follower(self, port):
        extension_id = 1
        package = bytearray([0xff, 0x55, 0x4, extension_id, 0x1, 0x11, port])
        value = self._request_sensor_value(extension_id, package)
        return value

    def request_sound_sensor(self, port):
        sleep(0.01)
        extension_id = 1
        package = bytearray([0xff, 0x55, 0x4, extension_id, 0x1, 0x7, port])
        value = self._request_sensor_value(extension_id, package)
        sleep(0.01)
        return value

    def do_rgb_led_on_board(self, red, green, blue):
        index = 2
        self.do_rgb_led(0x7, 0x2, index, red, green, blue)

    def do_rgb_led(self, port, slot, index, red, green, blue):
        self._write_package(bytearray([0xff, 0x55, 0x9, 0x0, 0x2, 0x8, port, slot, index, red, green, blue]))

    def request_light_on_board(self):
        extension_id = 3
        return self._request_light(extension_id, 8)

    def _request_light(self, extension_id, port):
        package = bytearray([0xff, 0x55, 0x4, extension_id, 0x1, 0x3, port])
        value = self._request_sensor_value(extension_id, package)
        return value

    def request_ultrasonic_sensor(self, port):
        extension_id = 4
        package = bytearray([0xff, 0x55, 0x4, extension_id, 0x1, 0x1, port])
        value = self._request_sensor_value(extension_id, package)
        return value

    def do_buzzer(self, tone, time=0):
        buzzer = tones_table[tone]
        buzzer_as_short = self._short_to_bytes(buzzer)
        time_as_short = self._short_to_bytes(time)
        package = bytearray([0xff, 0x55, 0x7, 0x0, 0x2, 0x22] + buzzer_as_short + time_as_short)
        self._write_package(package)

    def do_move(self, left_speed, right_speed):
        left_speed_bytes = self._short_to_bytes(-left_speed)
        right_speed_bytes = self._short_to_bytes(right_speed)
        package = bytearray([0xff, 0x55, 0x7, 0x0, 0x2, 0x5] + left_speed_bytes + right_speed_bytes)
        self._write_package(package)

    def _request_sensor_value(self, extension_id, package):
        count = 0
        while count < 10:
            count += 1
            self._write_package(package)
            response_index, value = self._read_message_from_robot()
            if extension_id == response_index:
                break
        return value

    def _write_package(self, package):
        buf = []
        buf += [0, len(package)]
        for i in range(len(package)):
            buf += [package[i]]
        self._robot.write(buf)
        sleep(0.05)

    def _read_buffer_from_robot(self):
        try:
            count = 0
            buffer_as_hex = []
            while True:
                count += 1
                waiting_buffer_length = self._robot.inWaiting()
                buffer = [ord(self._robot.read()) for _ in range(waiting_buffer_length)]
                buffer_as_hex += list(map(hex, buffer))
                if self._debug:
                    print('buffer:', buffer_as_hex)
                message_as_numbers = self._get_last_long_message(buffer_as_hex)
                if message_as_numbers:
                    return message_as_numbers
                if count > 10000:
                    break
        except KeyError:
            traceback.print_exc(file=sys.stdout)
            print('buffer:', buffer_as_hex)
            self._robot.do_move(0, 0)
        return None

    def _get_last_long_message(self, buffer_as_hex):
        all_message_strings = re.findall('0xff-0x55.*?0xd-0xa', "-".join(buffer_as_hex))
        messages_list = list(map(lambda x: x.split('-'), all_message_strings))
        if self._debug:
            print('messages_list:', messages_list)
        df = pd.Series(messages_list).to_frame('message')
        df['len'] = df['message'].apply(len)
        relevant = df[df['len'] > 4]
        if relevant.shape[0]:
            message = relevant.iloc[-1]['message']
            message_as_numbers = list(map(lambda x: int(x, 0), message))
        else:
            message_as_numbers = None
        return message_as_numbers

    @staticmethod
    def _get_message_index(buffer):
        buffer_series = pd.Series(buffer)
        message_index = \
            (buffer_series[buffer_series.index[buffer_series == int('0xff', 0)] + 1] == int('0x55', 0)).index[-1] + 1
        return message_index

    @staticmethod
    def _convert_buffer_to_float(buffer):
        selected_buffer = buffer[:4]
        return struct.unpack('<f', struct.pack('4B', *selected_buffer))[0]

    @staticmethod
    def _convert_buffer_to_short(buffer):
        return struct.unpack('<h', struct.pack('2B', *buffer[:2]))[0]

    def _convert_buffer_to_number(self, buffer):
        number = None
        try:
            number_type_index = buffer[0]
            convert_dict = {
                2: self._convert_buffer_to_float,
                3: self._convert_buffer_to_short}
            # noinspection PyArgumentList
            if number_type_index not in convert_dict.keys():
                print(f'{number_type_index} not in convert_dict {convert_dict}')
                return None
            number = convert_dict[number_type_index](buffer[1:])
        except KeyError:
            traceback.print_exc(file=sys.stdout)
            buffer_as_hex += list(map(hex, buffer))
            print('buffer:', buffer_as_hex)
            self._robot.do_move(0, 0)
        return number

    def _read_message_from_robot(self):
        buffer = self._read_buffer_from_robot()
        if not buffer:
            return None, None
        message_start_index = self._get_message_index(buffer)
        response_index = buffer[message_start_index]
        value = self._convert_buffer_to_number(buffer[message_start_index + 1:])
        return response_index, value

    @staticmethod
    def _float_to_bytes(value):
        val = struct.pack("f", value)
        return list(val)

    @staticmethod
    def _short_to_bytes(value):
        val = struct.pack("h", value)
        return list(val)
