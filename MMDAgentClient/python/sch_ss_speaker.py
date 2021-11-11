# coding: utf-8
import time
import pyaudio as pa
import struct
import threading

def duration_str2list(str):
    u"""音素継続長情報の文字列から，
    各音素と発話開始時からの終了時刻のペアのリストを生成する
    """
    l = str.split(' ')
    rv = [] # 戻り値
    td = 0  # トータルのデュレーション
    for p, d in zip(l[::2], l[1::2]):
        td += int(d)
        rv.append((p,td))
    return rv

def find_phone_from_duration_list (pos, duration_list):
    u"""発話位置から，対応する音素を取得する"""
    for p, d in duration_list:
        if pos < d:
            return p
    return duration_list[-1][0]

def isOpenVowel (phone):
    u"""口を開く母音かどうかを判断"""
    return phone[0] in 'auo'

def isCloseVowel (phone):
    u"""口を閉める母音かどうかを判断"""
    return phone[0] in 'ie'

def isCloseConsonant (phone):
    u"""口を閉める子音かどうか判断"""
    return phone[0] in 'nmbpxw'

class LipSync:
    def __init__ (self, mmdagent_schema_client):
        self.__client = mmdagent_schema_client

    def put (self, phone):
        target = 0
        if isOpenVowel (phone):
            target = 40.0
        elif isCloseVowel (phone):
            target = 13.0
        elif isCloseVowel (phone):
            target = 0.0
        elif isCloseConsonant (phone):
            target = 0.0
        else:
            target = 20.0
        self.__client.send ('MOU', target)

class SoundPlay:
    CHUNK=512

    def __init__(self, lip_sync=None):
        self._p = pa.PyAudio()
        self._stream = self._p.open (format=pa.paInt16,
                                     channels=1,
                                     rate=32000,
                                     output=True,
                                     frames_per_buffer=SoundPlay.CHUNK,
                                     stream_callback=self.callback)

        # データの入出力時に利用111
        self._cond = threading.Condition()

        # データ
        self._data = None
        self._duration_list = None
        self.duration = 0.4
        self.sample_rate = 32000
        self._pos = 0

        # リップシンク制御用
        self._lip_sync = lip_sync

    def put (self, data):
        with self._cond:
            self._data = data
            self._pos = 0
            self._last_phone = None
            self._cond.notify_all()

    def callback (self, in_data, frame_count, time_info, status):
        # print "%d" % frame_count
        rv = b'\x00\x00' * frame_count
        with self._cond:
            if self._data == None:
                return (rv, pa.paContinue)
            else:
                s = self._pos
                e = s + (frame_count * 2)
                if e <= len(self._data):
                    rv = self._data[s:e]
                    self._pos = e
                else:
                    rv = self._data[s:]
                    rv += b'\x00\x00' * (frame_count - int(len(rv)/2))
                    self._data = None
                    self._duration_list = None
                    self._pos = 0
                    self._lip_sync.put('n')

                if self._pos != 0:
                    # p = find_phone_from_duration_list(
                    #     self._pos / 2, self._duration_list)
                    tmp = self._pos // (self.sample_rate*self.duration)
                    if tmp % 2 == 0:
                        p = 'a'
                    else:
                        p = 'n'

                    if p != self._last_phone:
                        self._lip_sync.put (p)
                    self._last_phone = p

        return (rv, pa.paContinue)

    def clear (self):
        with self._cond:
            self._data = None
            self._pos = 0
            self._last_phone = None
            self._lip_sync.put ('m')
            self._cond.notify_all()

    def start (self):
        with self._cond:
            self._stream.start_stream()

    def stop (self):
        with self._cond:
            self._stream.stop_stream()

# class PlayHandler (monea.ProcessingRequestHandler):
#     def __init__ (self, sound_play):
#         monea.ProcessingRequestHandler.__init__ (self)
#         self._sound_play = sound_play
#
#     def handleRequest (self, request):
#         print(u"入力文: %s" % (request.findFirstParam ('text').getAsString().decode('utf-8')))
#         print(u"長さ(バイト): %d" % (len(request.findFirstParam ('data').getAsByteArray())))
#         print(u"音素継続長情報: %s" % (request.findFirstParam ('duration').getAsString()))
#
#         data = request.findFirstParam ('data').getAsByteArray()
#         data = bytes(''.join(data))
#
#         duration_list = duration_str2list(request.findFirstParam ('duration').getAsString())
#         self._sound_play.put (data, duration_list)
#
# class StopHandler (monea.ProcessingRequestHandler):
#     def __init__ (self, sound_play):
#         monea.ProcessingRequestHandler.__init__ (self)
#         self._sound_play = sound_play
#
#     def handleRequest (self, request):
#         self._sound_play.clear()
#
# class SchemaSpeaker:
#     DEFAULT_MODULE_XML_FILENAME="sch_speech_speaker.xml"
#
#     def __init__ (self, mmdagent_schema_client, module_xml_filename=DEFAULT_MODULE_XML_FILENAME):
#         self.__client = mmdagent_schema_client
#         self.__context = monea.ModuleContextFactory_newContext (module_xml_filename)
#         self.__local = self.__context.getLocalModule ()
#
#         self.__lip_sync = LipSync (self.__client)
#         self.__sound_play = SoundPlay (self.__lip_sync)
#         self.__play_handler = PlayHandler (self.__sound_play)
#         self.__stop_handler = StopHandler (self.__sound_play)
#
#     def start (self):
#         self.__sound_play.start()
#         self.__local.getProcessingRequestQueue ('play').setHandler(self.__play_handler)
#         self.__local.getProcessingRequestQueue ('stop').setHandler(self.__stop_handler)
#
# if __name__ == '__main__':
#     import mmdagent_schema_client as msc
#
#     client = msc.MMDAgentSchemaClient()
#     speaker = SchemaSpeaker (client)
#     speaker.start()
#
#     while True:
#         time.sleep (1)
