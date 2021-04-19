# -*- coding: utf-8 -*-
"""
ラベル作成
"""
__author__ = "Yuto Akagawa"
__editor__ = "Hayato Katayama"
import datetime
from csv_processing import CSVProcessing


class Logger:
    def __init__(self):
        self.csv = CSVProcessing()
        self.label = []

    def stamp(self, action, topic, target, content):
        now = datetime.datetime.now()
        time = now.strftime("%Y%m%d%H%M%S.") + "%06d" % (now.microsecond)
        self.label.append([time, action, topic, target, content])

    def write(self, fname):
        if fname == '':
            now = datetime.datetime.now()
            fname = now.strftime("%Y%m%d%H%M")
        self.csv.write('../DialogAct/' + fname + '.csv', self.label)
        self.label = []
