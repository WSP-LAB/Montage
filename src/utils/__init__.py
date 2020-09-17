import atexit
import json
import os
import pickle
import shutil
import signal
import string
import torch
import ujson

from functools import partial
from hashlib import sha1
from random import choice

from utils.logger import get_msg
from utils.logger import print_msg
from utils.node import PROP_DICT

def data2tensor(batch, tensor_type='Long'):
  if tensor_type == 'Long':
    batch = torch.cuda.LongTensor(batch)
  elif tensor_type == 'Byte':
    batch = torch.cuda.ByteTensor(batch)
  elif tensor_type == 'Float':
    batch = torch.cuda.FloatTensor(batch)
  return batch

def get_node_type(node):
  return node['type']

def hash_frag(frag):
  return hash_val(stringify_frag(frag))

def hash_val(text):
  if type(text) is str:
    text = text.encode('utf-8')
  return sha1(text).hexdigest()

def init_worker():
  signal.signal(signal.SIGINT, signal.SIG_IGN)

def is_node_list(node):
  return type(node) == list

def is_single_node(node):
  return (type(node) == dict and
          'type' in node)

def kill_proc(proc):
  if proc.poll() is None:
    proc.kill()

def list_dir(dir_path):
  return [os.path.join(dir_path, f) for f in os.listdir(dir_path)]

def load_ast(ast_path):
  with open(ast_path, 'r') as f:
    try:
      ast = ujson.load(f)
    except Exception as e:
      dec = json.JSONDecoder()
      f.seek(0, 0)
      ast = f.read()
      ast = dec.decode(ast)
  js_name = os.path.basename(ast_path)[:-2]
  return js_name, ast

def load_pickle(dpath):
  with open(dpath, 'rb') as f:
    data = pickle.load(f)
  return data

def make_dir(dir_path):
  ans = 'y'
  if os.path.exists(dir_path):
    msg = 'Do you want to delete %s? (y/n): ' % (dir_path)
    msg = get_msg(msg, 'WARN')
    ans = input(msg)
    if ans == 'y':
      shutil.rmtree(dir_path)
      os.makedirs(dir_path)
    else:
      if ans != 'n':
        print_msg('Wrong Answer', 'ERROR')
      os._exit(1)
  else:
    os.makedirs(dir_path)
  return dir_path

def make_tmp_dir(dir_path):
  dir_path = os.path.join(dir_path, random_string(10))
  os.makedirs(dir_path)
  return dir_path

def pool_map(pool, func, list, **args):
  try:
    func = partial(func, **args)
    return pool.map(func, list)
  except KeyboardInterrupt:
    print_msg('Terminating workers ...', 'INFO')
    pool.terminate()
    pool.join()
    print_msg('Killed processes', 'INFO')
    os.killpg(os.getpid(), signal.SIGKILL)

def random_string(length):
  candidate = string.ascii_letters + string.digits
  rand_str = [choice(candidate) for i in range(length)]
  return ''.join(rand_str)

def read(file_name, mode='rb'):
  with open(file_name, mode) as f:
    return f.read()

def store_pickle(dpath, data):
  with open(dpath, 'wb') as f:
    pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

def stringify_frag(node):
  str_val = ''
  if 'type' in node:
    node_type = get_node_type(node)
    prop_list = PROP_DICT[node_type]
  else:
    prop_list = sorted(node.keys())

  for key in prop_list:
    if key not in node: continue
    child = node[key]

    # If it has a single child
    if type(child) == dict:
      str_val += '{'
      str_val += stringify_frag(child)
      str_val += '}'
    # If it has multiple children
    elif type(child) == list:
      str_val += '['
      for _child in child:
        if _child is None:
          str_val += str(None)
        else:
          str_val += stringify_frag(_child)
      str_val += ']'
    # If it is a terminal
    else:
      str_val += str((key, node[key]))
  return str_val

def write(file_name, content, mode='wb'):
  with open(file_name, mode) as f:
    f.write(content)

def write_ast(ast_path, ast):
  ast = json.dumps(ast, indent=2)
  ast = str.encode(ast)
  write(ast_path, ast)
