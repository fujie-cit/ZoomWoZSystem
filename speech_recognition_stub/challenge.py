# coding: utf-8
# SSL(Let's Encrypt)の認証ファイルを作成するためのドメイン確認用プログラム
# 参照 https://python.ms/lets-encrypt/

import flask

app = flask.Flask(__name__)

@app.route(
    "/.well-known/acme-challenge/*********")
def acme_challenge():
    return "******"

app.run(host='0.0.0.0', port=80)
