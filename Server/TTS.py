from google.cloud import texttospeech
import os
from playsound import playsound

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'sincere-stack-307000-708764b1979c.json'


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
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.1
        )

        # 音声合成のリクエスト
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # レスポンスをファイル出力
        with open(self.path, "wb") as out:
            out.write(response.audio_content)

    def play(self):
        playsound(self.path)

    def main(self, text):
        self.generate(text)
        self.play()
