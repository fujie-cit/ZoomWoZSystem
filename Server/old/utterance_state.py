# -*- coding: utf-8 -*-

"""
ロボットの発話状況を監視する
"""
__author__ = "Yuto Akagawa"
__editor__ = "Hayato Katayama"
import os.path
import sys
import subprocess
import time
import random
import threading
from monea_connector import MoneaConnector
from conversation_manager import ConversationManager
from logger import Logger
os.environ["REGISTRY_SERVER_PORT"]="25001"


class UtteranceState:

    def __init__(self, remote, logger, conv_manager):
        self.remote = remote
        self.contents=''
        self.target=''
        self.logger = logger
        self.conv_manager = conv_manager
        thr=threading.Thread(target=self.watcher)
        thr.setDaemon(True)
        thr.start()

    def watcher(self):
        while 1:
            self.remote.timedUpdate(-1)
            order = self.remote.getAsString("tree").decode("euc-jp")
            if 'speak' in order:
                contents = order.split('{')[1].split(']}')[0].split('[')[1]
                target = order.split('t=')[1].split(',')[0][0]
                if (self.get_contents() != contents or self.get_target() != target) and len(self.get_contents()) > 0:
                    print 'speak_end' + target
                    self.logger.stamp('SpeakEnd', self.conv_manager.get_topic(), self.get_target().encode('utf-8'), self.get_contents().encode('utf-8'))
                self.set_state(CONTENTS = contents, TARGET = target)
            else:
                if self.get_contents() != '':
                    print 'speak_end' + target
                    self.logger.stamp('SpeakEnd', self.conv_manager.get_topic(), self.get_target().encode('utf-8'), self.get_contents().encode('utf-8'))
                    self.set_state()

    def set_state(self, CONTENTS='', TARGET=''):
        self.contents = CONTENTS
        self.target = TARGET

    def get_contents(self):
        return self.contents

    def get_target(self):
        return self.target
"""
if __name__ == '__main__':
    l = Logger()
    us = UtteranceState(l)
"""
