import threading
import os, sys
from functools import partial

current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append (os.path.abspath(os.path.join(current_dir, '../../MMDAgentClient', 'run')))
import run_action_player


class AgentPlayerWrapperError(Exception):
    pass


class AgentPlayerWrapper:
    def __init__(self):
        self._agent_player = run_action_player.AgentPlayer()

        self._task = None

        self._cond = threading.Condition()
        self._is_alive = True
        self._thread = threading.Thread(target=self._worker)

        self._thread.start()

    def join(self):
        if not self._is_alive:
            return
        with self._cond:
            self._is_alive = False
            self._cond.notify_all()
        self._thread.join()
        self._thread = None

    def look(self, usr):
        task = partial(self._agent_player.look, usr)
        self._put_task(task)

    def nod(self):
        task = self._agent_player.nod()
        self._put_task(task)

    def _put_task(self, task):
        if self._task is not None:
            raise AgentPlayerWrapperError("another action being executed")
        if not self._cond.acquire(blocking=False):
            raise AgentPlayerWrapperError("could not acquire the lock")            
        try:
            self._task = task
            self._cond.notify_all()
        finally:
            self._cond.release()

    def _worker(self):
        while True:
            with self._cond:
                while self._is_alive and self._task is None:
                    self._cond.wait()
                if not self._is_alive:
                    break
                if self._task is None:
                    continue
                print("executing ... {}".format(self._task))
                self._task() 
                self._task = None
                self._cond.notify_all()


class SoundPlayer:
    def __init__(self):
        self._sound_player = run_action_player.sound_player

    def play(self, data: bytes):
        self._sound_player.put(data)
