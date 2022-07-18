import cv2

import numpy as np


class VLoader:
    def load_video(self, path):
        capture = cv2.VideoCapture(path)

        frames = []
        while True:
            ret, tmp_frame = capture.read()

            if not ret:
                break

            frame = cv2.cvtColor(tmp_frame, cv2.COLOR_RGB2GRAY)
            frames.append(frame)

        capture.release()

        res = np.array(frames) #shape: (frame, height, width)
        return res


if __name__ == "__main__":
    loader = VLoader()
    loader.load_video("C:\\Users\\ZJLAB\\Downloads\\Video\\msCam2.avi") #传递路径


