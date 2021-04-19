import threading
import socketio
import requests


class STT(threading.Thread):
    def __init__(self):
        super(STT, self).__init__()
        self.sio = socketio.Client()

    def run(self):
        self.sio.connect('http://34.82.235.69:9001')

        @self.sio.event
        def connect():
            print("connected!")

        @self.sio.on('on_server_to_client')
        def on_server_to_client(data):
            usr = data['user']
            text = data['word']

            response = requests.post(
                                    'http://localhost:8080/stt',
                                    {'text': text, 'user': usr}
                                )
