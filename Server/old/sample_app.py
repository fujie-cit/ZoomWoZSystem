# coding:utf-8
__editor__ = "Hayato Katayama"
from flask import Flask, render_template, request
# from robot_controller import RobotController
import logging
# l = logging.getLogger()
# l.addHandler(logging.FileHandler("/dev/null"))
host = 'localhost'
port = 8080
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index0227.html')


if __name__ == '__main__':
    app.run(host=host, port=port, debug=False)
