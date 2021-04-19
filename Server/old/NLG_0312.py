# -*- coding: utf-8 -*-

"""
MySQLデータベースを用いた発話生成
"""
__editor__ = "Hayato Katayama"
import random
import sys
import MySQLdb


class NLG:
    def __init__(self, error_rate=0.0, host="localhost", db_name="woz_system", user="root"):
        get_db_result = self.get_db(host, db_name, user)
        self.db = get_db_result[0]
        self.topic2genre = get_db_result[1]
        self.topic2yomi = get_db_result[2]
        self.utter_list = get_db_result[3]
        self.topic_list = get_db_result[4]
        self.genre_list = get_db_result[5]
        self.reset()
        self.error_rate = error_rate

    def get_db(self, host="localhost", db_name="woz_system", user="root"):
        '''
        MySQLから発話内容を一括取得

        input
          host: str
          db_name: str
          user: str

        output
          db: dict{dict{dict{dict{}}}, ... , dict{dict{}}}
          topic2genre: dict{"topic": genre}
          topic2yomi: dict{"topic": yomi}
          utter_list: list()  全発話文のリスト
          topic_list: list()  全トピック(=映画タイトル)のリスト
          genre_list: list()  全ジャンルのリスト

          db = {"genre1":
                    {"title1":
                        {"abstract"  : {},
                         "director"  : {},
                         "actor"     : {},
                         "review"    : {},
                         "evaluation": {}
                        }
                     "title2":
                        {"abstract"  : {},
                         "director"  : {},
                         "actor"     : {},
                         "review"    : {},
                         "evaluation": {}
                        }
                     "title3"
                       ...
                    }
                 "genre2":
                   ...
                 "util":
                    {"pardon": {},
                     "unknown": {},
                     "followup": {},
                     "yes": {},
                     "no": {},
                     "start": {},
                     "summarize", {},
                     "end": {}
                    }
                }
        '''

        # コネクションの確立
        connector = MySQLdb.connect(host=host, db=db_name, user=user, passwd="", charset="utf8")
        cursor = connector.cursor()  # カーソル(概念)を作成

        db = {}
        topic2genre = {}
        topic2yomi = {}
        topic_list = []
        utter_list = []
        genre_list = []

        cursor.execute('select * from genre')
        genres = cursor.fetchall()  # e.g. genres = ((1, 1, 'romance'), (2, 2, 'action'), (3, 3, 'SF'), (4, 4, 'horror'))
        for genre in genres:
            genre_id = genre[1]
            genre_name = genre[2]#.encode('utf-8')
            genre_list.append(genre_name)
            db[genre_name] = {}
            cursor.execute('select * from topic where genre_id={}'.format(genre_id))
            topics = cursor.fetchall()  # e.g. topics = ((1, 1, 'ハッピー・デスデイ', 'happy death day'), (2, 2, 'ララランド', 'ララランド')...)
            for topic in topics:
                topic_id = topic[2]
                topic_name = topic[3]#.encode('utf-8')
                topic_yomi = topic[4]#.encode('utf-8')
                db[genre_name][topic_name] = {}
                topic2yomi[topic_name] = topic_yomi
                topic2genre[topic_name] = genre_name
                topic_list.append(topic_name)

                for message in ['abstract', 'director', 'actor', 'review', 'evaluation']:
                    db[genre_name][topic_name][message] = {}
                    cursor.execute('select * from {} where topic_id={}'.format(message, topic_id))
                    fields = cursor.fetchall()
                    for field in fields:
                        id = field[0]
                        text = field[2]#.encode('utf-8')
                        db[genre_name][topic_name][message][id] = text
                        # 使うときは utterance = random.choice(db[genre_name][topic_name][message].values())
                        # でランダムに1発話取り出す仕様
                        utter_list.append(text)

        # 汎用発話セット
        db['util'] = {}
        for message in ['pardon', 'unknown', 'followup', 'yes', 'no', 'start', 'summarize', 'end']:
            db['util'][message] = {}
            cursor.execute('select * from {}'.format(message))
            fields = cursor.fetchall()
            for field in fields:
                id = field[0]
                text = field[1]#.encode('utf-8')
                db['util'][message][id] = text
                utter_list.append(text)

        cursor.close()
        connector.close()
        return db, topic2genre, topic2yomi, utter_list, topic_list, genre_list

    def reset(self):
        '''
        使用済み発話リストをリセット
        '''
        self.used = {}
        for topic in self.topic2genre.keys():
            self.used[topic] = {}
            self.used[topic]['review'] = []

    def error_generator(self):
        '''
        エラー(ノイズ)を生成
        :return: True or False
        '''
        x = random.uniform(0, 1)
        return x < self.error_rate

    def topic_random_choice(self, genre, topic_memory):
        '''
        ジャンルを指定するとトピックをランダムに選択する
        '''
        if genre not in self.genre_list:
            genre = random.choice(self.genre_list)

        num_topics = len(self.db[genre].keys())
        # そのジャンルの映画を全て推薦済みの場合
        if len(topic_memory[genre]) == num_topics:
            return None, None

        topics = list(self.db[genre].keys())
        topic = random.choice(topics)
        while topic in topic_memory[genre]:
            topics.remove(topic)
            topic = random.choice(topics)

        return topic, genre

    def generate(self, order, topic_memory, topic='', isActiveDetail=False):
        '''
        条件に応じた発話を生成
        :param message: メッセージ(情報)の種別
        # :param genre: 映画ジャンル
        :param topic: トピック (映画タイトル) (str)
        :return: 発話 (条件に当てはまらないものは''で返す) (str)
                (message, kwargs**):　発話内容
            --recommend--
            1.  ('recommendation', topic): 'だったら、{topic}がおすすめだよ'
            --knowledge--
            2.  ('review', topic): レビュー e.g. 'アナ雪の100倍面白いってさ'
            3.  ('actor', topic): 出演者 e.g. '主演は...'
            4.  ('director', topic): 監督 e.g. '監督は...'
            5.  ('evaluation', topic): 評価 e.g. '{topic}の評価は{point}点だよ'
            6.  ('abstract', topic): 概要 e.g. 'XXがYYする映画なんだよ'
            7. ('title', topic): 映画タイトル  'XXだよ'
            8. ('genre', topic): 映画ジャンル 'XXだよ'
            ---util---
            9.  ('pardon', *): 聞き返し e.g. 'もう一回言って？'
            10.  ('unknown', *): 回答不能 e.g. 'ちょっとわからないなぁ'
            11.  ('followup', *): フォローアップ e.g. 'なるほど'
            12. ('yes', *): 肯定 e.g. 'そうだよ'
            13. ('no', *): 否定 e.g. 'ちがうよ'
            --question--
            14. ('question', topic): 質問 e.g. 'XXは興味ある？'
            --check--
            15. ('check', *): 確認 e.g. '観に行く映画はきまった？'
            --start--
            16. ('start', *): 開始 e.g. 'どんな映画が観たいの？'
            --end--
            17. ('end', *): 終了 e.g. 'いってらっしゃい'
        '''

        # エラー生成（ランダム発話生成）
        # if self.error_generator():
        #     return random.choice(self.utter_list)

        if 'recommendation' in order:
            if topic is None:
                utterance = 'ごめん、もうこれ以上は知らないな'
            else:
                utterance = 'じゃあ{}、はどうかな？'.format(self.topic2yomi[topic])

        elif order in ['actor', 'director', 'abstract']:
            utterance = random.choice(list(self.db[self.topic2genre[topic]][topic][order].values()))

        elif order == 'review':
            if len(self.used[topic][order]) == len(list(self.db[self.topic2genre[topic]][topic][order].values())):
                self.used[topic][order] = []
            utterance = random.choice(list(self.db[self.topic2genre[topic]][topic][order].values()))
            while utterance in self.used[topic][order]:
                utterance = random.choice(list(self.db[self.topic2genre[topic]][topic][order].values()))
            self.used[topic]['review'].append(utterance)

        elif order in ['pardon', 'unknown', 'followup', 'yes', 'no', 'summarize', 'start', 'end']:
            utterance = random.choice(list(self.db['util'][order].values()))

        elif order == 'title':
            utterance = '{}だよ'.format(self.topic2yomi[topic])

        elif order == 'evaluation':
            # utterance = '{0}の評価は、5点満点中{1}点だよ'.format(self.topic2yomi[topic],
            #                                         self.db[self.topic2genre[topic]][topic][message].values()[0])
            utterance = '評価は、5点満点中{0}点だよ'.format(list(self.db[self.topic2genre[topic]][topic][order].values())[0])

        elif order == 'genre':
            utterance = '{}だよ'.format(self.topic2genre[topic])

        elif order == 'question':
            utterance = random.choice(['{}、は興味ある？'.format(self.topic2yomi[topic]),
                                       '{}、はみたいと思う？'.format(self.topic2yomi[topic])])

        else:
            assert False, 'Unknown order: {}'.format(order)

        return utterance
