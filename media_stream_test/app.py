# coding: utf-8
from __future__ import print_function
from http import client
import os
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
from werkzeug.debug import DebuggedApplication
from flask import Flask, render_template
import datetime
import base64
import webm2wav

import json

from gevent import monkey
monkey.patch_all()


flask_app = Flask(__name__)
flask_app.debug = True

def get_new_wav_filename(topdir):
    """新しいWAVファイル名を取得する

    Args:
        topdir (str): トップディレクトリ

    Returns:
        str: ファイル名（パス）
    """
    i = 0
    while True:
        i += 1
        fname = os.path.join(topdir, "{:08d}.wav".format(i))
        if not os.path.exists(fname):
            return fname


class SoundStreamRecordingApplication(WebSocketApplication):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 録音時に使うもの
        self.__decoder = None
        self._total_bytes = 0
        self._count = 0
        self._fname = None

        # 録音されたファイルが置かれる場所
        self._topdir = "./wav"

    def on_open(self):
        # print("Some client connected!")
        pass

    def on_message(self, message):
        if message is None:
            return

        # print(message)
        message = json.loads(message)

        message_type = message['message_type']
        if message_type == 'sound_start':
            # print("BEFORE webm2wav.Webm2WavDecoder()")
            self._fname = get_new_wav_filename(self._topdir)
            self._total_bytes = 1
            self._count = 0
            self.__decoder = webm2wav.Webm2WavDecoder()
            # print("AFTER  webm2wav.Webm2WavDecoder()")
            print("RECORDING STARTED into {}".format(self._fname))

        elif message_type == "sound_data":
            if self.__decoder is None:
                raise RuntimeError("Decoder is not Ready")
            data = base64.b64decode(message['data'])
            self.__decoder.put(data)
            wav_data = self.__decoder.get()
            if wav_data and len(wav_data) > 0:
                with open(self._fname, "ba") as f:
                    f.write(wav_data)
            self._total_bytes += len(wav_data)
            self._count += 1
            # print("CURRENT: {} TOTAL: {} ({} seconds) FRAME_SHIFT: {}".format(
            #     len(wav_data), self._total_bytes, self._total_bytes / 32000,
            #     int((self._total_bytes / 32000) / self._count * 1000)
            # ))
        elif message_type == "sound_stop":
            # print("BEFORE stop()")
            self.__decoder.stop()
            # print("AFTER  stop()")
            print("RECORDING STOPPED")


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
        ('^/websocket', SoundStreamRecordingApplication),
        ('^/.*', DebuggedApplication(flask_app))
    ]),
    debug=True,
    **ssl_settings
)
server.serve_forever()
