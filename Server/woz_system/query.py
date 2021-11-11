class Query:
    """DialogManagerで検索を行うためのクエリを扱うデータ型
    """

    class CommandName:
        """コマンド名の定数を集めたクラス"""
        # TODO 多分，ここじゃなくて woz_command モジュールにあるべき...

        Look="look"
        Nod="nod"
        Cancel="cancel"

        StartDialog="start_dialog"
        FinishDialog="finish_dialog"
        ChangeTopic="change_topic"
        ChangePerson="change_person"
        ChangeGenre="change_genre"

        Start="start"
        Summarize="summarize"
        End="end"
        Recommendation="recommendation"
        Detail="detail"
        Question="question"
        Response="response"
        Yes="yes"
        No="no"
        Unknown="unknown"
        Repeat="repeat"
        Title="title"
        Genre="genre"
        CastDetail="cast_detail"
        DirectorDetail="director_detail"
        Tips="tips"
        Review="review"
        Evaluation="evaluation"
        Cast="cast"
        Director="director"

    class CommandType:
        """コマンドタイプ（ここで宣言するべきものではないかも...）"""
        Action="action"
        Meta="meta"
        Active="active"
        Passive="passive"
        Correction="correction"

    def __init__(self, command=None, command_type=None, target=None, slot=dict()):
        self._command = command
        self._command_type = command_type
        self._target = target
        self._slot = slot

    @property
    def command(self):
        """コマンド名"""
        return self._command

    @command.setter
    def command(self, value):
        self._command = value

    @property
    def command_type(self):
        """コマンドタイプ(active, passive, correction)"""
        return self._command_type

    @command_type.setter
    def command_type(self, value):
        self._command_type = value

    @property
    def target(self):
        """ターゲット(A, B)"""
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    @property
    def slot(self):
        """検索に用いるスロット"""
        return self._slot

    def __str__(self):
        return '{}({})[{}] -> {}'.format(
            self._command, self._command_type,
            self._slot, self._target,
        )
    
    def __repr__(self):
        return '{}({}, {}, {}, {})'.format(
            str(self.__class__.__name__), repr(self._command),
            repr(self._command_type), repr(self._target),
            repr(self._slot),
        )
