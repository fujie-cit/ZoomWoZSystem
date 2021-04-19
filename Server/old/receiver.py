# -*- coding: utf-8 -*-
import sys
import subprocess
"""MONEAに書き込まれた結果を受け取(って処理す)るサンプルプログラム"""


def get_lines(cmd):
    '''
    :param cmd: str 実行するコマンド.
    :rtype: generator
    :return: 標準出力 (行毎).
    '''
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
        line = proc.stdout.readline()
        if line:
            yield line
            # TODO parse

        if not line and proc.poll() is not None:
            break


if __name__ == '__main__':
    jar_path = './jar/displaystdout.jar'
    xml_path = './config/display.xml'
    remoteName = 'GENERATOR'
    tagToWatch = 'Content'
    cmd = 'java -jar {0} -m {1} -r {2} -t {3}'.format(
            jar_path, xml_path, remoteName, tagToWatch
            )
    for line in get_lines(cmd=cmd):
        sys.stdout.write(line)
