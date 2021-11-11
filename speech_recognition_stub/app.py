# coding: utf-8
from __future__ import print_function

import json

from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template
from werkzeug.debug import DebuggedApplication

from geventwebsocket import WebSocketServer, WebSocketApplication, Resource

flask_app = Flask(__name__)
flask_app.debug = True


class SpeechRecognitionApplication(WebSocketApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ユーザ名 -> 送信すべきサーバのsocketのリスト
        print("*****constructor called****!")
        print("{:x}".format(id(self.ws.handler.server)))
        server = self.ws.handler.server
        if getattr(server, 'username2servers', None) is None:
            server.username2servers = dict()
        self.__username2servers = server.username2servers

    def on_open(self):
        print("Some client connected!")

    def on_message(self, message):
        if message is None:
            return
        
        print(message)
        message = json.loads(message)

        message_type = message['message_type']
        # from user
        if message_type == 'RequestLogin':
            # 管理する必要は現時点ではない
            print("{} logged in".format(message['user_name']))
        elif message_type == 'SendSpeechRecognitionResult':
            self.send_speech_recognition_result(message)
        # from server
        elif message_type == 'RequestSendUserNameList':
            # 未対応
            self.send_user_name_list()
        elif message_type == 'RequestStartSendSpeechRecognitionResult':
            self.start_send_speech_recognition_result(message)
        elif message_type == 'RequestStopSendSpeechRecognitionResult':
            self.stop_send_speech_recognition_result(message)

        # message = json.loads(message)
        # if message['msg_type'] == 'message':
        #     self.broadcast(message)
        # elif message['msg_type'] == 'update_clients':
        #     self.send_client_list(message)

    def send_user_name_list(self):
        pass

    def send_speech_recognition_result(self, message):
        user_name = message['user_name']
        if user_name not in self.__username2servers:
            self.__username2servers[user_name] = [] 
        server_list = self.__username2servers[user_name]
        message = json.dumps(message)
        errorneous_sockets = []
        for socket in server_list:
            try:
                socket.send(message)
            except:
                errorneous_sockets.append(socket)
        for socket in errorneous_sockets:
            server_list.remove(socket)
        print(server_list)

    def start_send_speech_recognition_result(self, message):
        user_name = message['user_name']
        if user_name not in self.__username2servers:
            self.__username2servers[user_name] = []
        server_list = self.__username2servers[user_name]
        if self.ws not in server_list:
            server_list.append(self.ws)
        print(server_list)

    def stop_send_speech_recognition_result(self, message):
        user_name = message['user_name']
        if user_name not in self.__username2servers:
            return
        server_list = self.__username2servers[user_name]
        if self.ws not in server_list:
            return
        server_list.remove(self.ws)
        print(server_list)

    def send_client_list(self, message):

        # ここで使用している，ソケット情報に関するまとめ．
        
        # self.ws: サーバソケットに対応する WebSocketオブジェクト
        # self.ws.handler: self.ws に紐付いた WebSocketHandlerオブジェクト
        # self.ws.handler.active_client: 現在対応しているクライアントに対応する
        #   Clientオブジェクト
        # self.ws.handler.server: サーバソケットに対応する WebSocketServer オブジェクト
        # self.ws.handler.server.clients: サーバソケットに接続しているクライアントの
        #   Clientオブジェクトのディクショナリ． Clientのアドレス（address属性）が
        #   キーになっている
        
        # Clientオブジェクトは，デフォルトで addressとwsの2つの属性を持つ．
        # addressは接続元のアドレス（'127.0.0.1'などの文字列）と，ポート番号（int）の
        # タプル（タプルなのでディクショナリのキーとして使える）．
        # wsは対応するWebSocketオブジェクト．

        # 下の例では，Clientオブジェクトに nickname属性を追加してチャット上でのクライアント
        # のニックネームを管理している．
        current_client = self.ws.handler.active_client
        current_client.nickname = message['nickname']

        self.ws.send(json.dumps({
            'msg_type': 'update_clients',
            'clients': [
                getattr(client, 'nickname', 'anonymous')
                for client in self.ws.handler.server.clients.values()
            ]
        }))

    def broadcast(self, message):
        for client in self.ws.handler.server.clients.values():
            client.ws.send(json.dumps({
                'msg_type': 'message',
                'nickname': message['nickname'],
                'message': message['message']
            }))

    def on_close(self, reason):
        print("Connection closed!")


@flask_app.route('/')
def index():
    return render_template('index.html')

WebSocketServer(
    ('0.0.0.0', 8000),

    Resource([
        ('^/websocket', SpeechRecognitionApplication),
        ('^/.*', DebuggedApplication(flask_app))
    ]),

    debug=False
).serve_forever()
