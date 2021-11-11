from typing import Text
from google.cloud import texttospeech
import os
import pyaudio
import io, wave

from collections import OrderedDict
from configparser import ConfigParser
from os import path


CHUNK = 1024
WIDTH = 2
CHANNEL = 1
RATE = 24000

def audio_content2pcm(audio_content):
    f = io.BytesIO(audio_content)
    w = wave.open(f)
    b = w.readframes(w.getnframes())
    return b

class TextToSpeech:
    """音声合成"""

    def __init__(self, config: ConfigParser):
        
        self._config = config
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config['TTS']['key_path']

        # クライアントの生成
        self.client = texttospeech.TextToSpeechClient()

        # キャッシュを保存するディレクトリ
        self._cache_dir = config["TTS"]["cache_dir"]
        # メモリに載せる最大のサイズ
        self._cache_on_mem_size = int(config["TTS"]["cache_on_mem_size"])

        # ID テキスト を書き出したファイル
        self._cache_file_path = path.join(self._cache_dir, "tts.txt")
        # テキスト -> ID の対応辞書
        self._cache_text_to_id = dict()
        # ID -> wav_data の対応辞書（最近のものが末尾，on_mem_size を超えると古いものが消される）
        self._cache_wav_data = OrderedDict()

        self._open_cache()

    @staticmethod
    def _id2filename(id):
        """IDをファイル名に変換する

        Args:
            id (int): id

        Returns:
            str: ファイル名
        """
        return "{:08d}.wav".format(id)

    def _get_new_id(self):
        """新しいIDを取得する. 簡易的にキャッシュファイルの行数 + 1"""
        return len(self._cache_text_to_id) + 1
    
    def _open_cache(self):
        try:
            with open(self._cache_file_path, 'r') as f:
                while True:
                    line = f.readline()
                
                    if not line:
                        break

                    line = line.rstrip()
                    id, text = line.split(' ', 1)
                    self._cache_text_to_id[text] = int(id)
        except FileNotFoundError:
            pass
    
    def _search_cache(self, text):
        """textに対応するデータをキャッシュ内で検索する．
        キャッシュ内に無ければ None を返す．
        メモリ上に見つかればそのデータを返す．
        メモリ上に見つからなければファイルを読み出し，メモリ上に載せて返す．
        
        データは，WAVファイルのバイト列（ヘッダ有り）

        Args:
            text (str): 合成したいテキスト

        Returns:
            [bytes]: WAVファイルのバイト列（ヘッダ有り）. キャッシュに無ければ None
        """
        if text not in self._cache_text_to_id:
            return None
        
        id = self._cache_text_to_id[text]

        if id in self._cache_wav_data:
            self._cache_wav_data.move_to_end(id)
            return self._cache_wav_data[id]

        wav_filename = TextToSpeech._id2filename(id)
        wav_path = path.join(self._cache_dir, wav_filename)

        with open(wav_path, 'rb') as f:
            bytes = f.read()

        self._cache_wav_data[id] = bytes
        self._cache_wav_data.move_to_end(id)

        if len(self._cache_wav_data) > self._cache_on_mem_size:
            self._cache_wav_data.popitem(last=False)

        return bytes

    def _update_cache(self, text, data):
        id = self._get_new_id()
        wav_filename = TextToSpeech._id2filename(id)
        wav_path = path.join(self._cache_dir, wav_filename)

        with open(wav_path, 'wb') as f:
            f.write(data)

        with open(self._cache_file_path, 'a') as f:
            f.write("{} {}\n".format(id, text))
        
        self._cache_wav_data[id] = data
        self._cache_wav_data.move_to_end(id)

        if len(self._cache_wav_data) > self._cache_on_mem_size:
            self._cache_wav_data.popitem(last=False)
        
        self._cache_text_to_id[text] = id

    def generate(self, text):
        data = self._search_cache(text)
        if data:
            return audio_content2pcm(data)
        
        # 入力の生成
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # 声設定の生成
        # https://cloud.google.com/text-to-speech/docs/voices?hl=ja
        voice = texttospeech.VoiceSelectionParams(
            language_code="ja-JP",
            # name="ja-JP-Standard-A", # 女性
            # name="ja-JP-Standard-B", # 女性
            # name="ja-JP-Standard-C", # 男性
            # name="ja-JP-Standard-D", # 男性
            # name="ja-JP-Wavenet-A", # 女性
            # name="ja-JP-Wavenet-B", # 女性
            # name="ja-JP-Wavenet-C", # 男性
            # name="ja-JP-Wavenet-D", # 男性
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        # オーディオ設定の生成
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=1.0,
            sample_rate_hertz=32000,
        )

        # 音声合成のリクエスト
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        self._update_cache(text, response.audio_content)

        # return response.audio_content
        return audio_content2pcm(response.audio_content)
