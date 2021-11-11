# coding:utf-8
__editor__ = "Jin Sakuma"
from flask import Flask, render_template, request
from robot_controller import RobotController
import sys
import logging
import logging.handlers


app = Flask(__name__)
# FlaskのLoggerを無効化する
# app.logger.disabled = True
# werkzeugのLoggerを無効化する
# werkzeug_logger = logging.getLogger('werkzeug')
# werkzeug_logger.disabled = True

# logger = logging.getLogger()
# logger.addHandler(logging.FileHandler("/dev/null"))

# host = 'dm'
host = 'localhost'
port = 8080
app = Flask(__name__)
rc = RobotController()
topic_history_length = 6


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stt', methods=['POST'])
def stt():
    date = request.form['date']
    time = request.form['time']
    text = request.form['text']
    user = request.form['user']
    topics, persons = rc.main(date, time, user, text)

    while len(topics) < topic_history_length:
        topics.append('NONE')
        persons.append('NONE')
    while len(topics) > topic_history_length:
        topics.pop(0)
        persons.pop(0)

    message_dic = {}
    message_dic['topics'] = topics
    message_dic['person'] = persons

    return render_template('index.html', message=message_dic)


@app.route('/send/<command>/<detail>', methods=['POST'])
def push_button(command, detail):
    # command = command.encode('utf-8')
    # detail = detail.encode('utf-8')
    if command == 'look':
        topics, persons = rc.look(detail)
    elif command == 'nod':
        topics, persons = rc.nod(detail)
    elif command == 'cancel':
        topics, persons = rc.look(target='U')
    elif command == 'change-topic':
        topics, persons = rc.change_topic_title(detail)
    elif command == 'change-person':
        topics, persons = rc.change_topic_person(detail)
    elif command == 'change-genre':
        topics, persons = rc.change_genre(detail, "U")
    else:
        topics, persons = rc.utter(command, detail)

    while len(topics) < topic_history_length:
        topics.append('NONE')
    while len(topics) > topic_history_length:
        topics.pop(0)
    while len(persons) < topic_history_length:
        persons.append('NONE')
    while len(persons) > topic_history_length:
        persons.pop(0)

    message_dic = {}
    message_dic['topics'] = topics
    message_dic['person'] = persons

    # active = '監督'
    return render_template('index.html', message=message_dic)


if __name__ == '__main__':
    app.run(debug=False, host=host, port=port, threaded=True)
