# -*- coding: utf-8 -*-

"""
MySQLデータベースを用いた発話生成
"""
__editor__ = "Hayato Katayama"
import random


class NLG:
    def __init__(self, config):
        self.config = config

    def generate(self, command, slot, input):
        '''
        条件に応じた発話を生成
        Parameters
        ------------
        command: str
          命令 ex.recommend, person, overview
        slot: dict
          命令の引数 ex. recommend->{"genre": _, "actor": _, "director": _}
        ------------

        commandの種類
        1. recommend        slot: {"genre": _, "person": _"sort_by":_, "history":_}, それでは、{topic}はどうでしょう？"
        2. cast             slot: {"title": _, "job": _, "history":_}, "{person}が出演しています"
        3. director         slot: {"title": _, "job": _},  "監督は{person}です"
        4. cast_detail      slot: {"person_name", "history":_}, "~や~に出演しています"
        5. director_detail  slot: {"person_name", "history":_}, "~や~を手掛けています"
        6. tips             slot: {"title": _, "history":_}, "XXがYYする映画なんだよ"
        7. review           slot: {"title": _, "history":_}, "~だったって"
        8. evaluation       slot: {"title": _}, "評価はが{score}点だよ"
        9. genre            slot: {"title": _}, "{genre}だよ"
        10. title           slot: {"title": _}, "タイトルは{title}だよ"
        11. pardon          slot: None, "もう一回言ってもらえますか？"
        12. unknown         slot: None, "ちょっとわからないなぁ""
        13.start            slot: None, "どんな映画が観たいですか？"
        14.end              slot: None, "行ってらっしゃい"
        15.yes              slot: None, "はい、そうです"
        16.no               slot: None, "違います"
        17.question         slot: {"title": _}, "XXは興味ありますか？"
        18.sumarize         slot: NONE  "観に行く映画は決まりましたか？"
        '''

        if 'recommendation' in command:
            print(input)
            if input['pron'] is not None:
                utterance = "それでは、{}はどうでしょう".format(input['pron'])
            else:
                if input['genre'] is not None:
                    utterance = "すみません、{}の映画はもうこれ以上知りません".format(input['genre'])
                else:
                    utterance = "すみません、映画はこれ以上知りません"


        elif command == 'cast':
            if len(input['person_list']) > 0:
                text = '、'.join(input['person_list'])
                utterance = "{}らが出演しています".format(text)
            elif input['history']:
                utterance = "もう他の出演者は知りません"
            else:
                utterance = "すみません、出演者は知りません"

        elif command == 'director':
            text = 'と'.join(input['person_list'])
            utterance = "監督は{}です".format(text)

        elif command == 'cast_detail':
            if len(input['cast_detail']) > 0:
                if input['topic'] is not None and input['cast_detail'] == [input['topic']]:
                    utterance = "すみません、{}が出演している映画は{}以外知りません".format(slot['person'], input['topic'])
                elif input['topic'] is not None:
                    title_list = input['cast_detail']
                    if input['topic'] in title_list:
                        title_list.remove(input['topic'])
                    text = 'や'.join(title_list)
                    utterance = "{}に出演しています".format(text)
                else:
                    utterance = "すみません、{}が出演している映画は知りません".format(slot['person'])
            else:
                utterance = "すみません、{}のことは知りません".format(slot['person'])

        elif command == 'director_detail':
            if len(input['director_detail']) > 0:
                if input['topic'] is not None and input['director_detail'] == [input['topic']]:
                    utterance = "すみません、{}が手がけた映画は{}以外知りません".format(slot['person'], input['topic'])
                elif input['topic'] is not None:
                    title_list = input['director_detail']
                    if input['topic'] in title_list:
                        title_list.remove(input['topic'])
                    text = 'や'.join(title_list)
                    utterance = "{}を手がけています".format(text)
                else:
                    utterance = "すみません、{}が手がけた映画は知りません".format(slot['person'])
            else:
                utterance = "すみません、{}のことは知りません".format(slot['person'])

        elif command == 'tips':
            if input['tips'] is not None:
                utterance = "{}".format(input['tips'])
            else:
                utterance = "すみません、{}に関する情報は持っていません".format(input['topic'])

        elif command == 'review':
            if input['review'] is not None:
                utterance = "{}".format(input['review'])
            else:
                utterance = "すみません、{}のレビューは知りません".format(input['topic'])

        elif command == 'evaluation':
            score = input['evaluation']
            if score is None:
                utterance = "すみません、{}は知りません".format(slot['title'])
            else:
                utterance = "評価は10点満点中{}点です".format(score)

        elif command == 'genre':
            genres = input['genres']
            if len(genres) > 0:
                text = '、'.join(genres)
                utterance = "ジャンルは{}です".format(text)
            else:
                utterance = "すみません、{}は知りません".format(slot['title'])

        elif command == 'title':
            utterance = "タイトルは{}です".format(input['topic'])

        elif command == 'pardon':
            utterance = "すみません、もう一回言ってもらえますか"

        elif command == 'unknown':
            utterance = "すみません、わかりません"

        elif command == 'start':
            utterance = "どんな映画が見たいですか？"

        elif command == 'end':
            utterance = "いってらっしゃい"

        elif command == 'yes':
            utterance = "はい、そうです"

        elif command == 'no':
            utterance = "いいえ、違います"

        elif command == 'question':
            if random.randint(0, 10) % 2 == 0:
                 utterance = "{}は興味ありますか".format(slot['title'])
            else:
                utterance = "{}は見たいと思いますか".format(slot['title'])

        elif command == 'summarize':
            utterance = "見に行く映画は決まりましたか"

        else:
            print(command)
            raise NotImplementedError()

        return utterance
