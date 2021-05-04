#! /usr/bin/env python
# coding: utf-8
#####################################################
# MMDAgent SCHEMA用のActionPlayerを起動するスクリプト
#####################################################
import os
import sys
import traceback
import readline

# --- 各種設定ファイルの場所など ---
# カレントディレクトリ
current_dir = os.path.abspath(os.path.dirname(__file__))

# モジュールを読み込む場所を追加
sys.path.append (os.path.abspath(os.path.join(current_dir, '..', 'python')))

# actionフォルダの位置
action_dir  = os.path.abspath(os.path.join(current_dir, '..', 'action'))
# dataフォルダの位置
data_dir  = os.path.abspath(os.path.join(current_dir, '..', 'data'))
# XMLファイルのパス
action_player_module_xml_path = os.path.abspath(
    os.path.join(data_dir, 'sch_action_player.xml'))
speech_speaker_module_xml_path = os.path.abspath(
    os.path.join(data_dir, 'sch_speech_speaker.xml'))

# MMDAgentのホスト名，ポート番号
mmdagent_host_name = "localhost"
mmdagent_port = 7000

# --- 実際の処理 ---
import mmdagent_schema_client as msc
# import sch_ss_speaker as ss
import sch_action as sa
import sch_action_player as sap

client = msc.MMDAgentSchemaClient (mmdagent_host_name, mmdagent_port)

action_dictionary = sa.ActionDictionary ()
action_dictionary.read (action_dir)
context = sa.ActionMasterContext (action_dictionary)

# speaker = ss.SchemaSpeaker (client, speech_speaker_module_xml_path)
action_player = sap.ActionPlayer (client, context)
# action_player_monea_thread = sap.ActionPlayerMoneaThread (
#      action_player, action_player_module_xml_path)

# speaker.start ()
action_player.start ()
# action_player_monea_thread.start ()

def look(usr):
    if usr == 'A':
        action_player.put_le(20, 10)
    elif usr == 'B':
        action_player.put_le(-20, 10)
    else:
        action_player.put_ln(0, 0)

# while True:
#     try:
#         line = input('ActionPlayer> ')
#         cmds = line.split(' ')
#         if cmds[0] == 'c':
#             action_player.cancel(cmds[1])
#         elif cmds[0] == 'le':
#             yaw, pitch = float(cmds[1]), float(cmds[2])
#             action_player.put_le (yaw, pitch)
#         elif cmds[0] == 'ln':
#             yaw, pitch = float(cmds[1]), float(cmds[2])
#             action_player.put_ln (yaw, pitch)
#         elif cmds[0] == 'lt':
#             yaw, pitch = float(cmds[1]), float(cmds[2])
#             action_player.put_lt (yaw, pitch)
#         else:
#             action_player.put (cmds[0])
#     except KeyboardInterrupt:
#         break
#     except:
#         print(traceback.format_exc())
