# coding:utf-8
__editor__ = "Jin Sakuma"
from flask import Flask, render_template, request
# from robot_controller import RobotController
from woz_system.woz_controller import WoZController 
import sys
# import logging
# import logging.handlers


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
# rc = RobotController()
topic_history_length = 6
woz_controller = WoZController()

@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/stt', methods=['POST'])
# def stt():
#     date = request.form['date']
#     time = request.form['time']
#     text = request.form['text']
#     user = request.form['user']
#     topics, persons = rc.main(date, time, user, text)

#     while len(topics) < topic_history_length:
#         topics.append('NONE')
#         persons.append('NONE')
#     while len(topics) > topic_history_length:
#         topics.pop(0)
#         persons.pop(0)

#     message_dic = {}
#     message_dic['topics'] = topics
#     message_dic['person'] = persons

#     return render_template('index.html', message=message_dic)


@app.route('/send/<command>/<detail>', methods=['POST'])
def push_button(command, detail):
    woz_controller.execute(command, detail)

    title_list, person_list = woz_controller.get_latest_information()

    title_list.extend(['None'] * topic_history_length)
    title_list = title_list[:topic_history_length]
    person_list.extend(['None'] * topic_history_length)
    person_list = person_list[:topic_history_length]
    message_dict = dict(
        topics=title_list, person=person_list
    )

    return render_template('index.html', message=message_dict)

if __name__ == '__main__':
    app.run(debug=False, host=host, port=port, threaded=True)
