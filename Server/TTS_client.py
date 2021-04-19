import socket
import numpy as np
import pyaudio
import time

PORT = 5000
BUFFER_SIZE = 1024

p = pyaudio.PyAudio()
SAMPLE_RATE=24000
# ストリームを開く
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=SAMPLE_RATE,
                frames_per_buffer=1024,
                output=True)

def play(s, sample):
    # ストリームに渡して再生
    s.write(sample.astype(np.float32).tostring())

total_data = bytes()
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(('127.0.0.1', PORT))
    data = "どんな映画がみたいですか"
    s.send(data.encode())

    while True:
        data = s.recv(BUFFER_SIZE) #BUFFER_SIZEバイトづつ分割して受信する
        if not data:
            data = ''
            break
        else:
            total_data = total_data + data #受信した分だけ足していく

    wav = np.fromstring(total_data, dtype='float32')
    print(wav.shape)
    play(stream, wav)
    time.sleep(1)
