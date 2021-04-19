# -*- coding: utf-8 -*-

"""
ロボットの発話状況を監視する
"""
__author__ = "Yuto Akagawa"

import os.path
import sys
import subprocess
import time
import random
from monea_connector import MoneaConnector   
from logger import Logger
os.environ["REGISTRY_SERVER_PORT"]="25001"

class UtteranceState:
    def __init__(self, logger):
        jar_path = '../jar/displaystdout.jar'
        xml_path = '../config/moduleWoz.xml'
        remoteName = 'ActionDecoderTree'
        tagToWatch = 'Content'
        self.cmd = 'java -jar {0} -m {1} -r {2} -t {3}'.format(
        jar_path, xml_path, remoteName, tagToWatch
        )
        self.logger = logger 

    def run(self):
	count = 0
        for line in self.get_lines(cmd=self.cmd):
            sys.stdout.write(line)
            print count
            count += 1 
            print line
            if 'speak' in line:
                self.logger.stamp('isspeak', '', '') 
            elif 'nod' in line:
                self.logger.stamp('isspeak', '', '') 

    def get_lines(self, cmd):
        '''
        :param cmd: str 実行するコマンド.
        :rtype: generator
        :return: 標準出力 (行毎).
        '''
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = proc.stdout.readline()
            if line:
                yield line
                # TODO parse
            if not line and proc.poll() is not None:
                break

if __name__ == '__main__':
    us = UtteranceState()
    us.run()

