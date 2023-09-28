from PySide2.QtUiTools import QUiLoader

import asyncio
import websockets
from PySide2.QtWidgets import QDialog


class NetworkController():
    def __init__(self, text_label):
        self.dialog = QUiLoader().load('230922_Network_Dialog.ui')
        self.dialog.ConnectButton.clicked.connect(self.connect)
        self.text_label = text_label

    def connect(self):
        print('NetworkController: connect')
        url = self.getUrl()
        asyncio.get_event_loop().run_until_complete(self.handshake(url, 'hello'))

    def feed(self):
        print('NetworkController: feed')
        url = self.getUrl()
        asyncio.get_event_loop().run_until_complete(self.sendmessage(url, 'feed'))

    def getUrl(self):
        ip = self.dialog.ipAddress.text()
        port = self.dialog.port.text()

        url = 'ws://' + ip + ':' + port
        return url

    async def handshake(self, url, msg):
        async with websockets.connect(url) as ws:
            await ws.send(msg)
            recv = await ws.recv()
            print(recv)
            if recv == 'success':
                self.dialog.connectLabel.setText('Status: Connected')
                self.text_label.setText('Controller Connected')

    async def sendmessage(self, url, msg):
        async with websockets.connect(url) as ws:
            await ws.send(msg)

