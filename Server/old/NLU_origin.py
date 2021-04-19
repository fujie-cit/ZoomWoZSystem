# -*- coding: utf-8 -*-

"""
言語理解モジュール
"""
__author__ = "Yuto Akagawa"
__editor__ = "Hayato Katayama"

import os
import os.path
import time
# from monea_connector import MoneaConnector
import threading
from logger import Logger
import MySQLdb
os.environ["REGISTRY_SERVER_PORT"] = "25001"


class RecognitionResultManager:
    def __init__(self, remote, logger, personID):
        self.remote = remote
        self.logger = logger
        self.spreco_memory = []
        self.recognizing = ""
        self.personID = personID
        thr = threading.Thread(target=self.watcher)
        thr.setDaemon(True)
        thr.start()

    def watcher(self):
        pretext = ''
        while 1:
            self.remote.timedUpdate(-1)
            # order = self.remote.getAsString("01_RecognizeText").decode("euc-jp")
            spreco = self.remote.getAsString("01_RecognizeText")
            recognizing = self.remote.getAsString("Recognizing")
            audioID = self.remote.getAsString("AudioID")
            self.set_recognizing(recognizing)
            if pretext != spreco and spreco != "" and recognizing == "0":
                print(spreco)
                self.set_spreco(spreco)
                # 認識結果のログを残す
                self.logger.stamp("SpReco", "NONE", self.personID, spreco)
                pretext = spreco

    def set_spreco(self, spreco):
        """
        認識結果を保存しておく
        """
        if spreco != "":
            self.spreco_memory.append(spreco)
            if len(self.spreco_memory) > 15:
                self.spreco_memory.pop(0)

    def set_recognizing(self, recognizing):
        if recognizing == "1":
            self.recognizing = True
        else:
            self.recognizing = False

    def get_recognizing(self):
        return self.recognizing

    def get_spreco_memory(self):
        return self.spreco_memory

    def pop_spreco_memory(self, element):
        print("pop")
        index = self.spreco_memory.index(element)
        self.spreco_memory.pop(index)

    """
    reset_spreco_memoryは2018/6/7に追加
    ：Systemが応答するたびにA,Bの発話履歴を消してしまおう
    """
    def reset_spreco_memory(self):
        self.spreco_memory = []


class NLU:
    def __init__(self, RecognitionResultManager, host="localhost", db_name="woz_system", user="root"):
        self.keywords_db, self.genre_keywords_db = self.get_db(host, db_name, user)
        self.rrm = RecognitionResultManager

    def get_db(self, host="localhost", db_name="woz_system", user="root"):
        '''
        MySQLから発話内容を一括取得
        :return: db (dict)
        '''
        # 発話選択用キーワード
        connector = MySQLdb.connect(host=host, db=db_name, user=user, passwd="", charset="utf8")
        cursor = connector.cursor()  # カーソル(概念)を作成
        cursor.execute('select * from response')
        responses = cursor.fetchall()
        keywords_db = {}
        for response in responses:
            response_id = response[1]
            response_type = response[2].encode('utf-8')
            keywords_db[response_type] = []
            cursor.execute('select keywords from keywords where topic_id={}'.format(response_id))
            keywords = cursor.fetchall()
            keyword_list = keywords[0][0].split(",")
            keywords_db[response_type] = keyword_list

        # 映画推薦用キーワード
        cursor.execute('select * from genre')
        genres = cursor.fetchall()
        genre_keywords_db = {}
        for genre in genres:
            genre_id = genre[1]
            genre_type = genre[2].encode('utf-8')
            genre_keywords_db[genre_type] = []
            cursor.execute('select keywords from genre_keywords where genre_id={}'.format(genre_id))
            keywords = cursor.fetchall()
            keyword_list = keywords[0][0].split(",")
            genre_keywords_db[genre_type] = keyword_list
        return keywords_db, genre_keywords_db

    def check_keyword(self):  # response_typeを決める(推薦、概要、評価、など)
        while self.rrm.get_recognizing():
            print("wait")
            time.sleep(0.01)
            continue
        spreco_memory = self.rrm.get_spreco_memory()  # 発話履歴を参照
        result = self.calculate_score(self.init_result(spreco_memory), spreco_memory, self.keywords_db)#(推薦,他の映画教えて)
        response_type = None
        # 直近でマッチしたresponse_typeを適用する
        for i in reversed(range(len(result))):
            if len(result[i]) > 0:
                response_type = result[i][-1][0]
                # １度言った応答発話を繰り返さないようにする
                spreco = result[i][-1][1]
                # if response_type!="recommendation":self.rrm.pop_spreco_memory(spreco)#####
                # self.rrm.pop_spreco_memory(spreco)
                break
        return response_type

    def select_genre(self, conv_manager):
        while self.rrm.get_recognizing():
            continue
        spreco_memory = self.rrm.get_spreco_memory()
        result = self.calculate_score(self.init_result(spreco_memory), spreco_memory, self.genre_keywords_db)
        genre_type = conv_manager.get_current_genre()
        # 直近でマッチしたresponse_typeを適用する

        for i in reversed(range(len(result))):
            if len(result[i]) > 0:
                genre_type = result[i][-1][0]
                spreco = result[i][-1][1]
                conv_manager.set_current_genre(genre_type)
                # self.rrm.pop_spreco_memory(spreco)#####
                break
        return genre_type

    def init_result(self, spreco_memory):
        # マッチしたresponse_typeを格納するディクショナリを初期化
        result = {}
        for i in range(len(spreco_memory)):
            result[i] = []
        return result

    def calculate_score(self, result, spreco_memory, keywords_db):
        # キーワードマッチング
        for (i, spreco) in enumerate(spreco_memory):
            for response_type, keywords in keywords_db.iteritems():
                for keyword in keywords:
                    if keyword in spreco.decode("utf-8"):
                        result[i].append([response_type, spreco])  # response_typeは推薦や概要、sprecoはキーワードマッチングした時の話者の発話内容
        return result


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
