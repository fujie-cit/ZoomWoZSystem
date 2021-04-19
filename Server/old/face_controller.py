# -*- coding: utf-8 -*-

"""
キーボードイベントの監視(顔向き、頷き制御)
"""
__author__ = "Yuto Akagawa"

import os
import os.path
import csv
import sys
#from msvcrt import getch
import getch
import threading

class FaceController:
    def __init__(self):
        #self.rc = robot_controller
        thr=threading.Thread(target=self.watcher)
        thr.setDaemon(True)
        thr.start()

    def watcher(self):
        while 1:
            key = getch.getch()
            if key == "j": #J: Look A
                print "LA"
                #self.rc.look("A")
            elif key == "k": #K: Nod
                print "Nod"
                #self.rc.nod()
            elif key == "l": #L: Look B
                print "LB"
                #self.rc.look("B")

if __name__ == '__main__':
    fc = FaceController()
