import os
from subprocess import PIPE
from subprocess import Popen

from utils import hash_frag
from utils import write_ast

class CodePrinter:
  def __init__(self, js_dir):
    self._js_dir = js_dir
    cmd = ['node', 'utils/ast2code.js', js_dir]
    self._printer = Popen(cmd, cwd='./', bufsize=0,
                          stdin=PIPE, stdout=PIPE, stderr=PIPE)

  def __del__(self):
    self._printer.terminate()

  def ast2code(self, ast):
    ast_name = hash_frag(ast) + '.json'
    ast_path = os.path.join(self._js_dir, ast_name)
    write_ast(ast_path, ast)

    ast_path = str.encode(ast_path + '\n')
    self._printer.stdin.write(ast_path)
    js_path = self._printer.stdout.readline()
    js_path = js_path.decode('utf-8').strip()
    os.remove(ast_path.strip())

    if 'Error' in js_path:
      return None
    else:
      return js_path
