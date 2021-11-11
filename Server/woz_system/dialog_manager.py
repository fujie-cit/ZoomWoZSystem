from configparser import ConfigParser
from configparser import ConfigParser
import pandas as pd

from .query import Query
from .natural_language_generator_command import NaturalLanguageGeneratorCommand
from .dialog_context_manager import DialogContextManager
from .db_api import DB_API

class DialogManagerError(Exception):
    """対話制御（Query->NaturalLanguageGenerationCommandの変換）で出たエラー"""
    pass

class DialogManager:
    """対話管理部．
    Queryに基づき，出力意味表現を生成

    旧DM．引数がQueryになる以外は大きな変更はなし（のはず）
    """
    
    def __init__(
        self, context_manager: DialogContextManager,
        db_api: DB_API, config: ConfigParser):
        """ """
        self._dialog_context_manager = context_manager
        self._db_api = db_api
        self._config = config

    def _get_recommendation(self, slot, target, type='passive'):
        '''
        slot: dict
            key: genre ジャンル
            key: person 人名
            key: sort_by 並び替え条件(eva_gt/eval_lt/eval_eq/day_gt/day_lt/day_eq)
            key: history 他にフラグ
        '''
        # DBのmainテーブルから映画情報を取得
        if slot['genre'] is not None and slot['person'] is None:
            df = self._db_api.search_movie_by_genre(slot['genre'])

        elif slot['person'] is not None and slot['genre'] is None:
            pid = self._db_api.person2id(slot['person'])
            df = self._db_api.search_movie_by_crew(pid)

        elif slot['genre'] is not None and slot['person'] is not None:
            pid = self._db_api.person2id(slot['person'])
            df_genre = self._db_api.search_movie_by_genre(slot['genre'])
            df_person = self._db_api.search_movie_by_crew(pid)
            df = pd.merge(df_genre, df_person)
        else:
            df = self._db_api.search_movie()

        # 取得した映画群を条件でソート
        if slot['sort_by'] == 'eval_gt' or slot['sort_by'] == 'eval_lt' or slot['sort_by'] == 'eval_eq':
            # 一定の投票数以下の作品は除く
            df = df[df['vote'] > self._config['DM']['vote_min']]
            # 履歴の参照
            used_mid_list = self._dialog_context_manager.get_topic_history()
            prev_mid = used_mid_list[-1]
            prev_score = self._db_api.get_evaluation(prev_mid)

            if slot['sort_by'] == 'eval_gt':
                df = df.sort_values('evaluation', ascending=False)
                df = df[df['evaluation'] > prev_score]
            elif slot['sort_by'] == 'eval_lt':
                df = df.sort_values('evaluation', ascending=True)
                df = df[df['evaluation'] < prev_score]
            else:
                df = df.sort_values('evaluation', ascending=False)
                df = df[(df['evaluation'] > prev_score-1)]
                df = df[(df['evaluation'] < prev_score+1)]

        else:
            # print("#############")
            df = df.dropna(subset=['pronunciation'])
            df = df.sort_values('popularity', ascending=False)

        if slot['history']:
            N = int(self._config['DM']['N'])
            df = df[:N]
            # 履歴の参照
            used_mid_list = self._dialog_context_manager.get_introduced_movie_id_list()
            df = df[~df['movie_id'].isin(used_mid_list)]

        if len(df) > 0:
            # ランダムに選ぶ
            info = df.sample()
            pron = info['pronunciation'].iloc[0]
            if pron is not None:
                topic = pron
            else:
                topic = info['title'].iloc[0]
            mid = info['movie_id'].iloc[0]
        else:
            topic = ''
            mid = None
            pron = None

        gid = slot['genre']
        if gid is None:
            genre = None
        else:
            genre = self._db_api.id2genre(gid)

        # # 対話履歴をセット
        # data_dict = self.logger.get_main_data_dict()
        # data_dict.update(action='utter', target=target, topic=str(mid),
        #                  command='recommendation', type=type)
        # id = self.logger.write(data_dict, slot, [topic])

        output = {'topic': topic, 'mid': mid, 'pron': pron, 'genre': genre}
        return output

    def _get_cast(self, slot, target, type='passive'):
        '''
        slot: dict
            key: title 映画タイトル
            key: history 他にフラグ
        '''
        title = slot['title']
        title_list = self._dialog_context_manager.get_topic_history()
        mid_list = self._dialog_context_manager.get_movie_id_history()
        job_id = self._config['DM']['job_id_cast']
        # すでに話題に上がっている場合
        if title in title_list:
            mid = mid_list[title_list.index(title)]
            cast_list = self._db_api.get_crew(mid, job_id)['name_ja'].tolist()
            if cast_list[0] is None:
                cast_list = self._db_api.get_crew(mid, job_id)['name_en'].tolist()

        # 話題に上がっていない場合
        else:
            df = self._db_api.search_movie_by_title('title')
            if len(df) > 0:
                movie_info = df.iloc[0]
                mid = movie_info['movie_id']
                cast_list = self._db_api.get_crew(mid, job_id)['name_ja'].tolist()
                if cast_list[0] is None:
                    cast_list = self._db_api.get_crew(mid, job_id)['name_en'].tolist()
            else:
                cast_list = []
                mid = -1

        # history=Trueなら履歴を参照する
        N = int(self._config['DM']['cast_num'])
        if slot['history']:
            introduced_cast_list = \
                self._dialog_context_manager.get_introduced_list(
                    'cast', mid, 'person_list')
            cnt = 0
            cast_list_new = []
            for cast in cast_list:
                if cast not in introduced_cast_list:
                    cast_list_new.append(cast)
                    cnt += 1
                if cnt >= N:
                    break

            if len(cast_list) > len(introduced_cast_list)+N:
                state = 1
            else:
                state = 0
        else:
            cast_list_new = cast_list[:N]
            if len(cast_list) > N:
                state = 1
            else:
                state = 0

        # # 対話履歴をセット
        # data_dict = self.logger.get_main_data_dict()
        # data_dict.update(action='utter', target=target, topic=mid,
        #                  command='cast', state=state, type=type)
        # id = self.logger.write(data_dict, slot, cast_list_new)

        output = {'person_list': cast_list_new, 'topic': title, 'mid': mid, 'history': slot['history']}
        return output

    def _get_director(self, slot, target, type='passive'):
        '''
        slot: dict
            key: title 映画タイトル
        '''
        title = slot['title']
        title_list = self._dialog_context_manager.get_topic_history()
        mid_list = self._dialog_context_manager.get_movie_id_history()
        job_id = self._config['DM']['job_id_director']
        # すでに話題に上がっている場合
        if title in title_list:
            mid = mid_list[title_list.index(title)]
            director_list = self._db_api.get_crew(mid, job_id)['name_ja'].tolist()
            if director_list[0] is None:
                director_list = self._db_api.get_crew(mid, job_id)['name_en'].tolist()
        # 話題に上がっていない場合
        else:
            df = self._db_api.search_movie_by_title('title')
            if len(df) > 0:
                movie_info = df.iloc[0]
                mid = movie_info['movie_id']
                director_list = self._db_api.get_crew(mid, job_id)['name_ja'].tolist()
                if director_list[0] is None:
                    director_list = self._db_api.get_crew(mid, job_id)['name_en'].tolist()
            else:
                director_list = []
                mid = -1

        # TODO 履歴の扱い
        # # 対話履歴をセット
        # data_dict = self.logger.get_main_data_dict()
        # data_dict.update(action='utter', target=target, topic=mid,
        #                  command='director', type=type)
        # id = self.logger.write(data_dict, slot, director_list)

        output = {'person_list': director_list, 'topic': title, 'mid': mid}
        return output

    def _get_cast_detail(self, slot, target, type='passive'):
        '''
        slot: dict
            key: person 人物名
            key: history 他にフラグ
        '''
        pid = self._db_api.person2id(slot['person'])

        if pid is not None:
            df = self._db_api.get_credit(pid)
            # import ipdb; ipdb.set_trace()
            topic_list = df['title'].tolist()
            pron_list = df['pron'].tolist()
            N = int(self._config['DM']['cast_detail_num'])
            if slot['history']:
                introduced_cast_detail_list = \
                    self._dialog_context_manager.get_introduced_list(
                        'cast_detail', pid, 'cast_detail')
                cnt = 0
                topic_list_new = []
                for i in range(len(topic_list)):
                    if pron_list[i] is not None:
                        topic = pron_list[i]
                    else:
                        topic = topic_list[i]
                    if topic not in introduced_cast_detail_list:
                        topic_list_new.append(topic)
                        cnt += 1
                    if cnt >= N:
                        break

                if len(topic_list) > len(introduced_cast_detail_list)+N:
                    state = 1
                else:
                    state = 0
            else:
                topic_list_new = topic_list[:N]
                if len(topic_list) > N:
                    state = 1
                else:
                    state = 0

        else:
            topic_list_new = []
            state = 0

        # TODO 履歴の扱い
        # # 対話履歴をセット
        # data_dict = self.logger.get_main_data_dict()
        # data_dict.update(action='utter', target=target, topic=pid,
        #                  command='cast_detail', state=state, type=type)
        # id = self.logger.write(data_dict, slot, topic_list_new)

        topic = self._dialog_context_manager.get_topic_title()
        mid = self._dialog_context_manager.get_topic_movie_id()

        output = {'cast_detail': topic_list_new, 'topic': topic, 'mid': mid}

        return output

    def _get_director_detail(self, slot, target, type='passive'):
        '''
        slot: dict
            key: person 人物名
            key: history 他にフラグ
        '''
        pid = self._db_api.person2id(slot['person'])
        if pid is not None:
            df = self._db_api.get_credit(pid)
            topic_list = df['title'].tolist()

            N = int(self._config['DM']['director_detail_num'])
            if slot['history']:
                introduced_director_detail_list = \
                    self._dialog_context_manager.get_introduced_list(\
                        'director_detail', pid, 'director_detail')
                cnt = 0
                topic_list_new = []
                for topic in topic_list:
                    if topic not in introduced_director_detail_list:
                        topic_list_new.append(topic)
                        cnt += 1
                    if cnt >= N:
                        break

                if len(topic_list) > len(introduced_director_detail_list)+N:
                    state = 1
                else:
                    state = 0
            else:
                topic_list_new = topic_list[:N]
                if len(topic_list) > N:
                    state = 1
                else:
                    state = 0
        else:
            topic_list_new = []
            state = 0

        # TODO 履歴の扱い
        # # 対話履歴をセット
        # data_dict = self.logger.get_main_data_dict()
        # data_dict.update(action='utter', target=target, topic=pid,
        #                  command='director_detail', state=state, type=type)
        # id = self.logger.write(data_dict, slot, topic_list_new)

        topic = self._dialog_context_manager.get_topic_title()
        mid = self._dialog_context_manager.get_topic_movie_id()

        output = {'director_detail': topic_list_new, 'topic': topic, 'mid': mid}
        return output

    def _get_tips(self, slot, target, type='passive'):
        '''
        slot: dict
            key: title 映画タイトル
            key: tag 情報の種類 ex. overview/series
            key: history 他にフラグ
        '''

        title = slot['title']
        title_list = self._dialog_context_manager.get_topic_history()
        mid_list = self._dialog_context_manager.get_movie_id_history()
        # すでに話題に上がっている場合
        if title in title_list:
            mid = mid_list[title_list.index(title)]
            df_tips = self._db_api.get_tips(mid)
            if slot['tag'] is not None:
                tip_list = df_tips[df_tips['tag'] == slot['tag']]['tips'].tolist()
            else:
                tip_list = df_tips['tips'].tolist()

        # 話題に上がっていない場合
        else:
            df = self._db_api.search_movie_by_title('title')
            if len(df) > 0:
                movie_info = df.iloc[0]
                mid = movie_info['movie_id']
                df_tips = self._db_api.get_tips(mid)
                if slot['tag'] is not None:
                    tip_list = df_tips[df_tips['tag'] == slot['tag']]['tips'].tolist()
                else:
                    tip_list = df_tips['tips'].tolist()
            else:
                df_tips = pd.DataFrame({})
                tip_list = []
                mid = -1

        # history=Trueなら履歴を参照する
        if slot['history']:
            introduced_tips_list = \
                self._dialog_context_manager.get_introduced_list(\
                    'tips', mid, 'tips')
            output = None
            for tip in tip_list:
                if tip not in introduced_tips_list:
                    output = tip
                    break

            if len(df_tips) > len(introduced_tips_list)+1:
                state = 1
            else:
                state = 0

        else:
            if len(df_tips) > 1:
                state = 1
                output = tip_list[0]
            elif len(df_tips) == 1:
                state = 0
                output = tip_list[0]
            else:
                state = 0
                output = None

        # TODO 履歴の扱い
        # # 対話履歴をセット
        # data_dict = self.logger.get_main_data_dict()
        # data_dict.update(action='utter', target=target, topic=mid,
        #                  command='tips', state=state, type=type)
        # id = self.logger.write(data_dict, slot, [output])

        output = {'tips': output, 'topic': title, 'mid': mid}
        return output

    def _get_review(self, slot, target, type='passive'):
        '''
        slot: dict
            key: title 映画タイトル
            key: history 他にフラグ
        '''

        title = slot['title']
        title_list = self._dialog_context_manager.get_topic_history()
        mid_list = self._dialog_context_manager.get_movie_id_history()
        # すでに話題に上がっている場合
        if title in title_list:
            mid = mid_list[title_list.index(title)]
            review_list = self._db_api.get_review(mid)['review'].tolist()

        # 話題に上がっていない場合
        else:
            df = self._db_api.search_movie_by_title('title')
            if len(df) > 0:
                movie_info = df.iloc[0]
                mid = movie_info['movie_id']
                review_list = self._db_api.get_tips(mid)['review'].tolist()
            else:
                review_list = []
                mid = -1

        # history=Trueなら履歴を参照する
        if slot['history']:
            introduced_review_list = \
                self._dialog_context_manager.get_introduced_list(\
                    'review', mid, 'review')
            output = None
            for review in review_list:
                if review not in introduced_review_list:
                    output = review
                    break

            if len(review_list) > len(introduced_review_list)+1:
                state = 1
            else:
                state = 0

        else:
            if len(review_list) > 1:
                state = 1
                output = review_list[0]
            elif len(review_list) == 1:
                state = 0
                output = review_list[0]
            else:
                state = 0
                output = None

        # 履歴の扱い
        # # 対話履歴をセット
        # data_dict = self.logger.get_main_data_dict()
        # data_dict.update(action='utter', target=target, topic=mid,
        #                  command='review', state=state, type=type)
        # id = self.logger.write(data_dict, slot, [output])

        output = {'review': output, 'topic': title, 'mid': mid}
        return output

    def _get_evaluation(self, slot, target, type='passive'):
        '''
        slot: dict
            key: title 映画タイトル
        '''

        title = slot['title']
        title_list = self._dialog_context_manager.get_topic_history()
        mid_list = self._dialog_context_manager.get_movie_id_history()
        # すでに話題に上がっている場合
        if title in title_list:
            mid = mid_list[title_list.index(title)]
            df = self._db_api.search_movie_by_id(mid)
            if len(df) > 0:
                assert len(df) == 1, '1 id has multiple movies mid: {}'.format(mid)
                score = df['evaluation'].iloc[0]
            else:
                score = None
                mid = -1
        # 話題に上がっていない場合
        else:
            df = self._db_api.search_movie_by_title('title')
            if len(df) > 0:
                assert len(df) == 1, '1 title has multiple movies mid: {}'.format(title)
                score = df['evaluation']
            else:
                score = None
                mid = -1

        # 履歴の扱い
        # # 対話履歴をセット
        # data_dict = self.logger.get_main_data_dict()
        # data_dict.update(action='utter', target=target, topic=mid,
        #                  command='evaluation', type=type)
        # id = self.logger.write(data_dict, slot, [score])

        output = {'evaluation': score, 'topic': title, 'mid': mid}
        return output

    def _get_genres(self, slot, target, type='passive'):
        '''
        slot: dict
            key: title 映画タイトル
        '''

        title = slot['title']
        title_list = self._dialog_context_manager.get_topic_history()
        mid_list = self._dialog_context_manager.get_movie_id_history()
        # すでに話題に上がっている場合
        if title in title_list:
            mid = mid_list[title_list.index(title)]
            genre_list = self._db_api.get_genre(mid)['genre_id'].tolist()
        # 話題に上がっていない場合
        else:
            df = self._db_api.search_movie_by_title('title')
            if len(df) > 0:
                movie_info = df.iloc[0]
                mid = movie_info['movie_id']
                genre_list = self._db_api.get_genre(mid)['genre_id'].tolist()
            else:
                genre_list = []
                mid = -1

        # TODO 履歴の扱い
        # # 対話履歴をセット
        # data_dict = self.logger.get_main_data_dict()
        # data_dict.update(action='utter', target=target, topic=mid,
        #                  command='genre', type=type)
        # id = self.logger.write(data_dict, slot, genre_list)

        genres = [self._db_api.id2genre(gid) for gid in genre_list]
        output = {'genres': genres, 'topic': title, 'mid': mid}
        return output

    def _get_question(self, slot, target, type='active'):
        '''
        slot: dict
            key: title 映画タイトル
        '''

        title = slot['title']
        title_list = self._dialog_context_manager.get_topic_history()
        mid_list = self._dialog_context_manager.get_movie_id_history()
        # すでに話題に上がっている場合
        if title in title_list:
            mid = mid_list[title_list.index(title)]
        # 話題に上がっていない場合
        else:
            mid = None

        # TODO 履歴の扱い
        # # 対話履歴をセット
        # data_dict = self.logger.get_main_data_dict()
        # data_dict.update(action='utter', target=target, topic=mid,
        #                  command='question', type=type)
        # id = self.logger.write(data_dict, slot, [])
        
        output = {'topic': title, 'mid': mid}
        return output

    def _get_title(self, slot, target, type='correcrion'):
        '''
        slot: dict
            key: title 映画タイトル
        '''

        title = slot['title']
        title_list = self._dialog_context_manager.get_topic_history()
        mid_list = self._dialog_context_manager.get_movie_id_history()
        # すでに話題に上がっている場合
        if title in title_list:
            mid = mid_list[title_list.index(title)]
        # 話題に上がっていない場合
        else:
            mid = None

        # TODO 履歴の扱い
        # # 対話履歴をセット
        # data_dict = self.logger.get_main_data_dict()
        # data_dict.update(action='utter', target=target, topic=mid,
        #                  command='title', type=type)
        # id = self.logger.write(data_dict, slot, [])

        output = {'topic': title, 'mid': mid}
        return output

    """
    def _get_repeat(self, slot, target, type='correction'):
        '''
        slot: dict
            key:
        '''

        # mid_list = self._dialog_context_manager.get_movie_id_history()
        # if len(mid_list)>0:
        #     mid = mid_list[-1]
        # else:
        #     mid = None

        # TODO 履歴の扱い
        # # 対話履歴をセット
        # data_dict = self.logger.get_main_data_dict()
        # data_dict.update(action='utter', target=target, topic=mid,
        #                  command='repeat', type=type)
        # id = self.logger.write(data_dict, slot, [])

        # output = self.cash_output
        # output["command"] = self.cash_command
        # output["slot"] = self.cash_slot
        # return output

        nlg_command = self._dialog_context_manager.get_latest_executed_nlg_command()
        if nlg_command is None:
            raise DialogManagerError("no command executed yet")
        output = dict(
            command=nlg_command.query.command,
            slot=nlg_command.dm_result
        )
        return output
    """

    def _main(self, command, slot, target, type='passive'):
        '''
        DB, 対話履歴を参照してNLGに渡す情報を決定
        条件に応じた発話を生成
        Parameters
        ------------
        command: str
          命令 ex.recommend, person, overview
        slot: dict
          命令の引数 ex. recommend->{"genre": _, "actor": _, "director": _}
        ------------

        commandの種類
        1. recommend        slot: {"genre": _, "person": _"sort_by":_, "history":_}, "それでは、{topic}はどうでしょう？"
        2. cast             slot: {"title": _, "job": _, "history":_}, "{person}が出演しています"
        3. director         slot: {"title": _, "job": _},  "監督は{person}です"
        4. cast_detail      slot: {"person_name", "history":_}, "~や~に出演しています"
        5. director_detail  slot: {"person_name", "history":_}, "~や~を手掛けています"
        6. tips             slot: {"title": _, "history":_}, "XXのシリーズY作目の映画です"
        7. review           slot: {"title": _, "history":_}, "~だったって"
        8. evaluation       slot: {"title": _}, "評価はが{score}点だよ"
        9. genre            slot: {"title": _}, "{genre}だよ"
        10. detail_active   slot: None, 2,3,7~10から選ぶ
        11. pardon          slot: None, "もう一回言ってもらえますか？"
        12. unknown         slot: None, "ちょっとわからないなぁ"
        13.start            slot: None, "どんな映画が観たいですか？"
        14.end              slot: None, "行ってらっしゃい"
        15.yes              slot: None, "はい、そうです"
        16.no               slot: None, "違います"
        17.question         slot: None, "XXは興味ありますか？"
        18.sumarize         slot: NONE, "観に行く映画は決まりましたか？"
        '''

        # commandを履歴に保存
        if 'recommendation' in command:
            output = self._get_recommendation(slot, target, type)

        elif command == 'cast':
            output = self._get_cast(slot, target, type)

        elif command == 'director':
            output = self._get_director(slot, target, type)

        elif command == 'cast_detail':
            output = self._get_cast_detail(slot, target, type)

        elif command == 'director_detail':
            output = self._get_director_detail(slot, target, type)

        elif command == 'tips':
            output = self._get_tips(slot, target, type)

        elif command == 'review':
            output = self._get_review(slot, target, type)

        elif command == 'evaluation':
            output = self._get_evaluation(slot, target, type)

        elif command == 'genre':
            output = self._get_genres(slot, target, type)

        elif command == 'question':
            output = self._get_question(slot, target, type)

        elif command == 'title':
            output = self._get_title(slot, target, type)

        # elif command == 'repeat':
        #     output = self._get_repeat(slot, target, type)

        elif command in ["yes", "no", "unknown", "start", "end", "summarize"]:
            # # 対話履歴をセット
            # data_dict = self.logger.get_main_data_dict()
            # data_dict.update(action='utter', target=target, command=command, type=type)
            # id = self.logger.write(data_dict, slot, [])
            output = {}
            pass
        else:
            id = None
            output = {}

        # self.cash_output = output
        # self.cash_command = command
        # self.cash_slot = slot

        return output

    def generate(self, query: Query) -> NaturalLanguageGeneratorCommand:
        command = query.command
        slot = query.slot
        target = query.target
        type = query.command_type
        
        output = self._main(command, slot, target, type)

        nlg_command = NaturalLanguageGeneratorCommand(
            query=query, dm_result=output
        )

        return nlg_command

def _test_dialog_manager():
    import configparser
    from .woz_command import parse_wizard_command
    from .dialog_context_manager import DialogContextManager
    from .query_generator import QueryGenerator

    config = configparser.ConfigParser()
    config.read('config/config.ini', encoding='utf-8')
    db = DB_API(config)

    context_manager = DialogContextManager()
    query_generator = QueryGenerator(context_manager)
    dialog_manager = DialogManager(context_manager, db, config)

    # genre_id 18はドラマ
    context_manager.append_genre_id(18) 

    message, target = "recommendation-active", "A"
    # message, target = "tips-info-correction", "A"
    # message, target = "start", "A"
    command, command_arg, command_type, target = \
        parse_wizard_command(message, target)
    
    query = query_generator.generate_query(
        command, command_arg, command_type, target)

    nlg_command = dialog_manager.generate(query)

    print(nlg_command)