# -*- coding: utf-8 -*-
"""
Robot身体制御
"""
__author__ = "Yuto Akagawa"
__editor__ = "Hayato Katayama"
import os.path
import sys
from STT import STT
from NLG import NLG
from DM import DM
import configparser

os.environ["REGISTRY_SERVER_PORT"] = "25001"

# sys config
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
WHITE = '\033[37m'
END = '\033[0m'


class RobotController:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini', encoding='utf-8')
        self.stt = STT()
        self.nlg = NLG(self.config)
        self.dialog_manager = DM(self.config)

        self.utterance_candidate = {'id': None, 'command': None, 'utterance': None, 'topic': None, 'mid': None}
        self.active_command = None

        self.preorder = ""
        self.genre_flg = False  # ジャンル誤り訂正フラグ

        # 音声認識を別スレッドで開始する
        self.stt.start()

    def control_face(self):
        # while 1:
        #     key = getch.getch()
        #     if key == "j":  # J: Look A
        #         self.look("A")
        #     elif key == "k":  # K: Nod
        #         self.nod()
        #     elif key == "l":  # L: Look B
        #         self.look("B")
        raise NotImplementedError()

    def look(self, target):
        # TODO: ロボット画像(アニメーション)の視線変更
        # print('命令文: look, target: {}'.format(str(target)))
        # self.logger.stamp('look', 'NONE', target, 'NONE')
        topics = self.dialog_manager.logger.get_topic_history()
        persons = self.dialog_manager.logger.get_person_history()
        return topics, persons

    def nod(self, target):
        # order = 'nod'
        print('命令文: nod' + target)
        # self.logger.stamp('nod', 'NONE', target, 'NONE')
        topics = self.dialog_manager.logger.get_topic_history()
        persons = self.dialog_manager.logger.get_person_history()
        return topics, persons

    def change_topic_title(self, title):
        '''
        会話のトピック(映画タイトル)を変更する
        '''
        mid = self.dialog_managersearch_mid_by_title(title)
        self.dialog_manager.set_topic_cash(title, mid)

        topics = self.dialog_manager.logger.get_topic_history()
        persons = self.dialog_manager.logger.get_person_history()
        return topics, persons

    def change_topic_person(self, person):
        '''
        会話のトピック(人物)を変更する
        '''
        self.dialog_manager.logger.set_person_cash(person)

        topics = self.dialog_manager.logger.get_topic_history()
        persons = self.dialog_manager.logger.get_person_history()
        return topics, persons

    def change_genre(self, genre, target):
        '''
        推薦ジャンルを変更する
        target: topicを変えた人(R:robot, U:user)
        '''
        # genre = genre.decode("utf-8")
        genre_list = {"romance": "ロマンス", "SF": "SF", "action": "アクション", "horror": "ホラー", "human": "ヒューマンドラマ",
                      "anime": "アニメーション映画", "comedy": "コメディー", "advenchar": "アドベンチャー", "mistery": "ミステリー"}
        genre = genre_list[genre]
        self.conv_manager.set_current_genre(genre)
        self.genre_flg = True
        # self.logger.stamp('change_genre', genre, target, 'NONE')
        topics = self.dialog_manager.logger.get_topic_history()
        persons = self.dialog_manager.logger.get_person_history()
        return topics, persons

    def set_utterance(self, utterance):
        """
        systemの発話履歴の記録
        input:
            utterance: str systemの発話文
        """
        self.utterance_history.append(utterance)

    def send_message(self, message):
        # builder = self.remote_ad.newProcessingRequestBuilder('play')
        # builder.characters('actionName', message.decode('utf-8').encode('euc_jp'))
        # builder.sendMessage()
        raise NotImplementedError()

    def main(self, target, text):

        self.look(target)
        sys.stdout.write(GREEN)
        sys.stdout.write("\033[K")
        sys.stdout.write("{}: ".format(target) + text + "\n")
        sys.stdout.write(END)

        # 音声認識のログを取る
        self.dialog_manager.logger.write_asr_log(target, text)

        # 能動発話候補をあらかじめ算出しておく
        title = self.dialog_manager.logger.get_topic_title()
        mid = self.dialog_manager.logger.get_topic_mid()
        slot = {'title': title, 'history': None}
        self.active_command = self.dialog_manager.logger.get_not_used_active_command(mid)

        # TODO: NLU
        command = "recommendation"
        slot = {"genre": 12, "person": None, "sort_by": None, "history": None}

        # DM
        output, id = self.dialog_manager.main(command, slot, target)
        if 'topic' in output.keys():
            topic = output['topic']
            mid = output['mid']
        else:
            topic = None
            mid = None

        if 'person_list' in output.keys():
            person_name_list = output['person_list']
        else:
            person_name_list = None

        # NLG
        utterance = self.nlg.generate(command, slot, output)

        self.utterance_candidate = {'id': id, 'command': command, 'utterance': utterance,
                                    'topic': topic, 'mid': mid, 'person_list': person_name_list}

        self.look(target)
        sys.stdout.write(YELLOW)
        sys.stdout.write("\033[K")
        sys.stdout.write("Robot: " + utterance + "\n")
        sys.stdout.write("能動発話候補: " + self.active_command + "\n")
        sys.stdout.write(END)

        topics = self.dialog_manager.logger.get_topic_history()
        persons = self.dialog_manager.logger.get_person_history()
        return topics, persons

    def utter(self, message, target):
        """
        input:
          message: str ... 行動タイプ
          target: str  ... ユーザ(A or B)

        output:
          topic_list: list(str) ... トピックの履歴の1次元リスト

        処理内容
          orderの決定
          　topicの確認
          　genreの確認・変更
          発話生成
          音声合成
        """

        utterance = None

        # orderの決定
        # 応答
        if "response-passive" in message:
            if self.utterance_candidate['command'] is not None:
                self.dialog_manager.logger.set_command(self.utterance_candidate['command'])
                utterance = self.utterance_candidate['utterance']
                self.dialog_manager.logger.exec_log(self.utterance_candidate['id'])

                if self.utterance_candidate['topic'] is not None:
                    topic = self.utterance_candidate['topic']
                    mid = self.utterance_candidate['mid']
                    self.dialog_manager.logger.set_topic_cash(topic, mid)

                if self.utterance_candidate['person_list'] is not None:
                    person_name_list = self.utterance_candidate['person_list']
                    for person_name in person_name_list:
                        self.dialog_manager.logger.set_person_cash(person_name)
            else:
                pass

        # 能動発話　詳細("abstract", "review", "evaluation", "actor", "director")
        elif "detail-active" in message:
            command = self.active_command
            self.dialog_manager.logger.set_command(command)
            slot = None
            output, id = self.dialog_manager.main(command, slot, target, type='active')
            self.dialog_manager.logger.exec_log(id)
            if 'topic' in output.keys():
                if output['topic'] is not None:
                    topic = output['topic']
                    mid = output['mid']
                    self.dialog_manager.logger.set_topic_cash(topic, mid)

            if 'person_list' in output.keys():
                if output['person_list'] is not None:
                    person_name_list = output['person_list']
                    for person_name in person_name_list:
                        self.dialog_manager.logger.set_person_cash(person_name)

            utterance = self.nlg.generate(command, slot, output)

        # yes, no, unknown
        elif "yes-passive" in message or "no-passive" in message or "unknown-passive" in message:
            # self.logger.stamp(message, topic, target, "Recognizing")
            command = message.replace("-passive", "", 1)
            self.dialog_manager.logger.set_command(command)
            slot = None
            output, id = self.dialog_manager.main(command, slot, target, type='correction')
            self.dialog_manager.logger.exec_log(id)
            utterance = self.nlg.generate(command, slot, output)

        # 前の発話の繰り返し
        elif "repeat" in message:
            command = "repeat"
            self.dialog_manager.logger.set_command(command)
            slot = None
            output, id = self.dialog_manager.main(command, slot, target, type='correction')
            self.dialog_manager.logger.exec_log(id)
            if 'topic' in output.keys():
                if output['topic'] is not None:
                    topic = output['topic']
                    mid = output['mid']
                    self.dialog_manager.logger.set_topic_cash(topic, mid)

            utterance = self.nlg.generate(command, slot, output)

        # 誤り訂正発話
        else:
            # 推薦の訂正
            if "recommendation" in message:
                # TODO: 実装
                raise NotImplementedError()
                # command = "recommendation"
                # if self.genre_flg:  # すでに手動でジャンルを選んでいる場合
                #     genre = self.conv_manager.get_current_genre()
                #     self.genre_flg = False
                # else:
                #     # TODO: ジャンルの決定
                #     text_list, target_list = self.nlu.get_text(N=2)
                #     genre = self.nlu.check_genre(text_list)
                #
                # topic, genre = self.utterance_generator.topic_random_choice(genre, topic_memory)
                # if topic is not None:
                #     self.change_topic(topic, "R", genre)
                # elif topic is None and genre is None:
                #     order = "stock-empty"

            # yes, no, unknown, repeatの訂正
            elif message.replace("-correction", "", 1) in ["no", "yes", "unknown", "repeat"]:
                command = message.replace("-correction", "", 1)
                self.dialog_manager.logger.set_command(command)
                slot = None
                output, id = self.dialog_manager.main(command, slot, target, type='correction')
                self.dialog_manager.logger.exec_log(id)
                if 'topic' in output.keys():
                    if output['topic'] is not None:
                        topic = output['topic']
                        mid = output['mid']
                        self.dialog_manager.logger.set_topic_cash(topic, mid)

                utterance = self.nlg.generate(command, slot, output)

            elif message.replace("-correction", "", 1) in ["cast_detail", "director_detail"]:
                command = message.replace("-correction", "", 1)
                self.dialog_manager.logger.set_command(command)
                person_name = self.dialog_manager.logger.get_topic_person()
                slot = {"person": person_name, "history": True}
                output, id = self.dialog_manager.main(command, slot, target, type='correction')
                self.dialog_manager.logger.exec_log(id)
                utterance = self.nlg.generate(command, slot, output)

            # 内容詳細系の訂正
            elif "-correction" in message:
                command = message.split('-')[0]
                topic = self.dialog_manager.logger.get_topic_title()
                if command == 'tips':
                    tag = message.split('-')[1]
                    slot = {"title": topic, "tag": tag, "history": True}
                else:
                    slot = {"title": topic, "history": True}

                self.dialog_manager.logger.set_command(command)

                output, id = self.dialog_manager.main(command, slot, target, type='correction')
                self.dialog_manager.logger.exec_log(id)
                if 'topic' in output.keys():
                    if output['topic'] is not None:
                        topic = output['topic']
                        mid = output['mid']
                        self.dialog_manager.logger.set_topic_cash(topic, mid)

                if 'person_list' in output.keys():
                    if output['person_list'] is not None:
                        person_name_list = output['person_list']
                        for person_name in person_name_list:
                            self.dialog_manager.logger.set_person_cash(person_name)

                utterance = self.nlg.generate(command, slot, output)
            else:
                command = message
                self.dialog_manager.logger.set_command(command)
                slot = None

        if utterance is not None:
            self.look(target)
            sys.stdout.write(GREEN)
            sys.stdout.write("\033[K")
            sys.stdout.write("Robot: " + utterance + "\n")
            sys.stdout.write(END)

        # TODO: 音声合成
        # if utterance != '':
        #     order = '{ln_and_speak['+utterance+']}[t='+target+', d=300]'
        #     print('命令文:'+order)
        #     self.set_utterance(utterance)
        #     self.send_message(order)
        #     self.logger.stamp(message, topic, target, utterance)
        # else:
        #     print("Utterance is none::" + message)
        #     self.send_message(order)
        #     self.logger.stamp(message, topic, target, utterance)

        # 発話ログ
        self.dialog_manager.logger.write_asr_log("U", utterance)

        # 能動発話候補をあらかじめ算出しておく
        title = self.dialog_manager.logger.get_topic_title()
        mid = self.dialog_manager.logger.get_topic_mid()
        slot = {'title': title, 'history': None}
        self.active_command = self.dialog_manager.logger.get_not_used_active_command(mid)

        topics = self.dialog_manager.logger.get_topic_history()
        persons = self.dialog_manager.logger.get_person_history()
        return topics, persons

    def terminate(self, detail):
        # self.logger.write(detail)
        # self.conv_manager.flash_topic_memory_list()
        # self.csv.write(self.topic_file_path, self.conv_manager.get_topic_history())
        raise NotImplementedError()

"""
if __name__ == '__main__':
    bc = RobotController()
    bc.look('A')
    bc.utter('actor', 'none')
"""
