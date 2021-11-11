# -*- coding: utf-8 -*-
"""
Robot身体制御
"""
__author__ = "Jin Sakuma"
import os.path
import sys
import time
import datetime
from STT import STT
from TTS import TTS
from NLG import NLG
from DM import DM
import configparser
import threading

current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append (os.path.abspath(os.path.join(current_dir, '../MMDAgentClient', 'run')))
import run_action_player

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
        self.config.read('config/config.ini', encoding='utf-8')
        self.stt = STT(self.config)
        self.tts = TTS(self.config)
        self.nlg = NLG(self.config)
        self.dialog_manager = DM(self.config)
        self.agent_player = run_action_player.AgentPlayer()

        self.utterance_candidate = {'id': None, 'command': None, 'utterance': None, 'topic': None, 'mid': None}
        self.active_command = None

        self.preorder = ""
        self.genre_flg = False  # ジャンル誤り訂正フラグ

        self.curr_target = None # 現在システムが見ているtarget

        # 音声認識を別スレッドで開始する
        # self.stt.start()
        self.look('c')

    def look(self, target):
        if target != self.curr_target:
            self.curr_target = target
            self.agent_player.look(target)

        topics = self.dialog_manager.logger.get_topic_history()
        persons = self.dialog_manager.logger.get_person_history()
        return topics, persons

    def nod(self, target):
        if target != self.curr_target:
            self.curr_target = target
            self.agent_player.look(target)
            time.sleep(0.5)

        self.agent_player.nod()

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

    def change_genre(self, genre_id, target):
        '''
        推薦ジャンルを変更する
        target: topicを変えた人(R:robot, U:user)
        '''
        # genre = genre.decode("utf-8")
        # genre_id = self.dialog_manager.api.genre2id(genre)
        self.dialog_manager.logger.set_genre(int(genre_id))

        topics = self.dialog_manager.logger.get_topic_history()
        persons = self.dialog_manager.logger.get_person_history()
        return topics, persons

    def set_cash(self, output_dict):
        """
        操作画面に表示するキャッシュをセット
        input:
            output: dict DMの結果
        """

        # 映画タイトルのキャッシュ
        if 'topic' in output_dict.keys():
            if output_dict['topic'] is not None:
                topic = output_dict['topic']
                mid = output_dict['mid']
                self.dialog_manager.logger.set_topic_cash(topic, mid)

        # 人名のキャッシュ
        if 'person_list' in output_dict.keys():
            if output_dict['person_list'] is not None:
                person_name_list = output_dict['person_list']
                for person_name in person_name_list:
                    self.dialog_manager.logger.set_person_cash(person_name)

    def main(self, date, time, target, text):
        """
        音声認識されるたびに動く

        input:
            target: str  ... ユーザ(A or B)
            text: str ... 音声認識結果
        output:
          topic_list: list(str) ... トピックの履歴の1次元リスト
        """


        self.look(target)
        sys.stdout.write(GREEN)
        sys.stdout.write("\033[K")
        sys.stdout.write("{}: ".format(target) + text + "\n")
        sys.stdout.write(END)

        # 音声認識のログを取る
        self.dialog_manager.logger.write_asr_log(date, time, target, text)

        # 能動発話候補をあらかじめ算出しておく
        title = self.dialog_manager.logger.get_topic_title()
        mid = self.dialog_manager.logger.get_topic_mid()
        slot = {'title': title, 'history': None}
        self.active_command = self.dialog_manager.logger.get_not_used_active_command(mid)

        # # TODO: NLU
        # command = "recommendation"
        # slot = {"genre": 12, "person": None, "sort_by": None, "history": None}
        #
        # # DM
        # output, id = self.dialog_manager.main(command, slot, target)
        # if 'topic' in output.keys():
        #     topic = output['topic']
        #     mid = output['mid']
        # else:
        #     topic = None
        #     mid = None
        #
        # if 'person_list' in output.keys():
        #     person_name_list = output['person_list']
        # else:
        #     person_name_list = None
        #
        # # NLG
        # utterance = self.nlg.generate(command, slot, output)
        #
        # self.utterance_candidate = {'id': id, 'command': command, 'utterance': utterance,
        #                             'topic': topic, 'mid': mid, 'person_list': person_name_list}
        #
        # self.look(target)
        # sys.stdout.write(YELLOW)
        # sys.stdout.write("\033[K")
        # sys.stdout.write("Robot: " + utterance + "\n")
        # sys.stdout.write("能動発話候補: " + self.active_command + "\n")
        # sys.stdout.write(END)
        #
        topics = self.dialog_manager.logger.get_topic_history()
        persons = self.dialog_manager.logger.get_person_history()
        return topics, persons

    def utter(self, message, target):
        """
        Wizardがボタンを操作した際に動く

        input:
          message: str ... 行動タイプ
          target: str  ... ユーザ(A or B)

        output:
          topic_list: list(str) ... トピックの履歴の1次元リスト
        """

        now = datetime.datetime.now()
        now_str = now.strftime("%Y%m%d %H%M%S.") + "%d" % (now.microsecond / 10000)
        date, start = now_str.split(" ")

        utterance = None
        # 現状のHTMLの引数を取得しておく(誤操作などで更新がない場合はこれを返す)
        topics = self.dialog_manager.logger.get_topic_history()
        persons = self.dialog_manager.logger.get_person_history()

        # 応答
        if "response-passive" in message:
            if self.utterance_candidate['command'] is not None:
                self.dialog_manager.logger.set_command(self.utterance_candidate['command'])
                self.dialog_manager.logger.exec_log(self.utterance_candidate['id'])
                self.set_cash(self.utterance_candidate)
                utterance = self.utterance_candidate['utterance']
            else:
                pass

        else:
            # "recommendation"は能動と訂正両方ある
            if "recommendation" in message:
                if "correction" in message:
                    type = "correction"
                else:
                    type = "active"

                command = "recommendation"
                genre_id = self.dialog_manager.logger.get_current_genre()
                # if genre_id is None:
                #     return topics, persons

                if genre_id:
                    print(genre_id)
                    slot = {"genre": genre_id, "person": None, "sort_by": None, "history": True}
                else:
                    slot = {"genre": None, "person": None, "sort_by": None, "history": True}

            # 能動発話 ("tips", "review", "evaluation", "cast", "director")
            elif "detail-active" in message:
                type = "active"
                command = self.active_command

                title = self.dialog_manager.logger.get_topic_title()
                if title is None:
                    return topics, persons

                if command == "tips":
                    slot = {"title": title, "tag": None, "history": True}
                elif command == "review" or command == "cast":
                    slot = {"title": title, "history": True}
                elif command == "evaluation" or command == "director":
                    slot = {"title": title}

            # 能動発話 ("question")
            elif "question" in message:
                type = "active"
                command = "question"

                title = self.dialog_manager.logger.get_topic_title()
                if title is not None:
                    slot = {"title": title}
                else:
                    return topics, persons

            # 特殊コマンド
            elif message in ["start", "summarize", "end"]:
                type = "active"
                command = message
                slot = {}

            # 特殊応答系の訂正 ("tips", "review")
            elif message.replace("-correction", "", 1) in ["no", "yes", "unknown", "repeat"]:
                type = "correction"
                command = message.replace("-correction", "", 1)
                slot = {}

            elif message.replace("-correction", "", 1) == "title":
                type = "correction"
                command = message.replace("-correction", "", 1)
                self.dialog_manager.logger.set_command(command)
                title = self.dialog_manager.logger.get_topic_title()
                if title is not None:
                    slot = {"title": title}
                else:
                    return topics, persons

            # 人物詳細系の訂正 ("cast_detail", "directpr_detail")
            elif message.replace("-correction", "", 1) in ["cast_detail", "director_detail"]:
                type = "correction"
                command = message.replace("-correction", "", 1)
                self.dialog_manager.logger.set_command(command)
                person_name = self.dialog_manager.logger.get_topic_person()
                if person_name is not None:
                    slot = {"person": person_name, "history": True}
                else:
                    return topics, persons

            # 内容詳細系の訂正 ("tips", "review")
            elif "-correction" in message:
                type = "correction"
                command = message.split('-')[0]
                title = self.dialog_manager.logger.get_topic_title()
                if title is not None:
                    if command == 'tips':
                        tag = message.split('-')[1]
                        slot = {"title": title, "tag": tag, "history": True}
                    else:
                        slot = {"title": title, "history": True}
                else:
                    return topics, persons

            else:
                print(command)
                raise NotImplementedError

            self.dialog_manager.logger.set_command(command)
            output, id = self.dialog_manager.main(command, slot, target, type=type)
            self.dialog_manager.logger.exec_log(id)
            self.set_cash(output)

            if command == "repeat":
                command = output["command"]
                slot = output["slot"]
            utterance = self.nlg.generate(command, slot, output)

        if utterance is not None:
            self.look(target)
            sys.stdout.write(GREEN)
            sys.stdout.write("\033[K")
            sys.stdout.write("Robot: " + utterance + "\n")
            sys.stdout.write(END)

        # 音声合成
        sound_data = self.tts.generate(utterance)
        run_action_player.sound_player.put(sound_data)


        # 発話ログ
        self.dialog_manager.logger.write_asr_log(date, start, "U", utterance)
        if command == "end":
            start_list = run_action_player.sound_player.get_time_list()
            self.dialog_manager.logger.write_system_utterance_log(start_list)

        # 能動発話候補をあらかじめ算出しておく
        title = self.dialog_manager.logger.get_topic_title()
        mid = self.dialog_manager.logger.get_topic_mid()
        slot = {'title': title, 'history': None}
        self.active_command = self.dialog_manager.logger.get_not_used_active_command(mid)

        # HTMLへ渡す引数の更新
        topics = self.dialog_manager.logger.get_topic_history()
        persons = self.dialog_manager.logger.get_person_history()
        return topics, persons
