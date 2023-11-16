import time
from multiprocessing import Queue, Manager, Process

import cv2
import numpy as np
from PySide2 import QtCore

from src.cameraController import MiniscopeController, SimpleCameraController
from src.registration_h import on_NCC


def online_process(manager, scene_out_queue: Queue, trace_out_queue: Queue, event_queue: Queue):
    cap = cv2.VideoCapture(manager["camera"])

    if manager["miniscope"]:
        print('miniscope controller')
        controller = MiniscopeController('./configs/miniscopes.json')
    else:
        print('simple controller')
        controller = SimpleCameraController()

    args = controller.init_args(cap)

    width = args["width"]
    height = args["height"]
    gain = manager["gain"] = args["gain"]
    fps = manager["fps"] = args["fps"]
    focus = manager["focus"] = args["focus"]
    led = manager["led"] = args["led"]

    del args

    fakecapture = manager["fakecapture"]
    if fakecapture:
        # todo：修改视频路径
        cap = cv2.VideoCapture("D:\data\\2023_08_16\\2023_08_16\\14_59_15\Miniscope\\0.avi")
        fps = manager["fps"] = cap.get(cv2.CAP_PROP_FPS)  # todo: 默认读取视频文件帧率，可能需要手动改低一点

    ged_template = manager["ged_template"]
    mcc = None

    timelist = []
    ptime = time.perf_counter()
    while not manager["stopped"]:
        if event_queue.qsize() > 0:
            event = event_queue.get()
            # todo: handle events

        ret, frame = cap.read()
        time_stamp = time.perf_counter()
        
        if not ret:
            if fakecapture:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            break
        
        if not fakecapture:
            if gain != manager["gain"]:
                # change gain
                new_gain = manager["gain"]
                print(f'change gain {gain} -> {new_gain}')
                gain = new_gain
                controller.change_gain(cap, gain)
            if fps != manager["fps"]:
                # change fps
                new_fps = manager["fps"]
                print(f'change fps {fps} -> {new_fps}')
                fps = new_fps
                controller.change_fps(cap, fps)
            if focus != manager["focus"]:
                # change focus
                new_focus = manager["focus"]
                print(f'change focus {focus} -> {new_focus}')
                focus = new_focus
                controller.change_focus(cap, focus)
            if led != manager["led"]:
                # change led
                new_led = manager["led"]
                print(f'change led {led} -> {new_led}')
                led = new_led
                controller.change_LED(cap, led)

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        if ged_template is not None:
            t0 = time.time()
            if mcc is None:
                mcc = on_NCC(ged_template, frame)

            gray_frame, _ = mcc.NCC_framebyframe(gray_frame)
            frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)
            # gray_frame, _ = mcc.NCC_framebyframe_out_gpu(gray_frame)
            # frame = cv2.cvtColor(gray_frame.cpu().numpy().astype(np.uint8), cv2.COLOR_GRAY2RGB)
            t1 = time.time()
            # print('MC time: ', t1 - t0)

        if manager["rtProcess"]:
            trace_out_queue.put(gray_frame)

        scene_out_queue.put(frame)

        dis = time.perf_counter() - ptime
        ptime = time.perf_counter()

        if fakecapture:
            delay = 1/fps - dis
            if delay > 0:
                time.sleep(delay)


        timelist.append(ptime)
        if len(timelist) == 100:
            print(f'avg fps:', 100/(timelist[-1]-timelist[0]))
            timelist = []

    cap.release()


class OnlineProcess(QtCore.QObject):
    def __init__(self, camera: str, parent: QtCore.QObject, miniscope=False):
        super().__init__(parent)
        self.camera = camera
        self.miniscope = miniscope
        self.fakecapture = False
        self.ged_template = None

        self.mg = Manager()
        self.scene_queue = self.mg.Queue()
        self.trace_queue = self.mg.Queue()
        self.event_queue = self.mg.Queue()

    def start(self):
        args = self.init_manager()
        self.manager = self.mg.dict(args)
        p = Process(target=online_process, args=(self.manager, self.scene_queue, self.trace_queue, self.event_queue))
        p.start()

    def init_manager(self):
        args = {
            "camera": self.camera,
            "miniscope": self.miniscope,
            "fakecapture": True,
            "stopped": False,
            "ged_template": self.ged_template,
            "rtProcess": False,
        }

        return args

    def stop(self):
        self.manager["stopped"] = True

    def rtProcess(self):
        self.manager["rtProcess"] = True

    def fps_change(self, fps):
        self.manager["fps"] = fps

    def gain_change(self, gain):
        self.manager["gain"] = gain

    def focus_change(self, focus):
        self.manager["focus"] = focus

    def led_change(self, led):
        self.manager["led"] = led