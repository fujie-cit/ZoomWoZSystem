import random

from .query import Query
from .dialog_context_manager import DialogContextManager

class QueryGeneratorError(Exception):
    """クエリ生成に関する例外"""
    pass

class QueryGenerator:
    """Wizardの操作に基づきクエリを生成する
    """    
    def __init__(self, context_manager: DialogContextManager):
        self._context_manager = context_manager

    def generate_query(self, command, command_arg, command_type, target):
        qc = Query.CommandName

        if command == "detail" and command_type == "active":
            command = self._get_active_command()

        if command == qc.Recommendation:
            query = self._generate_query_for_recommendation(command_type)
        elif command == qc.Question:
            # command_type は None で呼ばれるはず．
            # command_type に active を入れるのは互換性による．
            query = self._generate_query_for_question(command_type="active")
        elif command == qc.Start:
            query = self._generate_query_for_start(command_type="active")
        elif command == qc.Summarize:
            query = self._generate_query_for_summarize(command_type="active")
        elif command == qc.End:
            query = self._generate_query_for_end(command_type="active")
        elif command == qc.Yes:
            query = self._generate_query_for_yes(command_type)
        elif command == qc.No:
            query = self._generate_query_for_no(command_type)
        elif command == qc.Unknown:
            query = self._generate_query_for_unknown(command_type)
        # elif command == qc.Repeat:
        #     query = self._generate_query_for_repeat(command_type)
        elif command == qc.Title:
            query = self._generate_query_for_title(command_type)
        elif command == qc.Genre:
            query = self._generate_query_for_genre(command_type)
        elif command == qc.CastDetail:
            query = self._generate_query_for_cast_detail(command_type)
        elif command == qc.DirectorDetail:
            query = self._generate_query_for_director_detail(command_type)
        elif command == qc.Tips:
            query = self._generate_query_for_tips(command_arg, command_type)
        elif command == qc.Review:
            query = self._generate_query_for_review(command_type)
        elif command == qc.Evaluation:
            query = self._generate_query_for_evaluation(command_type)
        elif command == qc.Cast:
            query = self._generate_query_for_cast(command_type)
        elif command == qc.Director:
            query = self._generate_query_for_director(command_type)
        else:
            raise QueryGeneratorError(
                "cannot generate query for {}, {}, {}, {}".format(
                    command, command_arg, command_type, target
                ))
        
        if query is not None:
            query.target = target

        return query

    def _get_active_command(self) -> str:
        """能動的な発話のうち，未発話のコマンドをランダムに生成する

        Returns:
            str: コマンド名
        """
        
        # 現在のトピック映画IDを取得
        movie_id = self._context_manager.get_topic_movie_id()
        # トピック映画に関して，実行済のNLGコマンドを取得
        nlg_command_list = self._context_manager.get_executed_command_list_for_movie_id(movie_id)

        # TODO cast_detailやdirector_dietalの生成．紹介していない人が
        # いれば，その人の詳細を紹介する(?)
    
        # 実行していないコマンド名を作成
        qc = Query.CommandName        
        command_candidates = [
            qc.Recommendation, qc.Review, qc.Evaluation, qc.Cast, qc.Director
        ]
        for nlg_command in nlg_command_list:
            if nlg_command.query.command in command_candidates:
                command_candidates.remove(nlg_command.query.command)

        # ランダムに選択        
        command = random.choice(command_candidates)

        return command

    def _generate_query_for_active(self, command):
        query = Query(command_type="active")
        
        title = self._context_manager.get_topic_title()
        if title is None:
            raise QueryGeneratorError("could not retrieve topic title")

        raise NotImplementedError


    def _generate_query_for_recommendation(self, command_type):
        query = Query(
            command="recommendation",
            command_type=command_type,
        )

        genre_id = self._context_manager.get_current_genre_id()
        
        # genre_id が False(0, Noneの場合もあり)は None にする
        if not genre_id: genre_id = None 

        query.slot.update(dict(
            genre=genre_id, person=None,
            sort_by=None, history=None,
        ))

        return query
    
    def _generate_query_for_question(self, command_type):
        query = Query(
            command="question",
            command_type=command_type
        )

        title = self._context_manager.get_topic_title()
        if title is None:
            raise QueryGeneratorError("could not retrieve topic title")
        
        query.slot.update(dict(
            title=title,
        ))

        return query

    def _generate_query_for_start(self, command_type):
        query = Query(
            command="start",
            command_type=command_type
        )

        return query
    
    def _generate_query_for_summarize(self, command_type):
        query = Query(
            command="summarize",
            command_type=command_type
        )

        return query
    
    def _generate_query_for_end(self, command_type):
        query = Query(
            command="end",
            command_type=command_type
        )

        return query
    
    def _generate_query_for_yes(self, command_type):
        query = Query(
            command="yes",
            command_type=command_type
        )

        return query
        
    def _generate_query_for_no(self, command_type):
        query = Query(
            command="no",
            command_type=command_type
        )

        return query

    def _generate_query_for_unknown(self, command_type):
        query = Query(
            command="unknown",
            command_type=command_type
        )

        return query

    def _generate_query_for_repeat(self, command_type):
        query = Query(
            command="repeat",
            command_type=command_type
        )

        return query

    def _generate_query_for_title(self, command_type):
        query = Query(
            command="title",
            command_type=command_type
        )

        title = self._context_manager.get_topic_title()

        if title is None:
            raise QueryGeneratorError("could not retrieve topic title")
        
        query.slot.update(dict(
            title=title
        ))

        return query

    def _generate_query_for_genre(self, command_type):
        query = Query(
            command="genre",
            command_type=command_type
        )

        title = self._context_manager.get_topic_title()

        if title is None:
            raise QueryGeneratorError("could not retrieve topic title")
        
        query.slot.update(dict(
            title=title
        ))

        return query
    
    def _generate_query_for_cast_detail(self, command_type):
        query = Query(
            command="cast_detail",
            command_type=command_type
        )

        person_name = self._context_manager.get_topic_person()

        if person_name is None:
            raise QueryGeneratorError("could not retrieve topic person")
        
        query.slot.update(dict(
            person=person_name,
            history=True
        ))

        return query

    def _generate_query_for_director_detail(self, command_type):
        query = Query(
            command="director_detail",
            command_type=command_type
        )

        person_name = self._context_manager.get_topic_person()

        if person_name is None:
            raise QueryGeneratorError("could not retrieve topic person")
        
        query.slot.update(dict(
            person=person_name,
            history=True
        ))

        return query

    def _generate_query_for_tips(self, command_arg, command_type):
        query = Query(
            command="tips",
            command_type=command_type
        )

        title = self._context_manager.get_topic_title()
        
        if title is None:
            raise QueryGeneratorError("could not retrieve topic title")

        query.slot.update(dict(
            title=title,
            tag=command_arg,
            history=True
        ))

        return query
    
    def _generate_query_for_review(self, command_type):
        query = Query(
            command="review",
            command_type=command_type
        )

        title = self._context_manager.get_topic_title()

        if title is None:
            raise QueryGeneratorError("could not retrieve topic title")
        
        query.slot.update(dict(
            title=title,
            history=True
        ))

        return query
    
    def _generate_query_for_evaluation(self, command_type):
        query = Query(
            command="evaluation",
            command_type=command_type
        )

        title = self._context_manager.get_topic_title()

        if title is None:
            raise QueryGeneratorError("could not retrieve topic title")
        
        query.slot.update(dict(
            title=title,
            history=True
        ))

        return query
    
    def _generate_query_for_cast(self, command_type):
        query = Query(
            command="cast",
            command_type=command_type
        )

        title = self._context_manager.get_topic_title()

        if title is None:
            raise QueryGeneratorError("could not retrieve topic title")
        
        query.slot.update(dict(
            title=title,
            history=True
        ))

        return query

    def _generate_query_for_director(self, command_type):
        query = Query(
            command="director",
            command_type=command_type
        )

        title = self._context_manager.get_topic_title()

        if title is None:
            raise QueryGeneratorError("could not retrieve topic title")
        
        query.slot.update(dict(
            title=title,
            history=True
        ))

        return query


def _test_query_generator():
    from .woz_command import parse_wizard_command
    from .dialog_context_manager import DialogContextManager
    context_manager = DialogContextManager()
    query_generator = QueryGenerator(context_manager)

    # genre_id 18はドラマ
    context_manager.append_genre_id(18) 

    message, target = "recommendation-active", "A"
    # message, target = "tips-info-correction", "A"
    # message, target = "start", "A"
    command, command_arg, command_type, target = \
        parse_wizard_command(message, target)
    
    query = query_generator.generate_query(
        command, command_arg, command_type, target)
    
    print(query)