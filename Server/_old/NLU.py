# -*- coding: utf-8 -*-

"""
言語理解モジュール
"""
__author__ = "Yuto Akagawa"
__editor__ = "Hayato Katayama"

import os
import pandas as pd
# import time
# from monea_connector import MoneaConnector
# import threading
# from logger import Logger
import MySQLdb
from model import BertClassifier
import torch
from transformers import BertJapaneseTokenizer, BertModel, BertConfig
os.environ["REGISTRY_SERVER_PORT"] = "25001"
csv_dir = '../data/text'


class RecognitionResultManager:
    def __init__(self):
        pass
        # self.text_df = self.get_df()  # 発話内容のログ

    def get_df(self):
        csv_list = [name for name in os.listdir(csv_dir) if '.csv' in name]
        csv_list = sorted(csv_list)
        df = pd.read_csv(os.path.join(csv_dir, csv_list[-1]))
        return df


class NLU:
    def __init__(self, config, RecognitionResultManager):
        self.config = config
        self.genre_keywords_db = self.get_db(self.config['DB']['host'], self.config['DB']['db_name'], self.config['DB']['user'])
        self.rrm = RecognitionResultManager

        self.model_path = "/Users/jinsakuma/Downloads/model_gpu_v4.3.3.pth"
        self.model_config = BertConfig.from_pretrained('cl-tohoku/bert-base-japanese-whole-word-masking', output_attentions=True)
        self.tokenizer = BertJapaneseTokenizer.from_pretrained('cl-tohoku/bert-base-japanese-whole-word-masking')
        self.bert_model = BertModel.from_pretrained('cl-tohoku/bert-base-japanese-whole-word-masking', config=self.model_config)
        self.model = BertClassifier(self.bert_model)
        self.max_len = 30
        self.load_weights(self.model_path)

        self.device = torch.device("cpu")

        self.order_list = ['recommendation', 'title', 'abstract', 'review',
                           'evaluation', 'actor', 'genre', 'director', None]

    def get_db(self, host="localhost", db_name="woz_system", user="root"):
        '''
        MySQLから発話内容を一括取得
        :return: db (dict)
        '''
        connector = MySQLdb.connect(host=host, db=db_name, user=user, passwd="", charset="utf8")
        cursor = connector.cursor()  # カーソル(概念)を作成
        # 映画推薦用キーワード
        cursor.execute('select * from genre')
        genres = cursor.fetchall()
        genre_keywords_db = {}
        for genre in genres:
            genre_id = genre[1]
            genre_type = genre[2]  # .encode('utf-8')
            genre_keywords_db[genre_type] = []
            cursor.execute('select keywords from genre_keywords where genre_id={}'.format(genre_id))
            keywords = cursor.fetchall()
            keyword_list = keywords[0][0].split(",")
            genre_keywords_db[genre_type] = keyword_list
        return genre_keywords_db

    def load_weights(self, model_path):
        load_weights = torch.load(model_path, map_location={'cuda:0': 'cpu'})
        self.model.load_state_dict(load_weights)

    def bert_tokenizer(self, input_text):
        return self.tokenizer.encode(input_text, max_length=self.max_len, truncation=True, return_tensors='pt')[0]

    def get_order(self, input_text):
        token = self.bert_tokenizer(input_text)
        token = token.unsqueeze(0)
        output, attentions = self.model(token.to(self.device))
        _, pred = torch.max(output, 1)

        print("NLU result: ", self.order_list[pred.item()])
        return self.order_list[pred.item()]

    def get_text(self, N):
        df = self.rrm.get_df()
        text_list = df['transcript'].iloc[-N:].tolist()
        target_list = df['speaker'].iloc[-N:].tolist()
        return text_list, target_list

    def check_genre(self, input_texts):
        # キーワードマッチング
        for text in reversed(input_texts):
            for response_type, keywords in self.genre_keywords_db.items():
                for keyword in keywords:
                    if keyword in text:
                        return response_type

        return None

    # def get_db(self, host="localhost", db_name="woz_system", user="root"):
    #     '''
    #     MySQLから発話内容を一括取得
    #     :return: db (dict)
    #     '''
    #     # 発話選択用キーワード
    #     connector = MySQLdb.connect(host=host, db=db_name, user=user, passwd="", charset="utf8")
    #     cursor = connector.cursor()  # カーソル(概念)を作成
    #     cursor.execute('select * from response')
    #     responses = cursor.fetchall()
    #     keywords_db = {}
    #     for response in responses:
    #         response_id = response[1]
    #         response_type = response[2].encode('utf-8')
    #         keywords_db[response_type] = []
    #         cursor.execute('select keywords from keywords where topic_id={}'.format(response_id))
    #         keywords = cursor.fetchall()
    #         keyword_list = keywords[0][0].split(",")
    #         keywords_db[response_type] = keyword_list
    #
    #     # 映画推薦用キーワード
    #     cursor.execute('select * from genre')
    #     genres = cursor.fetchall()
    #     genre_keywords_db = {}
    #     for genre in genres:
    #         genre_id = genre[1]
    #         genre_type = genre[2].encode('utf-8')
    #         genre_keywords_db[genre_type] = []
    #         cursor.execute('select keywords from genre_keywords where genre_id={}'.format(genre_id))
    #         keywords = cursor.fetchall()
    #         keyword_list = keywords[0][0].split(",")
    #         genre_keywords_db[genre_type] = keyword_list
    #     return keywords_db, genre_keywords_db
    #
    # def check_keyword(self):  # response_typeを決める(推薦、概要、評価、など)
    #     while self.rrm.get_recognizing():
    #         print("wait")
    #         time.sleep(0.01)
    #         continue
    #     spreco_memory = self.rrm.get_spreco_memory()  # 発話履歴を参照
    #     result = self.calculate_score(self.init_result(spreco_memory), spreco_memory, self.keywords_db)#(推薦,他の映画教えて)
    #     response_type = None
    #     # 直近でマッチしたresponse_typeを適用する
    #     for i in reversed(range(len(result))):
    #         if len(result[i]) > 0:
    #             response_type = result[i][-1][0]
    #             # １度言った応答発話を繰り返さないようにする
    #             spreco = result[i][-1][1]
    #             # if response_type!="recommendation":self.rrm.pop_spreco_memory(spreco)#####
    #             # self.rrm.pop_spreco_memory(spreco)
    #             break
    #     return response_type
    #
    # def select_genre(self, conv_manager):
    #     while self.rrm.get_recognizing():
    #         continue
    #     spreco_memory = self.rrm.get_spreco_memory()
    #     result = self.calculate_score(self.init_result(spreco_memory), spreco_memory, self.genre_keywords_db)
    #     genre_type = conv_manager.get_current_genre()
    #     # 直近でマッチしたresponse_typeを適用する
    #
    #     for i in reversed(range(len(result))):
    #         if len(result[i]) > 0:
    #             genre_type = result[i][-1][0]
    #             spreco = result[i][-1][1]
    #             conv_manager.set_current_genre(genre_type)
    #             # self.rrm.pop_spreco_memory(spreco)#####
    #             break
    #     return genre_type
    #
    # def init_result(self, spreco_memory):
    #     # マッチしたresponse_typeを格納するディクショナリを初期化
    #     result = {}
    #     for i in range(len(spreco_memory)):
    #         result[i] = []
    #     return result
    #
    # def calculate_score(self, result, spreco_memory, keywords_db):
    #     # キーワードマッチング
    #     for (i, spreco) in enumerate(spreco_memory):
    #         for response_type, keywords in keywords_db.iteritems():
    #             for keyword in keywords:
    #                 if keyword in spreco.decode("utf-8"):
    #                     result[i].append([response_type, spreco])  # response_typeは推薦や概要、sprecoはキーワードマッチングした時の話者の発話内容
    #     return result


"""
if __name__ == '__main__':
    l = Logger()
    connector = MoneaConnector('../config/moduleWoz.xml')
    time.sleep(1)
    remoteA = connector.context.getRemoteModule('SR2')
    rrm = RecognitionResultManager(remoteA, l,"A")
    nlu = NLU(rrm)
    #print "waiting"
    time.sleep(15)
    print(1)
    #print "analyzing"
    response_type = nlu.check_keyword()
    print response_type
"""
