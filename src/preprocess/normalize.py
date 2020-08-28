from utils import get_node_type
from utils import is_node_list
from utils import is_single_node
from utils import list_dir
from utils import load_ast
from utils import pool_map
from utils import write_ast
from utils.logger import print_msg
from utils.node import PROP_DICT

def add_id(org_id, id_dict, id_cnt, id_type):
  if org_id not in id_dict:
    id_idx = id_cnt[id_type]
    id_cnt[id_type] = id_idx + 1
    norm_id = '%s%d' % (id_type, id_idx)
    id_dict[org_id] = norm_id

def collect_id(node, id_dict, id_cnt, parent=None, prop=None):
  node_type = get_node_type(node)

  # Tree traversal
  for key in PROP_DICT[node_type]:
    if key not in node: continue
    child = node[key]

    if is_single_node(child):
      collect_id(child, id_dict, id_cnt, node, key)
    elif is_node_list(child):
      for _child in child:
        if _child is not None:
          collect_id(_child, id_dict, id_cnt, node, key)

  if parent is not None and is_func_decl(parent):
    id_type = 'f'
  else:
    id_type = 'v'

  if is_declared_id(node, parent, prop):
    id_name = node['name']
    add_id(id_name, id_dict, id_cnt, id_type)

def is_declared_id(node, parent, prop):
  node_type = get_node_type(node)
  if node_type != 'Identifier': return False

  parent_type = get_node_type(parent)
  # var, const, let, func
  if parent_type in ['VariableDeclarator', 'FunctionDeclaration']:
    return prop == 'id'
  # Assignment Expression
  elif parent_type == 'AssignmentExpression':
    return prop == 'left'

  return False

def is_func_decl(node):
  node_type = get_node_type(node)
  return node_type == 'FunctionDeclaration'

def main(pool, conf):
  ast_list = list_dir(conf.ast_dir)
  pool_map(pool, normalize, ast_list)

def normalize(ast_path):
  try:
    js_name, ast = load_ast(ast_path)
  except Exception as e:
    print_msg(str(e), 'WARN')
    return

  id_dict = {}
  id_cnt = {
    'v': 0,
    'f': 0
  }
  collect_id(ast, id_dict, id_cnt)
  normalize_id(ast, id_dict)
  write_ast(ast_path, ast)

def normalize_id(node, id_dict, parent=None, prop=None):
  node_type = get_node_type(node)
  if node_type == 'ObjectPattern': return

  for key in PROP_DICT[node_type]:
    if key not in node: continue
    child = node[key]

    # Traversal
    if is_single_node(child):
      normalize_id(child, id_dict, node, key)
    elif is_node_list(child):
      for _child in child:
        if _child is not None:
          normalize_id(_child, id_dict, node, key)

  # Exit if the node is not an ID
  if node_type != 'Identifier': return

  # Exit if the node is a property of an object
  if (parent['type'] == 'MemberExpression' and
      prop != 'object' and
      parent['computed'] == False):
    return

  # Do not normalize keys (ObjectExpression)
  if (parent['type'] == 'Property' and
      prop == 'key'):
    return

  # Replace the ID
  id_name = node['name']
  if id_name in id_dict:
    node['name'] = id_dict[id_name]
