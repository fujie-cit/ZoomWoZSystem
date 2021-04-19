# coding: utf8
from csv_processing import CSVProcessing
import threading
import time
import datetime

csv = CSVProcessing()
csv_path = "topic_memory.csv"

def output_html(o1, topic):
    topic_str = ""
    cur_topic = ""
    print topic
    for i, t in enumerate(topic):
        if len(topic_str) == 0:
            topic_str = t[0]
        else:
            if i == len(topic) - 1:
                cur_topic = t[0]
            else:
                topic_str += " → " + t[0]
    print >>o1, "<html>"
    print >>o1, "<head>"
    print >>o1, '<meta http-equiv="Content-Type" content="text/html; charset=utf8" />'
    print >>o1, "</head>"
    print >>o1, "<body>"
    print >>o1, "<h1>History</h1>"
    print >>o1, "<h2>"+ topic_str + "</h2>"
    print >>o1, "<h1>Current</h1>"
    print >>o1, "<h2>"+ cur_topic + "</h2>"
    print >>o1, "<table border="1">"
    print >>o1, "<tr>"
    print >>o1, "<th>日付</th>"
    print >>o1, "<th>集合場所</th>"
    print >>o1, "</tr>"
    print >>o1, "<th>日付</th>"
    print >>o1, "<th>集合場所</th>"
    print >>o1, "</tr>"
    print >>o1, "<th>日付</th>"
    print >>o1, "<th>集合場所</th>"
    print >>o1, "</tr>"
    print >>o1, "<th>日付</th>"
    print >>o1, "<th>集合場所</th>"
    print >>o1, "</tr>"
    print >>o1, "<th>日付</th>"
    print >>o1, "<th>集合場所</th>"
    print >>o1, "</tr>"
    print >>o1, "</table>"
    print >>o1, '<meta http-equiv="refresh" content="3" />'
    print >>o1, "</body>"
    print >>o1, "</html>"

#
# 極小ウェブサーバー
#
from BaseHTTPServer import *

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        topic = csv.read(csv_path)
        print topic
        output_html(self.wfile, topic)

time.sleep(1)
HTTPServer(('192.168.100.104', 8700), MyHandler).serve_forever()
