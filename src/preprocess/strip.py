import json
import os
import shutil

from copy import deepcopy

from utils import get_node_type
from utils import hash_val
from utils import is_node_list
from utils import is_single_node
from utils import list_dir
from utils import load_ast
from utils import make_tmp_dir
from utils import pool_map
from utils import write
from utils import write_ast
from utils.logger import print_msg
from utils.node import EVAL_LIST
from utils.node import PROP_DICT
from utils.parse import SingleParser

class Stripper:
  def __init__(self, conf):
    self._ast_dir = conf.ast_dir
    self._tmp_dir = conf.tmp_dir

  def append(self, child, subtree, idx):
    return child[:idx] + subtree + child[idx+1:]

  def is_eval(self, node):
    node_type = get_node_type(node)
    if node_type != 'ExpressionStatement': return False

    node_type = get_node_type(node['expression'])
    if node_type != 'CallExpression': return False

    node_type = get_node_type(node['expression']['callee'])
    if node_type != 'Identifier': return False

    return node['expression']['callee']['name'] in EVAL_LIST

  def is_string(self, node):
    node_type = get_node_type(node)
    if node_type != 'Literal': return False

    if (node['raw'].startswith('"') or
        node['raw'].startswith('\'')):
      return True
    else:
      return False

  def parse_arg(self, code, parser):
    tmp_dir = make_tmp_dir(self._tmp_dir)
    js_path = hash_val(code) + '.js'
    js_path = os.path.join(tmp_dir, js_path)
    write(js_path, code)
    ast_path = parser.parse(js_path)
    return tmp_dir, ast_path

  def rewrite(self, node, parser):
    node_type = get_node_type(node)
    if self.is_eval(node):
      # Parse arguments and retrieve new subtrees
      args = node['expression']['arguments']
      org_args = deepcopy(args)
      new_args = self.str2code(args, parser)
      if org_args != new_args:
        return new_args
      else:
        return

    # Recursive traversal
    for key in PROP_DICT[node_type]:
      if key not in node: continue
      child = node[key]

      if is_single_node(child):
        self.rewrite(child, parser)
      elif is_node_list(child):
        child_idx = 0
        for _child in child:
          if _child is not None:
            subtree = self.rewrite(_child, parser)
            if subtree is not None:
              node[key] = self.append(node[key], subtree, child_idx)
              child_idx += len(subtree) - 1
          child_idx += 1

  def rewrite_ast(self, ast, ast_path):
    file_name = os.path.basename(ast_path)
    idx = file_name.rfind('.')
    file_name = file_name[:idx] + '_aug.json'
    ast_path = os.path.join(self._ast_dir, file_name)
    write_ast(ast_path, ast)
    return ast_path

  def strip(self, ast_path):
    parser = SingleParser()
    try:
      _, ast = load_ast(ast_path)
      org_ast = deepcopy(ast)
    except Exception as e:
      print_msg(str(e), 'WARN')
      return

    self.rewrite(ast, parser)
    if org_ast != ast:
      ast_path = self.rewrite_ast(ast, ast_path)

  def str2code(self, args, parser):
    subtree = []
    for arg in args:
      if self.is_string(arg):
        code = arg['value'].encode('utf-8')
        tmp_dir, ast_path = self.parse_arg(code, parser)

        # Append the node
        if os.path.exists(ast_path):
          _, ast = load_ast(ast_path)
          for node in ast['body']:
            subtree += [node]
        shutil.rmtree(tmp_dir)
      else:
        subtree += [arg]
    return subtree

def main(pool, conf):
  ast_list = list_dir(conf.ast_dir)
  ast_list = pool_map(pool, strip, ast_list,
                      conf=conf)

def strip(ast_path, conf):
  stripper = Stripper(conf)
  stripper.strip(ast_path)
