import websocket
import threading
import json
from pprint import pprint
import datetime
from typing import Union, Callable, List
from enum import Enum


class SpeechRecognitionState(Enum):
    """音声認識の状態.
    
    Start（開始）, Partial（途中結果）, End（終了）
    """
    Start = 1
    Partial = 2
    End = 3


class SpeechRecognitionResult:
    """音声認識結果"""

    def __init__(
        self, 
        dtime: Union[datetime.datetime, str],
        user_name: str,
        state: Union[SpeechRecognitionState, str],
        result: str
    ):
        if isinstance(dtime, str):
            if dtime[-1] == 'Z':
                dtime = dtime[:-1]
            dtime = datetime.datetime.fromisoformat(dtime)

        if isinstance(state, str):
            if state == "Start":
                state = SpeechRecognitionState.Start
            elif state == "Partial":
                state = SpeechRecognitionState.Partial
            elif state == "End":
                state = SpeechRecognitionState.End
            else:
                raise RuntimeError(
                    "unkonwn speech recognition result: {}".format(state))

        self._dtime = dtime
        self._user_name = user_name
        self._state = state
        self._result = result

    @property
    def dtime(self) -> datetime.datetime:
        """日時"""
        return self._dtime

    @property
    def user_name(self):
        """ユーザ名"""
        return self._user_name

    @property
    def state(self) -> SpeechRecognitionState:
        """状態"""
        return self._state

    @property
    def result(self):
        return self._result

    def __str__(self):
        return 'SpeechRecognitionResult("{}", "{}", "{}", "{}")'.format(
            self.dtime.isoformat(),
            self.user_name,
            self.state.name,
            self.result
        )

    def __repr__(self):
        return self.__str__()


class UserManagerClient:
    def __init__(self, url="ws://localhost:8000/websocket"):
        self._websocket_app = websocket.WebSocketApp(
            url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close)

        self._cond = threading.Condition()

        self._opened = False # 接続しているかどうか
        self._closed = False # 閉じているかどうか
        self._closed_with_error = False # エラー状態かどうか

        self._receiver_list = [] # type: List[SpeechRecognitionResult]

        # アプリをバックグラウンドで動かすためのスレッド
        self._thread = threading.Thread(target=self._websocket_app.run_forever)
        self._thread.daemon = True
        self._thread.start()

        # 接続が開始するか，エラーで止まるまで待機
        with self._cond:
            while not self._opened and not self._closed:
                self._cond.wait()


    def append_receiver(self, receiver: Callable[[SpeechRecognitionResult], None]):
        if receiver in self._receiver_list:
            return
        self._receiver_list.append(receiver)


    def request_start_send_speech_recognition_result(self, user_name: str):
        """音声認識結果送信開始要求を送る

        Args:
            user_name (str): 対象ユーザ名
        """
        nowstr = datetime.datetime.now().isoformat()
        message = json.dumps(dict(
            message_type='RequestStartSendSpeechRecognitionResult',
            datetime=nowstr,
            user_name=user_name
        ))
        self._websocket_app.send(message)

    
    def request_stop_send_speech_recognition_result(self, user_name: str):
        """音声認識結果送信停止要求を送る

        Args:
            user_name (str): 対象ユーザ名
        """
        nowstr = datetime.datetime.now().isoformat()
        message = json.dumps(dict(
            message_type='RequestStopSendSpeechRecognitionResult',
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
            pprint(message, compact=False)

            result = SpeechRecognitionResult(
                message['datetime'], message['user_name'], 
                message['speech_recognition_state'], 
                message['speech_recognition_result'])
            for receiver in self._receiver_list:
                receiver(result)
                    

    def _on_open(self, ws):
        """サーバに接続したときに呼び出されるコールバック関数．

        Args:
            ws (WebSocket): WebSocket
        """
        with self._cond:
            self._opened = True
            self._cond.notify_all()


    def _on_error(self, ws, error):
        """エラーが起こったときに呼び出されるコールバック関数．

        Args:
            ws (WebSocket): WebSocket
        """
        with self._cond:
            self._closed = True
            self._closed_with_error = True
            self._cond.notify_all()
        

    def _on_close(self, ws, close_status_code, close_msg):
        """接続が切断したときに呼び出されるコールバック関数．

        Args:
            ws (WebSocket): WebSocket
        """
        with self._cond:
            self._closed = True
            self._cond.notify_all()


    def _send(self, message):
        """サーバにメッセージを送信する

        Args:
            message (str): 送信するメッセージ（文字列）
        """
        self._websocket_app.send(message)

