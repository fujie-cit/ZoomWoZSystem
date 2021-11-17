import websocket
import threading
import json
from pprint import pprint
import datetime
from typing import Union, Callable, List
from enum import Enum
import time


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
                dtime = dtime + datetime.timedelta(hours=9)
            else:
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
        
        self._user_name_list = [] # ユーザ名のリスト
        self._diff_time_dict = {} # ユーザ名 -> 誤差時間

        # アプリをバックグラウンドで動かすためのスレッド
        self._thread = threading.Thread(target=self._websocket_app.run_forever)
        self._thread.daemon = True
        self._thread.start()

        # 定期的に ping を打つスレッド
        self._ping_thread = threading.Thread(target=self._periodic_ping)
        self._ping_thread.daemon = True
        self._ping_thread.start()

        # 接続が開始するか，エラーで止まるまで待機
        with self._cond:
            while not self._opened and not self._closed:
                self._cond.wait()
        
        # 最初にユーザリストを更新する
        self.request_send_user_name_list()

    def append_receiver(self, receiver: Callable[[SpeechRecognitionResult], None]):
        """音声認識結果取得時のハンドラを追加する．

        Args:
            receiver (Callable[[SpeechRecognitionResult], None]): [description]
        """
        if receiver in self._receiver_list:
            return
        with self._cond:
            self._receiver_list.append(receiver)

    def get_diff_time(self, user_name: str) -> datetime.timedelta:
        """ユーザ端末との推定時差を返す．

        Args:
            user_name (str): ユーザ名

        Returns:
            datetime.timedelta: 時差．存在しないときは None
        """
        diff_time = None # type: datetime.timedelta
        with self._cond:
            diff_time = self._diff_time_dict.get(user_name)
        return diff_time


    def request_send_user_name_list(self):
        """ユーザ名リスト送信要求を出す"""
        message = json.dumps(dict(
            message_type="RequestSendUserNameList",
            datetime=datetime.datetime.now().isoformat(),
        ))
        self._websocket_app.send(message)

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

    def ping(self, user_name: str):
        nowstr = datetime.datetime.now().isoformat()
        message = json.dumps(dict(
            message_type='Ping',
            datetime=nowstr,
            user_name=user_name
        ))
        self._websocket_app.send(message)
    
    def get_user_name_list(self):
        r = []
        with self._cond:
            r.extend(self._user_name_list)
            return r

    def _on_message(self, ws, message):
        """メッセージを受信したときに呼び出されるコールバック関数．

        Args:
            ws (WebSocket): WebSocket
            message (str): 受信したメッセージ（文字列）
        """
        message = json.loads(message)

        # DEBUG
        # pprint(message)

        if message['message_type'] == 'SendSpeechRecognitionResult':
            self.handle_send_speech_recognition_result(message)
        elif message['message_type'] == 'SendUserNameList':
            self.handle_send_user_name_list(message)
        elif message['message_type'] == 'Pong':
            self.handle_pong(message)

    def handle_send_speech_recognition_result(self, message: dict):
        """音声認識結果受信時の処理

        Args:
            message (dict): 受信したメッセージ
        """
        result = SpeechRecognitionResult(
            message['datetime'], message['user_name'], 
            message['speech_recognition_state'], 
            message['speech_recognition_result'])
        
        with self._cond:
            current_receiver_list = self._receiver_list[:]
        
        for receiver in current_receiver_list:
            receiver(result)

    def handle_send_user_name_list(self, message: dict):
        """ユーザ名リストの更新

        Args:
            message (dict): ユーザ名リストを含むメッセージ
        """
        new_user_name_list = message["user_name_list"]
        with self._cond:
            self._user_name_list.clear()
            self._user_name_list.extend(new_user_name_list)

    def handle_pong(self, message: dict):
        """Pongを処理して，時差情報を更新

        Args:
            message (dict): 送信されたメッセージ
        """
        source_datetime = datetime.datetime.fromisoformat(message['source_datetime'])
        user_datetime = message['datetime']
        if user_datetime[-1] == 'Z':
            user_datetime = user_datetime[:-1]
            user_datetime = datetime.datetime.fromisoformat(user_datetime)
            user_datetime = user_datetime + datetime.timedelta(hours=9)
        else:
            user_datetime = datetime.datetime.fromisoformat(user_datetime)

        now = datetime.datetime.now()
        
        estimated_localtime = now + (now - source_datetime) / 2
        diff_time = estimated_localtime - user_datetime

        user_name = message['user_name']
        
        with self._cond:
            if user_name not in self._diff_time_dict:
                self._diff_time_dict[user_name] = (diff_time, 1)
            else:
                avg, cnt = self._diff_time_dict[user_name]
                new_diff_time = (avg * cnt + diff_time) / (cnt + 1)
                self._diff_time_dict[user_name] = (new_diff_time, cnt + 1)

        # pprint(self._diff_time_dict, compact=False)


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

    def _periodic_ping(self):
        while True:
            user_name_list = self.get_user_name_list()
            for user_name in user_name_list:
                self.ping(user_name)
            time.sleep(1)