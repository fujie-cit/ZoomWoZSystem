#coding:utf-8
__editor__ = "Hayato Katayama"
import sys
sys.path.append('/Users/dialog/Desktop/demo')
#from nlu import *
import time, random
"""

wizard => model に変更して自動制御

"""

from robot_controller import RobotController
import logging
#l = logging.getLogger()
#l.addHandler(logging.FileHandler("/dev/null"))
rc = RobotController()
topic_history_length = 8



if __name__ == '__main__':
    spreco_A = []
    spreco_B = []
    print "START!!!"
    time.sleep(2)
    #import pdb; pdb.set_trace()
    rc.utter("start","A")
    while 1:
        pred = 0
        #print(len(rc.rrmA.spreco_memory))
        time.sleep(0.1)
        if len(spreco_A) != len(rc.rrmA.spreco_memory):
            print('A talked..')
            print("length:",len(rc.rrmA.spreco_memory))
            spreco_A.append(rc.rrmA.spreco_memory[-1])
            ####################model入力#########
            #pred = wakati(spreco_A[-1])
            pred = random.choice([0,0,1])
            print(pred)
            if pred == 1:
                print('response ON...')
                spreco_A=[]
                command = "response-passive"
                rc.utter(command,"A")
                rc.rrmA.reset_spreco_memory()##消すかも

        if spreco_B != rc.rrmB.spreco_memory:
            spreco_B = rc.rrmB.spreco_memory
            ####################model入力#########
            pred = wakati(spreco_B)
            if pred == 1:
                spreco_B = []
                command = "response-passive"
                rc.utter(command,"B")
