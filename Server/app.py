# coding:utf-8
__editor__ = "Jin Sakuma"
from flask import Flask, render_template, request
from werkzeug.utils import get_content_type
# from robot_controller import RobotController
from woz_system.woz_controller import WoZController 
import sys
# import logging
# import logging.handlers
import traceback

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

def get_index_html_context() -> dict:
    """index.htmlをレンダリングするために必要なコンテキストを取得する"""

    # 対話履歴関係
    movie_list, person_list = woz_controller.get_latest_information()
    movie_list.extend([dict(title='None', movie_id=0)] * topic_history_length)
    movie_list = movie_list[:topic_history_length]
    person_list.extend(['None'] * topic_history_length)
    person_list = person_list[:topic_history_length]
    message_dict = dict(movie_list=movie_list, person=person_list)

    # 対話ID関係
    dialog_id = woz_controller.get_dialog_id()

    # 音声認識関係
    user_list = woz_controller.get_user_list()
    user_list.insert(0, "--")
    user_a = woz_controller.get_user_a()
    user_a = "--" if user_a is None else user_a
    user_b = woz_controller.get_user_b()
    user_b = "--" if user_b is None else user_b

    return dict(
        movie_list=movie_list, 
        person=person_list,
        message=message_dict,
        dialog_id=dialog_id,
        user_list=user_list,
        user_a=user_a,
        user_b=user_b
    )

@app.route('/')
def index():
    context = get_index_html_context()
    return render_template('index.html', **context)

@app.route('/test')
def test():
    user_list = ['--', 'fujie', 'sakuma', 'koba', 'suzuki']
    return render_template('index.html', dialog_id="2021111601", user_list=user_list, user_a="--")

@app.route('/update_user_a', methods=['POST'])
def update_user_a():
    if "user_name" in request.form:
        user_name = request.form["user_name"]
        woz_controller.set_user_a(user_name)
    
    context = get_index_html_context()
    return render_template('index.html', **context)

@app.route('/update_user_b', methods=['POST'])
def update_user_b():
    if "user_name" in request.form:
        user_name = request.form["user_name"]
        woz_controller.set_user_b(user_name)
    context = get_index_html_context()
    return render_template('index.html', **context)

@app.route('/send/<command>/<detail>', methods=['POST'])
def push_button(command, detail):
    debug_message = None
    try: 
        woz_controller.execute(command, detail)
    except Exception as e:
        debug_message = traceback.format_exc()
        # debug_message = debug_message.replace('\n', '<br>')

    context = get_index_html_context()
    context['debug_message'] = '<pre>' + debug_message  + '</pre>'
    return render_template('index.html', **context)

if __name__ == '__main__':
    app.run(debug=False, host=host, port=port, threaded=True)
