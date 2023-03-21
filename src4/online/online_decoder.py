import random
import time

from PySide2.QtCore import QThread


class DecodingThread(QThread):
    def __init__(self, label):
        super(DecodingThread, self).__init__()
        self.label = label
        self.running = True

    def run(self):
        while self.running:
            sleeptime = random.randint(2,5)
            time.sleep(sleeptime)
            self.label.setText("Activity detected!")
            time.sleep(3)
            self.label.setText("")

    def stop(self):
        self.running = False