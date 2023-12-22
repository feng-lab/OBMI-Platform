import json
import time

import cv2

class CameraController:
    '''
    Interface for camera controlling
    '''
    def change_gain(self, cap:cv2.VideoCapture, gain:int):
        raise NotImplementedError

    def change_fps(self, cap:cv2.VideoCapture, fps:int):
        raise NotImplementedError

    def change_focus(self, cap:cv2.VideoCapture, focus:int):
        raise NotImplementedError

    def change_LED(self, cap:cv2.VideoCapture, led_value:int):
        raise NotImplementedError

    def change_exposure(self, cap:cv2.VideoCapture, exposure:int):
        raise NotImplementedError

    def init_args(self, cap:cv2.VideoCapture):
        raise NotImplementedError


class SimpleCameraController(CameraController):
    def change_gain(self, cap, gain):
        cap.set(cv2.CAP_PROP_GAIN, gain)

    def change_fps(self, cap, fps):
        cap.set(cv2.CAP_PROP_FPS, fps)

    def change_focus(self, cap, focus):
        cap.set(cv2.CAP_PROP_FOCUS, focus)

    def change_exposure(self, cap:cv2.VideoCapture, exposure:int):
        cap.set(cv2.CAP_PROP_BRIGHTNESS, exposure)

    def change_LED(self, cap, led_value):
        # no led interface
        pass

    def init_args(self, cap):
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        gain = cap.get(cv2.CAP_PROP_GAIN)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        focus = cap.get(cv2.CAP_PROP_FOCUS)
        led = 0
        exposure = cap.get(cv2.CAP_PROP_BRIGHTNESS)

        args = {
            'width': width,
            'height': height,
            'gain': gain,
            'fps': fps,
            'focus': focus,
            'led': led,
            'exposure': exposure
        }

        return args

class MiniscopeController(CameraController):
    def __init__(self, config_path):

        self.loadConfig(config_path)

        self.gain_display_list = [1, 2, 3]
        self.gain_value_list = self.control_config['gain']['outputValues']
        self.fps_display_list = self.control_config['frameRate']['displayTextValues']
        self.fps_value_list = self.control_config['frameRate']['outputValues']

    def loadConfig(self, config_path):
        with open(config_path) as f:
            js = json.load(f)

        self.control_config = js['Miniscope_V4_BNO']['controlSettings']
        self.init_config = js['Miniscope_V4_BNO']['initialize']


    def init_args(self, cap):
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 608)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 608)

        self.init_commands(cap)

        args = {
            'width': 608,
            'height': 608,
            'gain': 1,
            'fps': 20,
            'focus': 0,
            'led': 0,
            'exposure': 0
        }

        return args

    def init_commands(self, cap):
        input_list = [0xC0, 0x1F, 0b00010000]
        self.sendCommands(input_list, cap)

        input_list = [0xB0, 0x05, 0b00100000]
        self.sendCommands(input_list, cap)

        for config in self.init_config:
            packet = self.parseConfig(config, 0)
            self.sendCommands(packet, cap)

    def parseConfig(self, config, value):
        packet = []

        v = config['addressW']
        if 'b' in v:
            packet.append(int(v, 2))
        else:
            packet.append(int(v, 16))

        for i in range(int(config['regLength'])):
            packet.append(int(config['reg' + str(i)], 16))

        for i in range(int(config['dataLength'])):
            v = config['data' + str(i)]

            if isinstance(v, int):
                packet.append(v)
                continue

            if v == "valueH":
                packet.append((value >> 8) & 0xFF)
                continue

            if v == "valueL":
                packet.append(value & 0xFF)
                continue

            if v == "value":
                packet.append(value)
                continue

            if 'b' in v:
                packet.append(int(v, 2))
            else:
                packet.append(int(v, 16))

        return packet

    def sendCommands(self, packet, cap):
        if len(packet) < 6:
            tmp = packet[0]
            tmp |= (len(packet) & 0xFF) << 8
            for i in range(1, len(packet)):
                tmp |= packet[i] << (8 * (i + 1))

            ret_list = [tmp & 0x00000000FFFF, (tmp & 0x0000FFFF0000) >> 16, (tmp & 0XFFFF00000000) >> 32]

            cap.set(cv2.CAP_PROP_CONTRAST, ret_list[0])
            cap.set(cv2.CAP_PROP_GAMMA, ret_list[1])
            cap.set(cv2.CAP_PROP_SHARPNESS, ret_list[2])
            time.sleep(0.001)

        elif len(packet) == 6:
            tmp = packet[0] | 0x01
            for i in range(1, len(packet)):
                tmp |= packet[i] << (8 * i)

            ret_list = [tmp & 0x00000000FFFF, (tmp & 0x0000FFFF0000) >> 16, (tmp & 0XFFFF00000000) >> 32]

            cap.set(cv2.CAP_PROP_CONTRAST, ret_list[0])
            cap.set(cv2.CAP_PROP_GAMMA, ret_list[1])
            cap.set(cv2.CAP_PROP_SHARPNESS, ret_list[2])
            time.sleep(0.001)

        else:
            print('Illegal packet length')


    def change_gain(self, cap, gain):
        value = self.gain_value_list[self.gain_display_list.index(gain)]
        gain_config = self.control_config['gain']
        commands_configs = gain_config['sendCommand']
        for command in commands_configs:
            packet = self.parseConfig(command, value)
            self.sendCommands(packet, cap)

    def change_fps(self, cap, fps):
        value = self.fps_value_list[self.fps_display_list.index(fps)]
        fps_config = self.control_config['frameRate']
        commands_configs = fps_config['sendCommand']
        for command in commands_configs:
            packet = self.parseConfig(command, value)
            self.sendCommands(packet, cap)

    def change_focus(self, cap, focus):
        focus_config = self.control_config['ewl']
        scale = float(focus_config['displayValueScale'])
        offset = int(focus_config['displayValueOffset'])
        value = int(focus * scale - offset)

        commands_configs = focus_config['sendCommand']
        for command in commands_configs:
            packet = self.parseConfig(command, value)
            self.sendCommands(packet, cap)

    def change_LED(self, cap, led_value):
        led_config = self.control_config['led0']
        scale = float(led_config['displayValueScale'])
        offset = int(led_config['displayValueOffset'])
        value = int(led_value * scale - offset)

        commands_configs = led_config['sendCommand']
        for command in commands_configs:
            packet = self.parseConfig(command, value)
            self.sendCommands(packet, cap)

    def change_exposure(self, cap:cv2.VideoCapture, exposure:int):
        # no exposure interfaces
        pass


