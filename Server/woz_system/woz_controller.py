import traceback
from configparser import ConfigParser
import threading
from typing import Tuple, List

from .db_api import DB_API
from .dialog_context_manager import DialogContextManager
from .query_generator import QueryGenerator
from .dialog_manager import DialogManager
from .natural_language_generator import NaturalLanguageGenerator
from .text_to_speech import TextToSpeech
from .utterance_generator import UtteranceCandidateGenerator, UtteranceCandidate

from .agent_player_wrapper import \
    AgentPlayerWrapper as AgentPlayer, \
    AgentPlayerWrapperError, SoundPlayer

from .query import Query
from .woz_command import parse_wizard_command

from .logging import Logger
from .logging.util import get_datetime_now_string
from .sound import get_bell_sound_data

class WoZControllerError(Exception):
    pass


def get_log_file_path(config: ConfigParser) -> str:
    import datetime, os
    now = datetime.datetime.now()
    name = now.strftime("%Y%m%d%H%M")
    dir = os.path.join(config['Log']['dir'], name)
    os.makedirs(dir, exist_ok=True)
    return os.path.join(dir, 'system.csv')
    

class WoZController:
    def __init__(self, config_file_path="config/config.ini"):
        self._config = ConfigParser()
        self._config.read(config_file_path, encoding='utf-8')

        self._db_api = DB_API(self._config)
        self._context_manager = DialogContextManager(self._db_api)
        self._query_generator = QueryGenerator(self._context_manager)
        self._dialog_manager = DialogManager(
            self._context_manager, self._db_api, self._config)
        self._natural_language_generator = NaturalLanguageGenerator()
        self._text_to_speech = TextToSpeech(self._config)
        self._utterance_candidate_generator = UtteranceCandidateGenerator(
            self._context_manager,
            self._query_generator,
            self._dialog_manager,
            self._natural_language_generator,
            self._text_to_speech
        )
        self._agent_player = AgentPlayer()
        self._sound_player = SoundPlayer()

        self._utterance_candidates = dict()
        self._utterance_candidates_errors = dict()

        self._logger = Logger(get_log_file_path(self._config))

        self._update_utterance_candidates_thread = None
        self._update_utterance_candidates_cond = threading.Condition()

    # インターフェース上のコマンドリスト
    _interface_command_list = [
        # # システム動作系(command_type: action)
        # "look-action", "nod-action", "cancel-action",
        # # メタコマンド系（command_type: meta)
        # "change_topic-meta", "change_person-meta",
        # "change_genre-meta",
        # 発話系(command_type: active, passive, correction)
        "start-active", "summarize-active", "end-active",
        "recommendation-active", "detail-active",
        "question", "response-passive", "yes-correction",
        "no-correction", "unknown-correction", "repeat-correction",
        "title-correction", "genre-correction",
        "recommendation-correction", "cast_detail-correction",
        "director_detail-correction", "tips-story-correction",
        "tips-info-correction", "review-correction",
        "evaluation-correction", "cast-correction",
        "director-correction",
    ]

    # インターフェース上のターゲットのリスト
    _interface_target_list = [
        "A", "B"
    ]

    def update_utterance_candidates(self):
        # 前回の実行の終了を待機する
        with self._update_utterance_candidates_cond:
            if self._update_utterance_candidates_thread is not None:
                self._update_utterance_candidates_thread.join()

            self._update_utterance_candidates_thread = threading.Thread(
                target=self.__update_utterance_candidates
            )
            self._update_utterance_candidates_thread.start()

    def __update_utterance_candidates(self):
        """ボタンを押された際の発話候補を更新する"""
        self._utterance_candidates.clear()
        self._utterance_candidates_errors.clear()
        for target in WoZController._interface_target_list:
            for message in WoZController._interface_command_list:
                utterance_candidate = None
                try:
                    utterance_candidate = \
                        self._utterance_candidate_generator.generate(
                            message, target
                        )
                    self._utterance_candidates[(message, target)] = \
                        utterance_candidate
                except Exception:
                    # print(traceback.format_exc())
                    self._utterance_candidates_errors[(message, target)] = \
                        traceback.format_exc()
                    pass

    def _execute_meta_command(self, command, command_arg, command_type, target):
        """メタコマンドの実行

        Args:
            command (str): コマンド名
            command_arg (str): コマンド引数
            command_type (str): コマンド型
            target (str): ターゲット

        Raises:
            WoZControllerError: コマンド不明
        """
        qcn = Query.CommandName

        # ログ保存用の日時文字列
        dt = get_datetime_now_string()

        if command == qcn.StartDialog or command == qcn.FinishDialog:
            # ベルを鳴らす
            bell_data = get_bell_sound_data()
            self._sound_player.play(bell_data)
        elif command == qcn.ChangeTopic:
            self._context_manager.append_title(target)
        elif command == qcn.ChangePerson:
            self._context_manager.append_person(target)
        elif command == qcn.ChangeGenre:
            self._context_manager.append_genre_id(int(target))
        else:
            raise WoZControllerError(
                "unknown command {} of command type {}".format(
                    command, command_type))

        # 実行成功時にログ保存
        self._logger.put([dt, command, command_type, target, None])


    def _execute_action_command(self, command, command_arg, command_type, target):
        """アクションコマンドの実行

        Args:
            command (str): コマンド名
            command_arg (str): コマンド引数
            command_type (str): コマンド型
            target (str): ターゲット

        Raises:
            WoZControllerError: コマンド不明
        """
        qcn = Query.CommandName

        # ログ用の日時文字列を予め取得
        dt = get_datetime_now_string()

        # 実行
        try:
            if command == qcn.Look:
                self._agent_player.look(target)
            elif command == qcn.Nod:
                self._agent_player.nod()
            else:
                raise WoZControllerError(
                    "unknown command {} of command type {}".format(
                        command, command_type))

            # 実行成功時にログ保存
            self._logger.put([dt, command, command_type, target, None])

        except AgentPlayerWrapperError:
            print(traceback.format_exc())

    def _execute_utterance_command(self, message, target):
        """システム発話の行動を実行する

        Args:
            message (str): インターフェースから与えられるコマンド文字列
            target (str): ターゲット

        Raises:
            WoZControllerError: 対応するシステム発話データを生成できなかった場合
        """
        dt = get_datetime_now_string()
        
        # 候補更新中だったら待機する
        if self._update_utterance_candidates_thread is not None:
            self._update_utterance_candidates_thread.join()
        
        ut = None
        if (message, target) in self._utterance_candidates:
            ut = self._utterance_candidates[(message, target)]
        else:
            ut = self._utterance_candidate_generator.generate(
                message, target
            )

        if ut is not None:
            self._sound_player.play(ut.speech_data)
            self._context_manager.append_executed_nlg_command(ut.nlg_command)
            self._logger.put([
                dt,
                ut.nlg_command.query.command,
                ut.nlg_command.query.command_type,
                ut.nlg_command.query.target,
                ut.text])
            # 次回の発話を生成する
            self.update_utterance_candidates()
        else:
            raise WoZControllerError(
                "could not generate utterance for {}/{}".format(message, target))

    def execute(self, message, target):
        """Wizardの操作を実行する．

        Args:
            message (str): インターフェースから与えられるコマンド文字列
            target (str): ターゲット
        """

        # コマンドタイプで処理を分けるため，まずパースする．
        command, command_arg, command_type, target = \
            parse_wizard_command(message, target)

        # コマンドタイプ別に実行する
        qct = Query.CommandType
        if command_type == qct.Meta:
            self._execute_meta_command(
                command, command_arg, command_type, target)
        elif command_type == qct.Action:
            self._execute_action_command(
                command, command_arg, command_type, target)
        else:
            self._execute_utterance_command(message, target)

    def get_latest_information(self) -> Tuple[List[str], List[str]]:
        title_list = self._context_manager.get_latest_movie_title_list()
        person_list = self._context_manager.get_latest_person_list()
        return title_list, person_list
