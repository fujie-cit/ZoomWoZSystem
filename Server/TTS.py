from google.cloud import texttospeech
import os
import pyaudio

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'config/dialogsys-8962938dd5f3.json'
CHUNK = 1024
WIDTH = 2
CHANNEL = 1
RATE = 24000


class TTS():
    def __init__(self, config):
        self.config = config
        self.path = self.config["TTS"]["path"]
        # クライアントの生成
        self.client = texttospeech.TextToSpeechClient()

    def generate(self, text):

        # 入力の生成
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # 声設定の生成
        voice = texttospeech.VoiceSelectionParams(
            language_code="ja-JP",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        # オーディオ設定の生成
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=1.1
        )

        # 音声合成のリクエスト
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        return response.audio_content
        # p = pyaudio.PyAudio()
        # stream = p.open(format=p.get_format_from_width(WIDTH),
        #                 channels=CHANNEL,
        #                 rate=RATE,
        #                 output=True)
        #
        # if response.audio_content != '':
        #     stream.write(response.audio_content)
        #
        # stream.stop_stream()
        # stream.close()
        # p.terminate()
