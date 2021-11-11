import datetime

def get_datetime_now_string():
    """ISOフォーマットの現在時刻の文字列を取得する．
    例: 2021-11-05T11:47:39.677281

    Returns:
        str: ISOフォーマットの日時文字列
           
    """
    return datetime.datetime.now().isoformat()
