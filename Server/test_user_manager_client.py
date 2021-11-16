from woz_system.speech_recognition.user_manager_client import \
    SpeechRecognitionState, SpeechRecognitionResult, UserManagerClient
from pprint import pprint
import time

def callback(result: SpeechRecognitionResult):
    pprint(result)

uc = UserManagerClient()
uc.append_receiver(callback)

uc.request_start_send_speech_recognition_result("fujie")

while True:
    uc.ping("fujie")
    time.sleep(0.3)
