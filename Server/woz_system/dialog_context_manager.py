from typing import List
from pprint import pprint

from .natural_language_generator_command import NaturalLanguageGeneratorCommand
from .query import Query
from .db_api import DB_API

class DialogContextManager:
    """対話の文脈（コンテクスト）を管理するためのクラス．

    旧LogManagerから抜粋した形．
    """

    def __init__(self, db_api: DB_API):
        
        # DB_API（映画名やジャンル名からIDを取得するため）
        self._db_api = db_api

        # ジャンルIDのリスト
        # 要素は int
        self._genre_cache_list = []
        # 人物(ID?)のリスト
        # 要素は int 
        self._person_cache_list = []
        # 映画タイトルとタイトルIDのリスト
        # 要素は，dict(title: str, mid: int)
        self._topic_cache_list = []

        # 実行した NaturalLanguageGeneratorCommand のリスト
        self._executed_nlg_command_list = []  # type: List[NaturalLanguageGeneratorCommand]


    def get_current_genre_id(self) -> int:
        """現在のジャンルIDを取得する"""
        if len(self._genre_cache_list) == 0:
            return None
        return self._genre_cache_list[-1]

    def get_topic_title(self) -> str:
        """現在の映画タイトルを取得する"""
        if len(self._topic_cache_list) == 0:
            return None
        return self._topic_cache_list[-1]["title"]

    def get_topic_movie_id(self) -> int:
        """現在の映画の映画IDを取得する"""
        if len(self._topic_cache_list) == 0:
            return None
        return self._topic_cache_list[-1]["movie_id"]

    def get_topic_person(self) -> str:
        """現在トピックの人の名前?を取得する"""
        if len(self._person_cache_list) == 0:
            return None
        return self._person_cache_list[-1]

    def get_topic_history(self):
        """これまでのトピック（映画タイトル）の履歴を取得する"""
        return [t['title'] for t in self._topic_cache_list]
    
    def get_movie_id_history(self):
        """これまでのトピック（映画）の映画IDの履歴を取得する"""
        return [t['movie_id'] for t in self._topic_cache_list]

    def get_introduced_movie_id_list(self):
        """照会済の映画IDのリストを取得する"""
        introduced_list = []
        for nlg_command in self._executed_nlg_command_list:
            if nlg_command.query.command != "recommendation":
                continue
            introduced_list.append(nlg_command.dm_result['topic'])
        return introduced_list

    def get_introduced_list(self, command, id, feature_name):
        """commandごとに，紹介した項目のリストを取得する

        Args:
            command (str): コマンド名
            id (int): movie id または person id （コマンドによる）
            feature_name (str): nlg_command.dm_result のキー

        Returns:
            List[str]: 紹介した項目のリスト
        """
        introduced_list = []
        for nlg_command in self._executed_nlg_command_list:
            if nlg_command.query.command != command:
                continue
            if nlg_command.dm_result['topic'] != id:
                continue
            introduced_list.extend(nlg_command.dm_result[feature_name])
        return introduced_list

    def get_latest_executed_nlg_command(self) -> NaturalLanguageGeneratorCommand:
        """最も最近実行したNaturalLanguageGenerationCommandを取得する"""
        if len(self._executed_nlg_command_list) < 1:
            return None
        return self._executed_nlg_command_list[-1]

    def get_executed_command_list_for_movie_id(self, movie_id: int) -> List[NaturalLanguageGeneratorCommand]:
        """与えられた映画IDに対して実行済みのNLGCommandのリストを取得する"""        
        result = []
        for nlg_command in self._executed_nlg_command_list:
            if nlg_command.dm_result.get("mid") == movie_id:
                result.append(nlg_command)
        return result

    def get_latest_movie_title_list(self):
        # 逆向きにする
        movie_list = self._topic_cache_list[::-1]
        # タイトルのリストに変える
        r = [m['title'] for m in movie_list]

        return r

    def get_latest_person_list(self):
        # 逆向きにする
        r = self._person_cache_list[::-1]

        return r

    ### 更新系
    def append_executed_nlg_command(
        self, 
        nlg_command: NaturalLanguageGeneratorCommand):
        """実行したNaturalLanguageGeneratorCommandを登録する"""        
        
        self._executed_nlg_command_list.append(nlg_command)

        qc = Query.CommandName
        # コマンドごとの特殊処理
        if nlg_command.query.command == qc.Recommendation:
            # TODO genreを変えなくていいのだろうか...
            self.append_title(
                nlg_command.dm_result['topic'],
                nlg_command.dm_result['mid']
            )
        elif nlg_command.query.command == qc.Director or \
            nlg_command.query.command == qc.Cast:
            for person_name in nlg_command.dm_result['person_list']:
                self.append_person(person_name)
        else:
            pass
            # raise NotImplementedError

    def append_title(self, title: str, movie_id: int = None):
        if movie_id is None:
            df = self._db_api.search_movie_by_title(title)
            if len(df) > 0:
                movie_id = df['movie_id'].iloc[0]
            else:
                raise RuntimeError("cannot find movie info for title {}".format(title))

        current_movie_id = self.get_topic_movie_id()

        if current_movie_id == movie_id:
            return

        self._topic_cache_list.append(dict(
            title=title, movie_id=movie_id
        ))

    def append_person(self, person_name: str):
        current_person_name = self.get_topic_person()

        if current_person_name == person_name:
            return
        
        # NEW すでにリストにある名前だったら削除する
        while person_name in self._person_cache_list:
            self._person_cache_list.remove(person_name)

        self._person_cache_list.append(person_name)

    def append_genre(self, genre: str):
        genre_id = self._db_api.genre2id(genre)
        
        if genre_id is None:
            raise RuntimeError("cannot find id for genre name {}".format(genre))

        self.append_genre_id(genre_id)

    def append_genre_id(self, genre_id: int):
        self._genre_cache_list.append(genre_id)
