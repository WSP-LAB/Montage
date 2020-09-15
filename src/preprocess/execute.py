import os
import threading

from subprocess import PIPE
from subprocess import Popen

from utils import kill_proc
from utils import list_dir
from utils import make_dir
from utils import pool_map
from utils import read
from utils import write
from utils.logger import print_msg

class Executor:
  def __init__(self, conf):
    self._conf = conf

  def const_log_path(self, js_path, log_dir):
    log_name = os.path.basename(js_path)
    log_name = log_name.split('.')[0]
    return os.path.join(log_dir, log_name)

  def execute(self, proc, log_path, timeout):
    timer = threading.Timer(timeout,
                            lambda p: kill_proc(p), [proc])
    timer.start()
    stdout, stderr = proc.communicate()
    ret = proc.returncode

    self.write_log(log_path, stdout, stderr, ret)
    timer.cancel()

  def run(self, js_path, cwd):
    cmd = [self._conf.eng_path]
    cmd += self._conf.opt
    cmd += [js_path]
    proc = Popen(cmd, cwd=cwd, stdout=PIPE, stderr=PIPE)
    log_path = self.const_log_path(js_path,
                                   self._conf.log_dir)
    self.execute(proc, log_path, self._conf.timeout)

  def write_log(self, log_path, stdout, stderr, ret):
    log = b'\n============== STDOUT ===============\n'
    log += stdout
    log += b'\n============== STDERR ===============\n'
    log += stderr
    log += b'\nMONTAGE_RETURN: %d' % (ret)
    write(log_path, log)

def exec_chakra(js_path, conf):
  tmp_js_path = rewrite_file(js_path, conf.data_dir)

  executor = Executor(conf)
  cwd = os.path.dirname(js_path)
  executor.run(tmp_js_path, cwd)

  os.remove(tmp_js_path)

def main(pool, conf):
  make_dir(conf.log_dir)

  js_list = []
  for js in list_dir(conf.seed_dir):
    if (js.endswith('.js') and
        os.path.getsize(js) < 30 * 1024):  # Excludes JS over 3KB
      js_list += [js]

  num_js = len(js_list)
  msg = 'Start executing %d JS files' % (num_js)
  print_msg(msg, 'INFO')

  if conf.eng_name == 'chakra':
    exec_func = exec_chakra

  pool_map(pool, exec_func, js_list, conf=conf)

def rewrite_file(js_path, tmp_dir):
  PREFIX = b'load = WScript.LoadScriptFile'

  code = read(js_path)
  code = b'\n'.join([PREFIX, code])

  js_name = os.path.basename(js_path)
  tmp_js_path = os.path.join(tmp_dir, js_name)

  write(tmp_js_path, code)

  return tmp_js_path
