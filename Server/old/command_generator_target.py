#!/usr/bin/python
# coding: utf-8
#import keras
#model = keras.models.load_model('utterance_lld_final10.h5')
import numpy as np
import matplotlib.pyplot as plt
import socket
import time
from robot_controller import RobotController
import logging

host = '127.0.0.1'
port = 65000
buff = 4096

fig, ax = plt.subplots(1, 1, figsize=(10,2.5))
x = list(range(1,11))
y = list(0 for i in range(10))
cnt = len(x)+1
ax.set_ylim(-0.2, 1.1)
ax.title.set_text('Action Probability')
# 初期化的に一度plotしなければならない
# そのときplotしたオブジェクトを受け取る受け取る必要がある．
# listが返ってくるので，注意
lines, = ax.plot(x, y, color='r')


if __name__ == '__main__':
  rc = RobotController()
  print(1)
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  s.bind((host, port))

  while True:
    s.listen(1)
    print('Waiting for connection')
    cl, addr = s.accept()
    print('Established connection')
    _ = raw_input('START THE CONVERSATION IF YOU PRESS THE "ENTER KET ..."')
    time.sleep(2)
    rc.utter('start','A')
    movement_limit = 10
    present_target = "A"
    while True:
        #try:
        msg = cl.recv(buff)
        #target = cl.recv(buff)
        #action = map(float,msg.strip().split(','))
        try:
            action = float(msg)
        except:
            continue
        print(action)
        y_pred = float(action)

        x.append(cnt)
        y.append(y_pred)
        del x[0]; del y[0]
        lines.set_data(x, y)
        ax.set_xlim((min(x), max(x)))
        cnt+=1
        plt.pause(.01)
        if movement_limit != 0:
            movement_limit -= 1
            continue
        if y_pred > 0.5 and present_target == "A":#max(y) == y_pred:
            rc.look("B")
            present_target = "B"
            movement_limit=5
        elif y_pred < 0.5 and present_target == "B":
            rc.look('A')
            movement_limit=5
            present_target = "A"
