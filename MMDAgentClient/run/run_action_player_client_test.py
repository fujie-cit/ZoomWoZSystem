#! /usr/bin/env python
# coding: utf-8
#####################################################
# ActionPlayerClientのテストプログラム
#####################################################
import os
import readline
import traceback
import sys

# カレントディレクトリ
current_dir = os.path.abspath(os.path.dirname(__file__))
# モジュールを読み込む場所を追加
sys.path.append (os.path.abspath(os.path.join(current_dir, '..', 'python')))

import action_player_client as apc

client = apc.ActionPlayerClient()

while True:
    try:
        line = raw_input('ActionPlayerClient> ')
        cmds = line.split(' ')
        if cmds[0] == 's':
            client.speak (cmds[1])
        elif cmds[0] == 'ss':
            client.stop_speaking ()
        elif cmds[0] == 'c':
            client.cancel(cmds[1])
        else:
            args = []
            for c in cmds[1:]:
                try:
                    v = float(c)
                    args.append(v)
                except ValueError:
                    v = 0.0
            args = args[:2]
            client.play (cmds[0], *args)
    except KeyboardInterrupt:
        break
    except:
        print traceback.format_exc()
        

