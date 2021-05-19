# -*- coding: utf-8 -*-

"""
会話状況管理
"""
__editor__ = "Jin Sakuma"

import os
import copy
import random
import datetime
import pandas as pd
from utils import CSVProcessing


class LogManager:
    def __init__(self, config):
        self.config = config

        # csvファイル
        self.csv = CSVProcessing()
        now = datetime.datetime.now()
        name = now.strftime("%Y%m%d%H%M")
        self.log_dir = os.path.join(self.config['Log']['dir'], name)
        os.makedirs(self.log_dir, exist_ok=True)

        # 音声認識のログ
        self.path_asr_log = os.path.join(self.log_dir, 'asr.csv')
        self.csv.write(self.path_asr_log, ['speaker', 'text'])

        # NLU結果とシステムの行動の履歴
        self.path_main_log = os.path.join(self.log_dir, 'main.csv')
        self.path_slot_log = os.path.join(self.log_dir, 'slot.csv')
        self.path_value_log = os.path.join(self.log_dir, 'value.csv')
        self.csv.write(self.path_main_log, ['id', 'time', 'action', 'target', 'topic', 'command', 'state', 'type', 'done'])
        self.csv.write(self.path_slot_log, ['id', 'slot_key', 'slot_value'])
        self.csv.write(self.path_value_log, ['id', 'value'])
        self.id_cnt = 0

        # キャッシュ
        self.target = 'NONE'
        self.topic_cash_list = {'title': [], 'mid': []}  # コントローラーに表示するために頻繁にアクセスするためキャッシュする
        self.person_cash_list = []  # コントローラーに表示するために頻繁にアクセスするためキャッシュする
        self.command_cash_list = []  # コントローラーに表示するために頻繁にアクセスするためキャッシュする
        self.genre_cash_list = []

    def get_main_data_dict(self):
        data_dict = {'id': None, 'time': None, 'action': None,
                     'target': None, 'topic': None, 'command': None,
                     'state': 0, 'type': 'passive', 'done': 0
                     }

        return data_dict

    def write_asr_log(self, speaker, text):
        self.csv.write(self.path_asr_log, [speaker, text])

    def write(self, data_dict, slot, value_list):
        now = datetime.datetime.now()
        time = now.strftime("%Y%m%d%H%M%S.") + "%d" % (now.microsecond / 10000)
        data_dict['time'] = time
        id = str(self.id_cnt)
        data_dict['id'] = id
        self.csv.write(self.path_main_log, list(data_dict.values()))

        for data in value_list:
            self.csv.write(self.path_value_log, [id, data])

        for key, value in list(slot.items()):
            self.csv.write(self.path_slot_log, [id, str(key), str(value)])

        self.id_cnt += 1

        return id

    def exec_log(self, id):
        df_main = self.read(self.path_main_log)
        df_main['done'].iloc[int(id)] = int(1)
        self.csv.to_csv(df_main, self.path_main_log)

    def read(self, path):
        df_log = pd.read_csv(path, encoding="utf-8-sig")
        return df_log

    def get_intoduced_list(self, command, id):
        '''
        commandごとの履歴検索
        param: command 命令コマンド (str)
        param: id csvのカラム「topic」に記録しているid(mid or pid) (int)

        return: 過去の出力のリスト (list)
                ex. (command->cast, id-><mid>)
                    -> ['Boyd Holbrook', 'Thomas Jane', 'Keegan-Michael Key']
        '''
        df_main = self.read(self.path_main_log)
        df_value = self.read(self.path_value_log)
        df_main = df_main[df_main['topic'] == id]
        df_main = df_main[df_main['done'] == 1]
        df_main = df_main[df_main['command'] == command]
        id_list = df_main['id'].tolist()
        df_value = df_value[df_value['id'].isin(id_list)]
        introduced_list = df_value['value'].tolist()
        return introduced_list

    def get_not_used_active_command(self, mid):
        df_main = self.read(self.path_main_log)
        df_main = df_main[df_main['topic'] == mid]
        df_main = df_main[df_main['done'] == 1]
        df_main = df_main[df_main['state'] == 0]
        used_command_list = list(set(df_main['command'].tolist()))
        detail_command_list = []
        for com in ["tips", "review", "evaluation", "cast", "director"]:
            if com not in used_command_list:
                detail_command_list.append(com)

        return random.choice(detail_command_list)

    def set_topic_cash(self, title, movie_id):
        if len(self.topic_cash_list['mid']) == 0:
            self.topic_cash_list['title'].append(title)
            self.topic_cash_list['mid'].append(movie_id)

        elif self.topic_cash_list['mid'][-1] != movie_id:
            self.topic_cash_list['title'].append(title)
            self.topic_cash_list['mid'].append(movie_id)

        else:
            pass

    def set_person_cash(self, person_name):
        if len(self.person_cash_list) == 0:
            self.person_cash_list.append(person_name)

        elif self.person_cash_list[-1] != person_name:
            self.person_cash_list.append(person_name)
        else:
            pass

    def set_command(self, command):
        self.command_cash_list.append(command)

    def set_genre(self, genre):
        self.genre_cash_list.append(genre)

    def set_review(self, topic, review):
        self.topic_review_hitory_dict[topic].append(review)

    def set_target(self, target):
        self.target = target

    def get_topic_title(self):
        if len(self.topic_cash_list['title']) > 0:
            return self.topic_cash_list['title'][-1]
        else:
            return None

    def get_topic_mid(self):
        if len(self.topic_cash_list['mid']) > 0:
            return self.topic_cash_list['mid'][-1]
        else:
            return None

    def search_mid_by_title(self, title):
        idx = self.topic_cash_list['title'].index(title)
        mid = self.topic_cash_list['mid'][idx]
        return mid

    def get_topic_person(self):
        if len(self.person_cash_list) > 0:
            return self.person_cash_list[-1]
        else:
            return None

    def get_current_genre(self):
        if len(self.genre_cash_list) > 0:
            return self.genre_cash_list[-1]
        else:
            return None

    def get_target(self):
        return self.target

    def get_topic_history(self):
        return copy.copy(self.topic_cash_list['title'])

    def get_person_history(self):
        return copy.copy(self.person_cash_list)

    def get_mid_history(self):
        return copy.copy(self.topic_cash_list['mid'])

    def get_command_history(self):
        return copy.copy(self.command_cash_list)

    def get_topic_review_history(self, topic):
        return self.topic_review_hitory_dict[topic]  # レビュー文の入ったリスト

    def flash_topic_history_list(self):
        self.topic_history_list = {'title': [], 'mid': []}
