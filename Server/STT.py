import threading
import socketio
import requests


class STT(threading.Thread):
    def __init__(self, config):
        super(STT, self).__init__()
        self.sio = socketio.Client()
        self.ip = config["STT"]["ip"]

    def run(self):
        # self.sio.connect('http://localhost:9001')
        self.sio.connect(self.ip)

        @self.sio.event
        def connect():
            print("connected!")

        @self.sio.on('on_server_to_client')
        def on_server_to_client(data):
            usr = data['usr']
            text = data['word']

            response = requests.post(
                                    'http://localhost:8080/stt',
                                    {'text': text, 'user': usr}
                                )
