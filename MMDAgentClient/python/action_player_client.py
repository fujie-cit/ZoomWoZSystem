# coding: utf-8
# 藤江注: このファイルはMONEAを使わない時は使いません 
import os
import monea

# --- 各種設定ファイルの場所など ---
# カレントディレクトリ
current_dir = os.path.abspath(os.path.dirname(__file__))
# dataフォルダの位置
data_dir  = os.path.abspath(os.path.join(current_dir, '..', 'data'))
# XMLファイルのパス
action_player_client_module_xml_path = os.path.abspath(
    os.path.join(data_dir, 'action_player_client.xml'))

# --- ActionPlayerClientクラス ---
class ActionPlayerClient (object):
    def __init__ (self):
        self._context = monea.ModuleContextFactory_newContext (
            action_player_client_module_xml_path)
        self._remote_ap = self._context.getRemoteModule ('action_player')
        self._remote_ss = self._context.getRemoteModule ('speech_synthesizer')

    def play (self, name, x=0.0, y=0.0):
        builder = self._remote_ap.newProcessingRequestBuilder ('play')
        builder.characters ('actionName', name)
        builder.float32 ('x', x)
        builder.float32 ('y', y)
        builder.sendMessage ()

    def cancel (self, name):
        builder = self._remote_ap.newProcessingRequestBuilder ('cancel')
        builder.characters ('actionName', name)
        builder.sendMessage ()

    def speak (self, content):
        builder = self._remote_ss.newProcessingRequestBuilder ('speak')
        builder.characters ('content', content)
        builder.sendMessage ()

    def stop_speaking (self):
        builder = self._remote_ss.newProcessingRequestBuilder ('stop')
        builder.sendMessage ()
