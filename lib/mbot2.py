import serial
import pandas as pd
import struct
from time import sleep


class Robot:
    def __init__(self, port="/dev/ttyUSB0", baud_rate=115200):
        self._robot = serial.Serial(port, baud_rate)
        sleep(0.05)

    def request_line_follower(self, extension_id, port):
        package = bytearray([0xff, 0x55, 0x4, extension_id, 0x1, 0x11, port])
        value = self._request_sensor_value(extension_id, package)
        return value

    def do_rgb_led_on_board(self, index, red, green, blue):
        self.do_rgb_led(0x7, 0x2, index, red, green, blue)

    def do_rgb_led(self, port, slot, index, red, green, blue):
        self._write_package(bytearray([0xff, 0x55, 0x9, 0x0, 0x2, 0x8, port, slot, index, red, green, blue]))

    def request_light_on_board(self, extension_id):
        return self.request_light(extension_id, 8)

    def request_light(self, extension_id, port):
        package = bytearray([0xff, 0x55, 0x4, extension_id, 0x1, 0x3, port])
        value = self._request_sensor_value(extension_id, package)
        return value

    def request_ultrasonic_sensor(self, extension_id, port):
        package = bytearray([0xff, 0x55, 0x4, extension_id, 0x1, 0x1, port])
        value = self._request_sensor_value(extension_id, package)
        return value

    def _request_sensor_value(self, extension_id, package):
        while True:
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
        buffer = None
        count = 0
        while True:
            count += 1
            waiting_buffer_length = self._robot.inWaiting()
            if waiting_buffer_length <= 4:
                continue
            buffer = [ord(self._robot.read()) for _ in range(waiting_buffer_length)]
            if hex(buffer[0]) == '0xff' and \
                    hex(buffer[1]) == '0x55' and \
                    hex(buffer[-1]) == '0xa' and \
                    hex(buffer[-2]) == '0xd':
                print('buffer:', list(map(hex, buffer)))
                return buffer
            else:
                return None
        return buffer

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
        number_type_index = buffer[0]
        convert_dict = {
            2: self._convert_buffer_to_float,
            3: self._convert_buffer_to_short}
        # noinspection PyArgumentList
        number = convert_dict[number_type_index](buffer[1:])
        return number

    def _read_message_from_robot(self):
        buffer = self._read_buffer_from_robot()
        if not buffer:
            return None, None
        message_start_index = self._get_message_index(buffer)
        response_index = buffer[message_start_index]
        value = self._convert_buffer_to_number(buffer[message_start_index + 1:])
        return response_index, value
