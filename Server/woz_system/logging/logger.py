import threading
import atexit
import queue
import csv

class Logger:
    def __init__(self, filepath, field_names=None):
        """ログファイル（CSVファイル）を書き出すためのクラス．
        Loggerを生成すると，直ちに filepath のファイルが作成されて
        field_names に設定したフィールド名が書き出される．
        既存のファイルが存在した場合は上書きされる．
        field_names が None の場合はヘッダ行は書き出されない．

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
            field_names (list): ヘッダ行のリスト
        """
        self._filepath = filepath
        self._queue = queue.Queue()
        self._thread = threading.Thread(target=self._run)
        self._thread_alive = True

        if field_names:
            self._write_record([field_names], append=False)
        else:
            with open(self._filepath, 'w') as f:
                pass

        # atexit.register(self.close)
        self._thread.start()

    def put(self, data: list):
        if not self._thread_alive:
            raise RuntimeError("already closed.")
        print("put: {}".format(data))
        self._queue.put(data)

    def close(self):
        self._thread_alive = False
        self._queue.put([])
        self._thread.join()
        # atexit.unregister(self.close)

    def _write_record(self, datas, append=True):
        mode = 'a' if append else 'w'
        with open(self._filepath, mode, newline='') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            writer.writerows(iter(datas))

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
