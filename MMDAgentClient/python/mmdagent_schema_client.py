# coding: utf-8
import socket
import readline
import threading as th
import time

class MMDAgentSchemaClient (object):
    u"""MMDAgentSchemaに接続して各自由度の制御を行うためのクラス.
    """

    # MMDAgentのホスト名のデフォルト値
    DEFAULT_HOST = 'localhost'
    # MMDAgentのポートのデフォルト値
    DEFAULT_PORT = 7000

    # 全体をリセットするコマンド
    COMMAND_RESET = 'reset'

    # 全DOF名
    DOF = ('EYE_R_P', 'EYE_R_Y',
           'EYE_L_P', 'EYE_L_Y',
           'MOU',
           'NEC_X_P', 'NEC_X_Y',
           'R_SHO_P', 'R_SHO_R',
           'R_ELB_P', 'R_ELB_Y',
           'R_WRI_Y', 'R_WRI_R',
           'L_SHO_P', 'L_SHO_R',
           'L_ELB_P', 'L_ELB_Y',
           'L_WRI_Y', 'L_WRI_R',
           'TURRET')

    # 全コマンド（リセットと全DOF）
    ALL_COMMANDS = (COMMAND_RESET,) + DOF

    u"""各DOFの最小，最大値"""
    MIN_MAX_POS = {
        'EYE_R_P': (-20, 20),
        'EYE_R_Y': (-15, 15),
        'EYE_L_P': (-20, 20),
        'EYE_L_Y': (-15, 15),
        'MOU':     (  0, 30),
        'NEC_X_P': (-30, 40),
        'NEC_X_Y': (-40, 40),
        'R_SHO_P': (-50, 85),
        'R_SHO_R': (  0, 60),
        'R_ELB_Y': (-90, 90),
        'R_WRI_Y': (-90, 90),
        'R_WRI_R': (-90, 90),
        'L_SHO_P': (-50, 85),
        'L_SHO_R': (  0, 60),
        'L_ELB_Y': (-90, 90),
        'L_WRI_Y': (-90, 90),
        'L_WRI_R': (-90, 90),
        'TURRET':  (-180, 180),
    }

    @classmethod
    def get_min_pos (cls, dof):
        return cls.MIN_MAX_POS[dof][0]

    @classmethod
    def get_max_pos (cls, dof):
        return cls.MIN_MAX_POS[dof][1]

    def __init__ (self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.__cond = th.Condition()
        self._host = host
        self._port = port
        self._client = None

        self._conn_thread = th.Thread (target=self._connect)
        self._conn_thread.daemon = True
        self._conn_thread.start()

    def _connect (self):
        client = None
        while True:
            with self.__cond:
                if self._client != None:
                    self.__cond.wait()
            try:
                client = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
                client.connect ((self._host, self._port))
                with self.__cond:
                    self._client = client
            except socket.error as e:
                if e.errno != socket.errno.ECONNREFUSED:
                    raise
                else:
                    time.sleep(1)

    def is_connected (self):
        with self.__cond:
            return self._client != None

    def send (self, cmd, target=None):
        if not cmd in MMDAgentSchemaClient.ALL_COMMANDS:
            print("command not found")
            return
        msg = ''
        if cmd == MMDAgentSchemaClient.COMMAND_RESET:
            msg = "TARGET_RESET DUMMY\n"
        else:
            if target == None:
                print("target is not given")
                return
            msg = "TARGET_SET %s|%s\n" % (cmd, target)

        with self.__cond:
            if self._client == None:
                # not connected
                return
            try:
                self._client.send(msg.encode("utf-8"))
            except socket.error as e:
                self._client = None
                self.__cond.notify_all()

if __name__ == "__main__":
    c = MMDAgentSchemaClient()

    while True:
        try:
            prompt = "> "
            if not c.is_connected ():
                prompt = "*> "

            line = input(prompt)
            ins = line.split(' ')
            if ins[0] == '':
                continue
            c.send (*ins)
        except KeyboardInterrupt:
            break
