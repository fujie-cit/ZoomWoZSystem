# -*- coding: utf-8 -*-

"""
CSV処理
"""
__author__ = "Yuto Akagawa"
__editor__ = "Hayato Katayama"
import csv


class CSVProcessing:
    def __init__(self):
        pass

    def read(self, path):
        f = open(path, 'r')
        reader = csv.reader(f)
        data = []
        for row in reader:
            data.append(row)
        f.close()
        return data

    def write(self, path, data):
        f = open(path, 'w')
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows(data)
        f.close()
