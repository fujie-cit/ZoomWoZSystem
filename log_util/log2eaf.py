from os import path
import pandas as pd
import datetime

from elan.data import EafInfo
from elan.io import write_to_eaf


def log2eaf(logdir: str,
            output_file: str,
            offset: float = 0.0,
            asr_start_offset: float = -1.0,
            asr_end_offset: float = -1.0,
            media_file_path: str = None):
    """ログファイルをEAFファイルに変換する

    Args:
        logdir (str): ログファイル（asr.csv, control.csv）が置かれたディレクトリのパス[description]
        output_file (str): 出力するEAFファイルのパス.
        offset (float, optional): 
           control.csvに記録された会話開始の合図が，動画上で何秒の位置にあるか.
           Defaults to 0.0.
        asr_start_offset (float, optional): 
            WebSpeechAPIの音声認識の発話開始（onspeechstartイベント）の実際の音声開始に
            対する推定オフセット.
            Defaults to -1.0.
        asr_end_offset (float, optional): 
            WebSpeechAPIの音声認識の発話開始（onspeechendイベント）の実際の音声開始に
            対する推定オフセット.
            Defaults to -1.0.
        media_file_path (str, optional): 
            動画ファイルのパス.
            Defaults to None.
    """
    eaf_info = EafInfo()

    if media_file_path:
        eaf_info.append_media(url="file://" + media_file_path,
                              mime_type="video/mp4",
                              relative_media_url="")
    asr_log_path = path.join(logdir, "asr.csv")
    control_log_path = path.join(logdir, "control.csv")
    df_asr = pd.read_csv(asr_log_path, header=None, encoding='sjis')
    df_control = pd.read_csv(control_log_path, header=None, encoding='sjis')

    # 対話開始の操作を取得する
    subdf_start = df_control[df_control.iloc[:, 2] == 'start_dialog']
    assert len(subdf_start) == 1, "dialog start button pushed several times"
    start_time = datetime.datetime.fromisoformat(subdf_start.iloc[0, 1])

    # 制御ログ
    for i, row in df_control.iterrows():
        v_id, v_time, command, command_arg, command_type, target, utterance, \
            completed = row

        # ビデオ内での時間を取得する
        v_time = datetime.datetime.fromisoformat(v_time)
        t_diff = v_time - start_time
        t_in_video = t_diff.total_seconds() + offset

        # 書き出すコマンドかどうか判断
        # action は 煩雑なのでやめておく
        if command_type == "action":
            continue
        # 成功していないコマンドもやめておく
        if not completed:
            continue

        text = command
        if not pd.isna(command_arg):
            text += "-" + command_arg
        text += "-" + command_type
        text += "/" + target

        eaf_info.append_annotation("control", int(t_in_video * 1000),
                                   int(t_in_video * 1000) + 3000, text)

    # 発話ログ
    for spk in ["S", "A", "B"]:
        for i, row in df_asr.iterrows():
            v_id, v_speaker, v_start_time, v_end_time, v_offset, content = row
            # 対象話者で無ければスキップ
            if v_speaker != spk:
                continue
            # 時間を直す（端末間オフセットを足し，対話開始時間からの差分を計算し，さらに全体のオフセットを足す）
            v_start_time = datetime.datetime.fromisoformat(v_start_time)
            v_start_time += datetime.timedelta(seconds=v_offset)
            v_start_time_in_video = (v_start_time -
                                     start_time).total_seconds() + offset
            v_end_time = datetime.datetime.fromisoformat(v_end_time)
            v_end_time += datetime.timedelta(seconds=v_offset)
            v_end_time_in_video = (v_end_time -
                                   start_time).total_seconds() + offset

            if spk in ["A", "B"]:
                v_start_time_in_video += asr_start_offset
                v_end_time_in_video += asr_end_offset

            eaf_info.append_annotation(spk, int(v_start_time_in_video * 1000),
                                       int(v_end_time_in_video * 1000),
                                       content)

    write_to_eaf(eaf_info, output_file)


if __name__ == "__main__":
    logdir = "../../../data/02/202111181514"
    output_file = path.join(logdir, "..", "202111181514.eaf")
    offset = 17.194
    asr_start_offset = -0.5
    asr_end_offset = -0.3
    media_file_path = "/Users/fujie/work/woz/data/02/" + \
        "2021-11-18 15.14.17 対話データ収録（テスト用）/video1196553938.mp4"
    log2eaf(logdir, output_file, offset, asr_start_offset, asr_end_offset,
            media_file_path)

    logdir = "../../../data/01/202111181436"
    output_file = path.join(logdir, "..", "202111181436.eaf")
    offset = 7.351
    asr_start_offset = -0.5
    asr_end_offset = -0.3
    media_file_path = "/Users/fujie/work/woz/data/01/" + \
        "2021-11-18 14.34.17 対話データ収録（テスト用）/video2982922143.mp4"
    log2eaf(logdir, output_file, offset, asr_start_offset, asr_end_offset,
            media_file_path)
