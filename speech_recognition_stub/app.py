# coding: utf-8
from __future__ import print_function
from http import client
import os
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
from werkzeug.debug import DebuggedApplication
from flask import Flask, render_template
import datetime

import json

from gevent import monkey
monkey.patch_all()


flask_app = Flask(__name__)
flask_app.debug = True


class SpeechRecognitionApplication(WebSocketApplication):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # print("SpeechRecognitionApplication.__init__(): called")
        # print("server id {:x}".format(id(self.ws.handler.server)))

        # ユーザ名 -> 送信すべきサーバのsocketのリスト のディクショナリを初期化
        # Applicationのインスタンス自体は接続ごとに構築されるため，
        # selfに対して新しいディクショナリを作っても接続間で共有できない．
        # その代わりに， self.ws.handler.server インスタンスは接続間で共有されて
        # いるため，これに username2servers という新しいプロパティを付け加えて共有
        # する．
        server = self.ws.handler.server
        # 初回でまだプロパティが無い場合は新規のディクショナリを追加する
        if getattr(server, 'username2servers', None) is None:
            server.username2servers = dict() # ユーザ名 -> 送信先のソケットのリスト
            server.username2client = dict() # ユーザ名 -> クライアント
        # 以降の処理を簡単化するため，メンバ変数で参照する
        self.__username2servers = server.username2servers
        self.__username2client = server.username2client

    def on_open(self):
        # print("Some client connected!")
        pass

    def on_message(self, message):
        if message is None:
            return

        print(message)
        message = json.loads(message)

        message_type = message['message_type']
        # from user
        if message_type == 'RequestLogin':
            self.login(message)
        elif message_type == 'SendSpeechRecognitionResult':
            # 音声認識結果．適宜Wizardへ送信
            self.send_speech_recognition_result(message)
        # from server
        elif message_type == 'RequestSendUserNameList':
            # 未対応
            self.send_user_name_list()
        elif message_type == 'RequestStartSendSpeechRecognitionResult':
            # 音声認識結果送信開始要求
            self.start_send_speech_recognition_result(message)
        elif message_type == 'RequestStopSendSpeechRecognitionResult':
            # 音声認識結果送信停止要求
            self.stop_send_speech_recognition_result(message)
        elif message_type == 'Ping':
            self.ping(message)
        elif message_type == 'Pong':
            self.pong(message)

    def login(self, message):
        """ログイン処理. とりあえずパスワード処理は無し

        Args:
            message (str): ユーザ名
        """
        user_name = message["user_name"]
        current_client = self.ws.handler.active_client
        old_user_name = getattr(current_client, 'user_name', None)

        reason = None
        if len(user_name) == 0:
            reason = "ユーザ名を入力して下さい"
        elif not user_name.encode('utf-8').isalnum():
            reason = "ユーザ名は半角英数字のみにしてください"
        elif user_name != old_user_name and user_name in self.__username2client.keys():
            reason = "ユーザ名 {} は既に使われています".format(user_name)
        if reason:
            message_to_send = json.dumps(dict(
                message_type="ResultLogin",
                datetime=datetime.datetime.now().isoformat(),
                result="Faiure",
                reason=reason,
            ))
            current_client = self.ws.handler.active_client
            current_client.ws.send(message_to_send)
            return

        if old_user_name is not None:
            if old_user_name in self.__username2client:
                del self.__username2client[old_user_name]
        current_client.user_name = user_name
        self.__username2client[user_name] = current_client
        print("{} logged in @{}".format(user_name, current_client.address))
        self.send_user_name_list(broadcast=True)

        message_to_send = json.dumps(dict(
            message_type="ResultLogin",
            datetime=datetime.datetime.now().isoformat(),
            result="Success",
        ))
        current_client = self.ws.handler.active_client
        current_client.ws.send(message_to_send)

    def send_user_name_list(self, broadcast=False):
        """ユーザ名リスト送信
        """
        dtime = datetime.datetime.now().isoformat()
        user_name_list = sorted(self.__username2client.keys())
        message_to_send = json.dumps(dict(
            message_type="SendUserNameList",
            datetime=dtime,
            user_name_list=user_name_list            
        ))
        print(message_to_send)
        if not broadcast: 
            current_client = self.ws.handler.active_client
            current_client.ws.send(message_to_send)
        else:
            for client in self.ws.handler.server.clients.values():
                client.ws.send(message_to_send)


    def send_speech_recognition_result(self, message: dict):
        """ユーザから送られてきた音声認識結果を適宜サーバ（Wizard）に送る

        Args:
            message (dict): ユーザから送られてきたデータ
        """
        # ユーザ名に対応する，送信先ソケットのリストを取得
        user_name = message['user_name']
        if user_name not in self.__username2servers:
            self.__username2servers[user_name] = []
        server_list = self.__username2servers[user_name]

        # 各送信先に送信する.
        # 送信に失敗したソケットは閉じるリストから外す．
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

    def start_send_speech_recognition_result(self, message: dict):
        """音声認識結果送信開始要求への対応

        Args:
            message (dict): サーバ（Wizard）から送られてきたデータ
        """
        # ユーザ名に対応したソケットのリストを取得する
        user_name = message['user_name']
        if user_name not in self.__username2servers:
            self.__username2servers[user_name] = []
        server_list = self.__username2servers[user_name]
        # そのリストの中にまだ現在のソケットがなければ追加する
        if self.ws not in server_list:
            server_list.append(self.ws)
        # print(server_list)

    def stop_send_speech_recognition_result(self, message: dict):
        """音声認識結果送信停止要求への対応

        Args:
            message (dict): サーバ（Wizard）から送られてきたデータ
        """
        # ユーザ名に対応したソケットのリストを取得する
        user_name = message['user_name']
        if user_name not in self.__username2servers:
            return
        server_list = self.__username2servers[user_name]
        # リストの中に現在のソケットが無ければ何もしない
        if self.ws not in server_list:
            return
        # リストから現在のソケットを削除する
        server_list.remove(self.ws)
        # print(server_list)

    def ping(self, message: dict):
        """Ping処理

        Args:
            message (dict): [description]
        """
        user_name = message['user_name']
        client_to_send = self.__username2client[user_name]

        dtime = datetime.datetime.now().isoformat()
        source_dtime = message['datetime']
        current_client = self.ws.handler.active_client
        source_id = current_client.address
        message_to_send = json.dumps(dict(
            message_type="Ping",
            datetime=dtime,
            user_name=user_name,
            source_datetime=source_dtime,
            source_id=source_id
        ))
        client_to_send.ws.send(message_to_send)


    def pong(self, message: dict):
        """Pingへの応答"""
        user_name=message['user_name']
        source_id=message['source_id']
        source_id=tuple(source_id)
        client_to_send = self.ws.handler.server.clients[source_id]
        
        dtime = message['datetime']
        source_dtime = message['source_datetime']
        message_to_send = json.dumps(dict(
            message_type="Pong",
            datetime=dtime,
            user_name=user_name,
            source_datetime=source_dtime,
        ))
        client_to_send.ws.send(message_to_send)

    """
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
    """

    def on_close(self, reason):
        current_client = self.ws.handler.active_client
        print("on_close: {} closed".format(current_client.address))
        user_name = getattr(current_client, 'user_name', None)
        if user_name is None:
            return
        del self.__username2client[user_name]
        print("{} logged out".format(user_name))

@flask_app.route('/')
def index():
    return render_template('index.html')


# メイン処理
# ポート番号
#   本番環境では80番にする．
#   ただしセキュリティ上の問題でクライアント側でマイクをオンに
#   できない現象を確認したので本番環境はSSLを使う必要があると思われる．
port = 8000

# SSL設定
#   実行ディレクトリに fullchain.pem と privkey.pem があれば
#   SSLにする．
if os.path.exists("fullchain.pem") and os.path.exists("privkey.pem"):
    ssl_settings = dict(certfile="fullchain.pem",
                        keyfile="privkey.pem")
    port = 443
else:
    ssl_settings = dict()

server = WebSocketServer(
    ('0.0.0.0', port),
    Resource([
        ('^/websocket', SpeechRecognitionApplication),
        ('^/.*', DebuggedApplication(flask_app))
    ]),
    debug=True,
    **ssl_settings
)
server.serve_forever()
