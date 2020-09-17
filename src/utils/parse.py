import os

from subprocess import PIPE
from subprocess import Popen

from utils import list_dir
from utils import make_dir
from utils.logger import print_msg

class Parser:
  def parse(self, seed_dir, ast_dir):
    js_list = list_dir(seed_dir)
    num_js = len(js_list)
    msg = 'Start parsing %d JS files' % (num_js)
    print_msg(msg, 'INFO')

    cmd = ['node', 'utils/parse.js']
    cmd += [seed_dir, ast_dir]
    parser = Popen(cmd, cwd='./',
                   stdin=PIPE, stdout=PIPE, stderr=PIPE)
    parser.wait()

class SingleParser:
  def __init__(self):
    cmd = ['node', 'utils/parse.js']
    self._parser = Popen(cmd, cwd='./', bufsize=0,
                         stdin=PIPE, stdout=PIPE, stderr=PIPE)

  def __del__(self):
    self._parser.terminate()

  def parse(self, js_path):
    js_path = str.encode(js_path + '\n')
    self._parser.stdin.write(js_path)
    ast_path = self._parser.stdout.readline()
    ast_path = ast_path.strip()
    return ast_path
