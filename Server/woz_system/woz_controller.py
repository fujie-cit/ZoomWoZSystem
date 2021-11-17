import traceback
from configparser import ConfigParser
import threading
from typing import Tuple, List
import datetime


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

from .logging import Logger, JSONLogger
from .logging.util import get_datetime_now_string
from .sound import get_bell_sound_data

from .speech_recognition.user_manager_client import SpeechRecognitionResult, SpeechRecognitionState, UserManagerClient

class WoZControllerError(Exception):
    pass


def generate_dialog_id() -> str:
    """対話IDを生成する（ログファイルのディレクトリ名に相当する）．
    日時をYYYYmmddHHMM形式で返す．

    Returns:
        str: 対話ID
    """
    import datetime
    now = datetime.datetime.now()
    dialog_id = now.strftime("%Y%m%d%H%M")
    return dialog_id
    

def get_log_file_path(topdir: str, dialog_id: str, filename: str) -> str:
    """ログファイルのパスを取得する.

    Args:
        topdir (str): ログのトップディレクトリ（設定ファイルから取得できる）
        dialog_id (str): 対話ID（対話セッションによって異なる）
        filename (str): ファイル名（用途によって異なる）

    Returns:
        str: ログファイルのパス
    """
    import os
    dir = os.path.join(topdir, dialog_id)
    os.makedirs(dir, exist_ok=True)
    return os.path.join(dir, filename)
    

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


        self._update_utterance_candidates_thread = None
        self._update_utterance_candidates_cond = threading.Condition()

        # 対話ID
        self._dialog_id = generate_dialog_id()

        # 各種ロガー
        log_top_dir = self._config['Log']['dir']
        self._control_logger = Logger(get_log_file_path(log_top_dir, self._dialog_id, "control.csv"))
        self._control_logger_cond = threading.Condition()
        self._asr_logger = Logger(get_log_file_path(log_top_dir, self._dialog_id, "asr.csv"))
        self._asr_logger_cond = threading.Condition()
        self._json_logger = JSONLogger(get_log_file_path(log_top_dir, self._dialog_id, "system.json"))

        # 音声認識関係
        self._user_a = None
        self._user_a_result_cache = None # 音声認識開始に対応する結果のキャッシュ
        self._user_b = None
        self._user_b_result_cache = None # 音声認識開始に対応する結果のキャッシュ
        self._user_manager_client = UserManagerClient(self._config["UserManager"]["url"])
        self._user_manager_client.append_receiver(self._handle_speech_recognition_result)

    def __del__(self):
        print("WoZController destructor called")

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
        """発話候補リストの更新を行う"""

        # 前回の実行の終了を待機する
        with self._update_utterance_candidates_cond:
            if self._update_utterance_candidates_thread is not None:
                self._update_utterance_candidates_thread.join()

            self._update_utterance_candidates_thread = threading.Thread(
                target=self.__update_utterance_candidates
            )
            self._update_utterance_candidates_thread.start()

    def __update_utterance_candidates(self):
        """発話候補リストの更新を行う（実際に行う）"""
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
        success = False
        try:
            if command == qcn.StartDialog or command == qcn.FinishDialog:
                # ベルを鳴らす
                bell_data = get_bell_sound_data()
                self._sound_player.play(bell_data)
            elif command == qcn.ChangeTopic:
                self._context_manager.append_movie_by_id(int(target))
            elif command == qcn.ChangePerson:
                self._context_manager.append_person(target)
            elif command == qcn.ChangeGenre:
                self._context_manager.append_genre_id(int(target))
            else:
                raise WoZControllerError(
                    "unknown command {} of command type {}".format(
                    command, command_type))
            success = True
        finally:
            # ログ保存
            with self._control_logger_cond:
                control_id = self._control_logger.get_new_id()
                self._control_logger.put([control_id, dt, command, None, command_type, target, None, success])


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
        success = False
        try:
            if command == qcn.Look:
                self._agent_player.look(target)
            elif command == qcn.Nod:
                self._agent_player.nod()
            else:
                raise WoZControllerError(
                    "unknown command {} of command type {}".format(
                        command, command_type))
            success = True
        except AgentPlayerWrapperError:
            print(traceback.format_exc())
        finally:
            # ログ保存
            with self._control_logger_cond:
                control_id = self._control_logger.get_new_id()
                self._control_logger.put([control_id, dt, command, None, command_type, target, None, success])

    def _execute_utterance_command(self, message, target):
        """システム発話の行動を実行する

        Args:
            message (str): インターフェースから与えられるコマンド文字列
            target (str): ターゲット

        Raises:
            WoZControllerError: 対応するシステム発話データを生成できなかった場合
        """
        dt = get_datetime_now_string()

        # パース（無駄だがログのため）
        command, command_arg, command_type, target = \
            parse_wizard_command(message, target)

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

            # 成功時の操作ログへの書き出し
            with self._control_logger_cond:
                control_id = self._control_logger.get_new_id()            
                self._control_logger.put([
                    control_id, 
                    dt,
                    ut.nlg_command.query.command,
                    ut.nlg_command.query.command_arg,
                    ut.nlg_command.query.command_type,
                    ut.nlg_command.query.target,
                    ut.text, True])
            # 音声認識結果ログに書き出し
            with self._asr_logger_cond:
                time_start = datetime.datetime.now()
                # 終了時間（予測） 
                # TODO 音声波形の時間計算はここでやりたくない
                num_samples = len(ut.speech_data) / 2
                duration_in_second = num_samples / 32000
                time_end = time_start + datetime.timedelta(seconds=duration_in_second)
                
                asr_id = self._asr_logger.get_new_id()
                user_label = "S"
                str_start = time_start.isoformat()
                str_end = time_end.isoformat()
                content = ut.text

                self._asr_logger.put([
                    asr_id, user_label, str_start, str_end, "0.0", content
                ])
            # システムログに書き出し
            json_info = dict(
                datetime=dt,
                control_id=control_id,
                asr_id=asr_id,
                utterance_candidate=ut.get_json_log_info()
            )
            self._json_logger.put(json_info)
            # 次回の発話を生成する
            self.update_utterance_candidates()
        else:
            # 失敗時の操作ログへの書き出し
            with self._control_logger_cond:
                control_id = self._control_logger.get_new_id()
                self._control_logger.put([control_id, dt, command, command_arg, command_type, target, None, False])

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

    def get_latest_information(self) -> Tuple[List[dict], List[str]]:
        """最新の映画（トピック）と人物のリスト

        Returns:
            List[dict]: 映画のタイトルとIDの辞書のリスト
            List[str]: 人物名のリスト
        """
        movie_list = self._context_manager.get_latest_movie_list()
        person_list = self._context_manager.get_latest_person_list()
        return movie_list, person_list

    # 対話ID関係
    def get_dialog_id(self):
        return self._dialog_id

    # 音声認識関係
    def get_user_list(self) -> List[str]:
        """接続中のユーザ名のリストを取得する"""
        return self._user_manager_client.get_user_name_list()
    
    def get_user_a(self) -> str:
        """参加者Aのユーザ名を取得する．設定して無ければNone"""
        return self._user_a

    def get_user_b(self) -> str:
        """参加者Bのユーザ名を取得する．設定して無ければNone"""
        return self._user_b

    def set_user_a(self, user_name: str):
        """参加者Aのユーザ名を設定する. 当該ユーザの音声認識結果の監視を開始する"""
        if user_name is self._user_a:
            return
        if self._user_a is not None and self._user_a != self._user_b:
            self._user_manager_client.request_stop_send_speech_recognition_result(self._user_a)
        self._user_a = user_name
        self._user_manager_client.request_start_send_speech_recognition_result(self._user_a)
        return

    def set_user_b(self, user_name: str):
        """参加者Bのユーザ名を設定する．当該ユーザの音声認識結果の監視を開始する"""
        if user_name is self._user_b:
            return
        if self._user_b is not None and self._user_b != self._user_a:
            self._user_manager_client.request_stop_send_speech_recognition_result(self._user_b)
        self._user_b = user_name
        self._user_manager_client.request_start_send_speech_recognition_result(self._user_b)
        return

    def _handle_speech_recognition_result(self, result: SpeechRecognitionResult):
        user_name = result.user_name
        if user_name not in [self._user_a, self._user_b]:
            return
        
        if result.state == SpeechRecognitionState.Start:
            if user_name == self._user_a:
                self._user_a_result_cache = result
            else:
                self._user_b_result_cache = result
            return
        
        if result.state == SpeechRecognitionState.End:
            content = result.result
            if len(content) == 0:
                return
            if user_name == self._user_a:
                cache = self._user_a_result_cache
                user_label = "A"
            else:
                cache = self._user_b_result_cache
                user_label = "B"
            if cache is not None:
                start_dtime = cache.dtime
            else:
                start_dtime = None

            # オフセット取得
            offset = self._user_manager_client.get_diff_time(user_name)
            if offset is not None:
                offset_seconds = offset[0].total_seconds()
            else:
                offset_seconds = 0

            with self._asr_logger_cond:
                str_id = self._asr_logger.get_new_id()
                str_start = start_dtime.isoformat() if start_dtime is not None else ""
                str_end = result.dtime.isoformat()
                str_offset = "{}".format(offset_seconds)
            
                self._asr_logger.put([
                    str_id, user_label, str_start, str_end, str_offset, content
                ])
            
            # TODO この後，言語処理 -> 発話候補更新の流れ



