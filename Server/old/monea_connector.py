# -*-coding: utf-8 -*-
"""Moneaに接続してContextを取得する(Singlton)
 - 同じmodle.xmlに対しては同じContextを取得する
"""

import monea
import os
import sys


class MoneaConnector(object):
    _instance_dict = {}

    def __new__(cls, moduleXmlPath):
        if moduleXmlPath not in cls._instance_dict.keys():
            instance = super(MoneaConnector, cls).__new__(cls, moduleXmlPath)
            cls._instance_dict[moduleXmlPath] = instance
        return cls._instance_dict[moduleXmlPath]

    def __init__(self, moduleXmlPath):
        try:
            if not os.path.isfile(moduleXmlPath):
                raise IOError('file {0} is not exist.'.format(moduleXmlPath))
            self.context = monea.ModuleContextFactory_newContext(moduleXmlPath, 0)
        except IOError as e:
            sys.exit(e)
