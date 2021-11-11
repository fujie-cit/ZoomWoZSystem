from os import path
import wave

def get_bell_sound_data():
    """ベル音（3秒，16bit，32kHz）のPCMバイト列を取得する"""

    filepath = path.join(__path__[0], "bell_mono_32k.wav")
    w = wave.open(filepath)
    b = w.readframes(w.getnframes())
    return b
