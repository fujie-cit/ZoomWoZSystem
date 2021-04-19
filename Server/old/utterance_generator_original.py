# -*- coding: utf-8 -*-

"""
MySQLデータベースを用いた発話生成
"""
__editor__ = "Hayato Katayama"
import random
import sys
import MySQLdb


class UtteranceGenerator:

    def __init__(self, error_rate=0.0, host="localhost", db_name="woz_system", user="root"):
        self.db, self.topic2genre, self.topic2yomi, self.utter_list, self.topic_list, self.genre_list = self.get_db(host, db_name, user)
        self.reset()
        self.error_rate=error_rate

    def get_db(self, host="localhost", db_name="woz_system", user="root"):
        '''
        MySQLから発話内容を一括取得
        :return: db (dict)
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
        genres = cursor.fetchall()
        # e.g. genres = ((1, 1, 'romance'), (2, 2, 'action'), (3, 3, 'SF'), (4, 4, 'horror'))
        for genre in genres:
            genre_id = genre[1]
            genre_name = genre[2].encode('utf-8')
            genre_list.append(genre_name)
            db[genre_name] = {}
            cursor.execute('select * from topic where genre_id={}'.format(genre_id))
            topics = cursor.fetchall()
            # e.g. topics = ((1, 1, '美女と野獣'), (2, 2, 'ララランド'), (3, 3, 'ピーチガール'))
            for topic in topics:
                topic_id = topic[2]
                topic_name = topic[3].encode('utf-8')
                topic_yomi = topic[4].encode('utf-8')
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
                        text = field[2].encode('utf-8')
                        db[genre_name][topic_name][message][id] = text
                        # 使うときは utterance = random.choice(db[genre_name][topic_name][message].values())
                        # でランダムに1発話取り出す仕様
                        utter_list.append(text)
        # 汎用発話セット
        db['util'] ={}
        for message in ['pardon', 'unknown', 'followup', 'yes', 'no', 'start', 'summarize', 'end']:
            db['util'][message] = {}
            cursor.execute('select * from {}'.format(message))
            fields = cursor.fetchall()
            for field in fields:
                id = field[0]
                text = field[1].encode('utf-8')
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
        x = random.uniform(0,1)
        return x < self.error_rate

    def random_choice(self, genre, topic_memory, c=0):
        '''
        ジャンルを指定するとトピックをランダムに選択する
        '''
        if genre not in self.genre_list: genre=None

        if genre == None :
            genre = random.choice(self.genre_list)

        num_topics = len(self.db[genre].keys())
        if len(topic_memory[genre]) == num_topics:#そのジャンルの映画を推薦済み、つまりジャンル変更
            if c == 1:
                c = 0
                return None,None
            genres = self.genre_list
            random.shuffle(genres)
            for g in genres:
                num_topics = len(self.db[g].keys())
                if len(topic_memory[g]) != num_topics:
                    genre = g
                    break

        num_topics = len(self.db[genre].keys())
        if len(topic_memory.get(genre)) == num_topics:
            if not genre == None:
                return None, None

        topic = random.choice(self.db[genre].keys())
        cnt=0
        while topic in topic_memory[genre]:
            topic = random.choice(self.db[genre].keys())
        return topic, genre

    def generate(self, message, topic_memory, topic='', isActiveDetail=False):
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
            ---util---
            7.  ('pardon', *): 聞き返し e.g. 'もう一回言って？'
            8.  ('unknown', *): 回答不能 e.g. 'ちょっとわからないなぁ'
            9.  ('followup', *): フォローアップ e.g. 'なるほど'
            10. ('yes', *): 肯定 e.g. 'そうだよ'
            11. ('no', *): 否定 e.g. 'ちがうよ'
            12. ('title', topic): 映画タイトル  'XXだよ'
            13. ('genre', topic): 映画ジャンル 'XXだよ'
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
        if self.error_generator():
            return random.choice(self.utter_list)

        elif 'recommendation' in message:
            if topic == None:
                utterance = 'ごめん、もうこれ以上は知らないな'
            else:
                utterance = 'じゃあ{}、はどうかな？'.format(self.topic2yomi[topic])

        elif message in ['actor', 'director', 'abstract']:
            utterance = random.choice(self.db[self.topic2genre[topic]][topic][message].values())

        elif message == 'review':
            if len(self.used[topic][message]) == len(self.db[self.topic2genre[topic]][topic][message].values()):
                self.used[topic][message] = []
            utterance = random.choice(self.db[self.topic2genre[topic]][topic][message].values())
            while utterance in self.used[topic][message]:
                utterance = random.choice(self.db[self.topic2genre[topic]][topic][message].values())
            self.used[topic]['review'].append(utterance)

        elif message in ['pardon', 'unknown', 'followup', 'yes', 'no', 'summarize', 'start', 'end']:
            utterance = random.choice(self.db['util'][message].values())

        elif message == 'title':
            utterance = '{}だよ'.format(self.topic2yomi[topic])

        elif message == 'evaluation':
            #utterance = '{0}の評価は、5点満点中{1}点だよ'.format(self.topic2yomi[topic],
            #                                         self.db[self.topic2genre[topic]][topic][message].values()[0])
            utterance = '評価は、5点満点中{0}点だよ'.format(self.db[self.topic2genre[topic]][topic][message].values()[0])

        elif message == 'genre':
            utterance = '{}だよ'.format(self.topic2genre[topic])

        elif message == 'question':
            utterance = random.choice(['{}、は興味ある？'.format(self.topic2yomi[topic]),
                                       '{}、はみたいと思う？'.format(self.topic2yomi[topic])])

        else:
            return "ごめん、もう1回言って"

        return utterance
"""
if __name__ == '__main__':
    ug = UtteranceGenerator()
    for i in ug.utter_list:
        print i
"""
