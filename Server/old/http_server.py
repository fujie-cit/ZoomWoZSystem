# -*- coding:utf-8 -*-

import urlparse
import SimpleHTTPServer
import SocketServer
import os
import sys
import os.path
from robot_controller import RobotController
import time


class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def get_data(self, params):
        message = params.get('message')[0]
        detail = params.get('detail')[0]
        print(type(message))
        print(type(detail))
        if message == 'look':
            rc.look(detail)
        elif message == 'nod':
            rc.nod(detail)
        elif message == 'changetopic':
            rc.change_topic(detail, "U")
        elif message == 'terminate':
            rc.terminate(detail)
        else:
            rc.utter(message, detail)
    handlers = {}
    handlers['/woz'] = get_data

    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(parsed_path.query)
        path = parsed_path.path
        print(parsed_path)
        print(params)
        print(path)
        if path in MyHandler.handlers:
            MyHandler.handlers[path](self, params)
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == '__main__':
    rc = RobotController()
    host = '192.168.100.104'
    # host = '192.168.179.4'
    port = 8080
    httpd = SocketServer.TCPServer((host, port), MyHandler)
    httpd.serve_forever()
