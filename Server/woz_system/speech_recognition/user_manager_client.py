import websocket
import threading
import json
from pprint import pprint
import datetime

class UserManagerClient:
    def __init__(self, url="ws://localhost:8000/websocket"):
        self._websocket_app = websocket.WebSocketApp(
            url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close)
        # アプリをバックグラウンドで動かすためのスレッド
        self._thread = threading.Thread(target=self._websocket_app.run_forever)
        self._thread.daemon = True

    def start(self):
        """スレッドを開始する
        """
        self._thread.start()

    def request_start_send_speech_recognition_result(self, user_name):
        nowstr = datetime.datetime.now().isoformat()
        message=json.dumps(dict(
            message_type='RequestStartSendSpeechRecognitionResult',
            datetime=nowstr,
            user_name=user_name
        ))
        self._websocket_app.send(message)

    def _on_message(self, ws, message):
        """メッセージを受信したときに呼び出されるコールバック関数．

        Args:
            ws (WebSocket): WebSocket
            message (str): 受信したメッセージ（文字列）
        """
        message = json.loads(message)
        if message['message_type'] == 'SendSpeechRecognitionResult':
            nowstr = datetime.datetime.now().isoformat()
            print("Speech Recognition Result " + nowstr)
            pprint(message, width=10)

    def _on_open(self, ws):
        """サーバに接続したときに呼び出されるコールバック関数．

        Args:
            ws (WebSocket): WebSocket
        """
        pass

    def _on_error(self, ws, error):
        """エラーが起こったときに呼び出されるコールバック関数．

        Args:
            ws (WebSocket): WebSocket
        """
        print(error)
        pass

    def _on_close(self, ws, close_status_code, close_msg):
        """接続が切断したときに呼び出されるコールバック関数．

        Args:
            ws (WebSocket): WebSocket
        """
        pass

    def _send(self, message):
        """サーバにメッセージを送信する

        Args:
            message (str): 送信するメッセージ（文字列）
        """
        self._websocket_app.send(message)

