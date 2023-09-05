import json
import time
import cv2
import numpy as np


def sendCommands(input_list, cap):
    if len(input_list) < 6:
        tmp = input_list[0]
        tmp |= (len(input_list) & 0xFF) << 8
        for i in range(1, len(input_list)):
            tmp |= input_list[i] << (8 * (i + 1))

        ret_list = [tmp & 0x00000000FFFF, (tmp & 0x0000FFFF0000) >> 16, (tmp & 0XFFFF00000000) >> 32]

        print(ret_list)

        cap.set(cv2.CAP_PROP_CONTRAST, ret_list[0])
        time.sleep(0.2)
        cap.set(cv2.CAP_PROP_GAMMA, ret_list[1])
        time.sleep(0.2)
        cap.set(cv2.CAP_PROP_SHARPNESS, ret_list[2])
        time.sleep(0.2)
    elif len(input_list) == 6:
        tmp = input_list[0] | 0x01
        for i in range(1, len(input_list)):
            tmp |= input_list[i] << (8 * i)

        ret_list = [tmp & 0x00000000FFFF, (tmp & 0x0000FFFF0000) >> 16, (tmp & 0XFFFF00000000) >> 32]

        print(ret_list)

        cap.set(cv2.CAP_PROP_CONTRAST, ret_list[0])
        time.sleep(0.2)
        cap.set(cv2.CAP_PROP_GAMMA, ret_list[1])
        time.sleep(0.2)
        cap.set(cv2.CAP_PROP_SHARPNESS, ret_list[2])

    else:
        print('Illegal packet length')


def parse_config(data):
    init_data = data['initialize']
    packets = []
    keys = []
    for command in init_data:
        key = 0
        packet = []

        v = command['addressW']
        if 'b' in v:
            packet.append(int(v, 2))
        else:
            packet.append(int(v, 16))
        key = (key << 8) | packet[-1]

        for i in range(int(command['regLength'])):
            packet.append(int(command['reg'+str(i)], 16))
            key = (key << 8) | packet[-1]

        for i in range(int(command['dataLength'])):
            v = command['data'+str(i)]
            if 'b' in v:
                packet.append(int(v, 2))
            else:
                packet.append(int(v, 16))
            key = (key << 8) | packet[-1]

        packets.append(packet)
        keys.append(key)

    return packets


js_path = 'C:\\Users\ZJLAB\Documents\WeChat Files\wxid_ciusgv6gvwq222\FileStorage\File\\2023-07\Miniscope\Miniscope\source\deviceConfigs\\miniscopes.json'

with open(js_path) as f:
    js = json.load(f)

data = js['Miniscope_V4_BNO']
init_data = data['initialize']
packets = parse_config(data)
print(packets)

cap = cv2.VideoCapture()

cap.open(0, cv2.CAP_DSHOW)


input_list = [0xC0, 0x1F, 0b00010000]
sendCommands(input_list, cap)

input_list = [0xB0, 0x05, 0b00100000]
sendCommands(input_list, cap)

for packet in packets:
    sendCommands(packet, cap)

while True:
    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2.imshow('frame', frame)
        cv2.waitKey(10)
