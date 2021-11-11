from .query import Query

class NaturalLanguageGeneratorCommand:
    """Natural Language Generator に与えるコマンド．
    DialogManager の検索に用いた Query (query) と，
    検索結果が入ったディクショナリ(dm_result)で構成される．
    """
    def __init__(self, query: Query = None, dm_result: dict = {}):
        """コンストラクタ

        Args:
            query (Query, optional): 生成に用いられたクエリ. Defaults to None.
            dm_result (dict, optional): 対話制御（検索）結果スロット群. Defaults to {}.
        """
        self._query = query
        self._dm_result = dm_result

    @property
    def query(self):
        """生成に用いられたクエリ"""
        return self._query

    @query.setter
    def query(self, value):
        self._query = value

    @property
    def dm_result(self):
        """対話制御（検索）結果スロット群"""
        return self._dm_result

    def __str__(self):
        return "Query:{}, DMResult:{}".format(self._query, self._dm_result)
