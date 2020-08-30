import os
import sys

from utils import list_dir
from utils import make_dir
from utils import read

ERROR = '============== STDERR ==============='

def chakra(log_path):
  log = read(log_path, 'r')
  error = get_err_msg(log)

  if ('SyntaxError:' in error or
      'ReferenceError:' in error or
      'TypeError:' in error or
      'RangeError:' in error or
      'URIError:' in error or
      'Error in opening file:' in error):
    return 1
  else:
    return get_ret(log)

def get_err_msg(log, read_err=True):
  idx = 1 if read_err else 0
  error = log.split(ERROR)[idx]
  error = error.strip()
  return error

def get_func(eng_name):
  if eng_name == 'chakra':
    return chakra

def get_ret(log):
  ret = log.split('MONTAGE_RETURN: ')
  ret = int(ret[1])
  if ret < 0 and ret != -9:
    return ret
  else:
    return 0

def main(conf):
  func = get_func(conf.eng_name)

  ret_dict = {}
  for log_path in list_dir(conf.log_dir):
    ret = func(log_path)
    if ret not in ret_dict: ret_dict[ret] = []
    ret_dict[ret] += [log_path]

  new_seed_dir = os.path.join(conf.data_dir, 'seed')
  make_dir(new_seed_dir)

  for log_path in ret_dict[0]:
    file_name = os.path.basename(log_path) + '.js'
    js_path = os.path.join(conf.seed_dir, file_name)
    new_js_path = os.path.join(new_seed_dir, file_name)

    with open(js_path, 'r') as fr, \
         open(new_js_path, 'w') as fw:
      for line in fr:
        if ('load("' not in line and
            'load(\'' not in line):
          fw.write(line)
