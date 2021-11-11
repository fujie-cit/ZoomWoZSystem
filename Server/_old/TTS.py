from google.cloud import texttospeech
import os
import pyaudio
import io, wave

CHUNK = 1024
WIDTH = 2
CHANNEL = 1
RATE = 24000

def audio_content2pcm(audio_content):
    f = io.BytesIO(audio_content)
    w = wave.open(f)
    b = w.readframes(w.getnframes())
    return b

class TTS():
    def __init__(self, config):
        self.config = config
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config['TTS']['key_path']

        # クライアントの生成
        self.client = texttospeech.TextToSpeechClient()

    def generate(self, text):

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

        # return response.audio_content
        return audio_content2pcm(response.audio_content)
