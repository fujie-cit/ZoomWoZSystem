import threading
import atexit
import queue
import csv
import json
import os
import numpy

# https://wtnvenga.hatenablog.com/entry/2018/05/27/113848
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.integer):
            return int(obj)
        elif isinstance(obj, numpy.floating):
            return float(obj)
        elif isinstance(obj, numpy.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)


class JSONLogger:
    def __init__(self, filepath):
        """JSONログファイルを書き出すためのクラス．
        JSONログファイルは，与えられた dict を随時JSON化して書き出したものである．
        明示的に閉じられない限り，全体をJSONとして読み込むことはできない（ ] で閉じられないため．）

        JSONLoggerを生成すると，直ちに filepath のファイルが作成されて
        リストを開始する記号 [ が書き出される．
        既存のファイルが存在した場合は上書きされる．

        実際の値の書き出しには put メソッドを使う．
        putメソッドはキューに値を保存するのみであり，
        実際のファイルの書き出しはバックグラウンドで行われるため
        処理時間のオーバーヘッドは小さい．
        
        ファイルは逐次更新される（最新の情報書き出しは保証されないが，
        過負荷の状態にならない限り遅延はそれほどないと思われる）

        ログファイルの更新を停止することになったら，close メソッドを呼ぶ．
        一度 close メソッドが呼ばれた Logger インスタンスに対しては
        put メソッドを再び呼び出すことはできない．

        Args:
            filepath (string): ログファイルのパス
        """
        self._filepath = filepath
        self._queue = queue.Queue()
        self._thread = threading.Thread(target=self._run)
        self._thread_alive = True
        self._cond = threading.Condition()

        with open(self._filepath, 'w') as f:
            f.write("[" + os.linesep)

        # 書き込んだレコード数
        self._count = 0

        # 実際に書き出したデータ数
        self._count_effective = 0

        # atexit.register(self.close)
        self._thread.start()

    def put(self, data: dict):
        if not self._thread_alive:
            raise RuntimeError("already closed.")
        print("put: {}".format(data))
        with self._cond:
            self._count += 1
            self._queue.put(data)

    def get_new_id(self):
        with self._cond:
            return self._count + 1

    def close(self):
        self._thread_alive = False
        self._queue.put([])
        self._thread.join()
        # atexit.unregister(self.close)
        with open(self._filepath, "a", newline='') as f:
            f.write("]" + os.linesep)


    def _write_record(self, datas, append=True):
        mode = 'a' if append else 'w'
        with open(self._filepath, mode, newline='') as f:
            for data in datas:
                # 最初の1回以降は , を書き出す
                if self._count_effective > 0:
                    f.write(',' + os.linesep)
                # データの書き出し
                f.write(json.dumps(data, indent=2, cls = MyEncoder, ensure_ascii=False))
                # 書き出し数の更新
                self._count_effective += 1
                        

    def _run(self):
        while self._thread_alive:
            datas = []
            try:
                data = self._queue.get(timeout=1.0)
                datas.append(data)
                while not self._queue.empty():
                    data = self._queue.get()
                    datas.append(data)
            except queue.Empty:
                pass
            if self._thread_alive and len(datas) > 0:
                self._write_record(datas)
