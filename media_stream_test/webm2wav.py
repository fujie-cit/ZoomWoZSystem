import subprocess as sp
import shlex
import queue
import threading


class Webm2WavDecoder:
    def __init__(self):
        # FFmpegのコマンド．パスは通っていることが前提
        cmd = "ffmpeg -loglevel -8 -f webm -i pipe:0 -acodec pcm_s16le -ar 16000 -ac 1 -f wav pipe:1"
        cmd_split = shlex.split(cmd)

        self._ffmpeg = sp.Popen(
            cmd_split, bufsize=0, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.DEVNULL)

        self._input_queue = queue.Queue()
        self._output_queue = queue.Queue()

        self._is_alive = True

        self._worker_input_thread = threading.Thread(target=self._work_input)
        self._worker_input_thread.daemon = True
        self._worker_output_thread = threading.Thread(target=self._work_output)
        self._worker_output_thread.daemon = True

        # print("BEFORE self._worker_thread.start()")
        self._worker_input_thread.start()
        self._worker_output_thread.start()
        # print("AFTER  self._worker_thread.start()")

    def put(self, data):
        # print("BEFORE put {}".format(len(data)))
        self._input_queue.put(data)
        # print("AFTER  put {}".format(len(data)))

    def get(self):
        data = b''
        while not self._output_queue.empty():
            data += self._output_queue.get()
        return data

    def stop(self):
        self._is_alive = False
        self._input_queue.put(b'dummy')
        self._ffmpeg.kill() # terminate では止まらない
        self._worker_input_thread.join()
        self._worker_output_thread.join()

    def _work_input(self):
        written_count = 0
        while True:
            # print("RETURN CODE: {}".format(self._ffmpeg.returncode))
            chunk = self._input_queue.get(block=True)

            if not self._is_alive:
                break

            # print("BEFORE write")
            if self._ffmpeg.returncode is not None:
                break
            self._ffmpeg.stdin.write(chunk)
            # print("AFTER  write")

    def _work_output(self):
        chunk_size = 1920
        while True:
            try:
                # print("BEFORE read stdout")
                data_out = self._ffmpeg.stdout.read(chunk_size)
                # print("AFTER  read stdout")
                # print("DATA OUT: {}".format(len(data_out)))
                self._output_queue.put(data_out)
            except OSError:
                pass

            if not self._is_alive:
                break

            if self._ffmpeg.returncode is not None:
                break
