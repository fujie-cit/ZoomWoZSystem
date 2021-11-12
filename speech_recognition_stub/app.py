# coding: utf-8
from __future__ import print_function
import os
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
from werkzeug.debug import DebuggedApplication
from flask import Flask, render_template

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
            server.username2servers = dict()
        # 以降の処理を簡単化するため，メンバ変数で参照する
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
            # ログインのリクエスト．現時点では管理する必要無し．
            # 厳密さを考えなければ，送られてくる音声認識結果にすべてuser_nameが入っている
            # のでそれを見れば送り先の判定ができる．
            print("{} logged in".format(message['user_name']))
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

    def send_user_name_list(self):
        pass

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
        print("Connection closed!")


@flask_app.route('/')
def index():
    return render_template('index.html')


# メイン処理
# ポート番号
#   本番環境では80番にする．
#   ただしセキュリティ上の問題でクライアント側でマイクをオンに
#   できない現象を確認したので本番環境はSSLを使う必要があると思われる．
port = 80

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
