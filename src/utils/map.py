import os

from utils import get_node_type
from utils import is_node_list
from utils import is_single_node
from utils import list_dir
from utils import load_ast
from utils import make_dir
from utils import trim_seed_name
from utils import write
from utils.harness import Harness
from utils.logger import print_msg
from utils.node import PROP_DICT
from utils.node import TERM_TYPE
from utils.parse import Parser

def build_def_dict(node, def_dict):
  node_type = get_node_type(node)

  if node_type in ['ClassExpression', 'FunctionExpression']:
    return

  if (node_type in ['FunctionDeclaration', 'ClassDeclaration'] and
      node['id'] != None and
      node['id']['type'] == 'Identifier'):
    func_name = node['id']['name']
    def_dict.add(func_name)
    return
  elif (node_type == 'VariableDeclarator' and
        'type' in node['id'] and
        node['id']['type'] == 'Identifier'):
    var_name = node['id']['name']
    def_dict.add(var_name)
  elif (node_type == 'AssignmentExpression' and
        'type' in node['left'] and
        node['left']['type'] == 'Identifier'):
    var_name = node['left']['name']
    def_dict.add(var_name)

  for key in PROP_DICT[node_type]:
    if key not in node: continue
    child = node[key]

    if (is_single_node(child) and
        child['type'] not in TERM_TYPE):
      build_def_dict(child, def_dict)
    elif is_node_list(child):
      for _child in child:
        if _child != None:
          build_def_dict(_child, def_dict)

def build_dict(ast_dir):
  def_dict = {}
  ast_list = list_dir(ast_dir)
  num_ast = len(ast_list)
  for idx, ast_name in enumerate(ast_list):
    msg = '[%d/%d] %s' % (idx + 1, num_ast, ast_name)
    print_msg(msg, 'INFO')
    js_name, ast = load_ast(ast_name)
    js_name = trim_seed_name(js_name)
    if js_name not in def_dict:
      def_dict[js_name] = set()
    build_def_dict(ast, def_dict[js_name])
  return def_dict

def build_id_map(conf):
  print_msg('[1/2] Building def dictionary')
  ast_dir = parse_seed(conf)
  def_dict = build_dict(ast_dir)

  print_msg('[2/2] Building ID map')
  id_harness_map = construct_map(conf, def_dict)

  write_map(id_harness_map)

def construct_map(conf, def_dict):
  no_err_path = os.path.join(conf.data_dir, 'seed')
  no_err_list = os.listdir(no_err_path)

  harness = Harness(conf.seed_dir)
  harness_keys = harness.get_keys()
  num_files = len(harness_keys)

  id_harness_map = {}
  for idx, file_name in enumerate(harness_keys):
    msg = '[%d/%d] %s' % (idx + 1, num_files, file_name)
    print_msg(msg, 'INFO')

    if file_name not in no_err_list: continue
    for harness_file in harness.get_list(file_name):
      if harness_file not in def_dict: continue
      for def_name in def_dict[harness_file]:
        if (file_name in def_dict and
            def_name in def_dict[file_name]):
          continue

        if def_name not in id_harness_map:
          id_harness_map[def_name] = set()
        id_harness_map[def_name].add(harness_file)
  return id_harness_map

def parse_seed(conf):
  parser = Parser()
  seed_dir = os.path.join(conf.data_dir, 'seed')
  ast_dir = os.path.join(conf.data_dir, 'ast_all')
  make_dir(ast_dir)
  parser.parse(seed_dir, ast_dir)
  return ast_dir

def write_map(id_harness_map):
  for key in id_harness_map:
    id_harness_map[key] = list(id_harness_map[key])

  map_path = 'fuzz/id_map.py'
  content = 'ID_HARNESS_MAP = {}'.format(id_harness_map)
  write(map_path, content, 'w')
