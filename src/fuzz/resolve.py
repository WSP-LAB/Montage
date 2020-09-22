import random

from fuzz.builtin import BuiltIn
from fuzz.id_map import ID_HARNESS_MAP
from fuzz.resolve_bug import error
from fuzz.symbol import JSType
from fuzz.symbol import Symbol
from utils.node import PROP_DICT
from utils.node import TERM_TYPE

builtin = BuiltIn()

def update_builtins(eng_path):
  builtin.update_builtins(eng_path)
  builtin.build_resolve_pattern(eng_path)

def init_symbols():
  return [], []

def hoisting(node, symbols, is_global):
  global_var, local_var = symbols
  if is_global : sym_list = global_var
  else : sym_list = local_var
  var_hoisting(node, None, sym_list)
  func_hoisting(node, sym_list)
  return global_var, local_var

def pattern_hoisting(pattern, node):
  if pattern == None: return []
  pattern_type = pattern['type']
  if pattern_type == 'Identifier':
    return [Symbol(pattern, node, JSType.undefined)]
  elif pattern_type == 'ArrayPattern':
    ret = []
    for item in pattern['elements']:
      ret += pattern_hoisting(item, pattern)
    return ret
  elif pattern_type == 'ObjectPattern':
    ret = []
    for prop in pattern['properties']:
      ret += pattern_hoisting(prop, pattern)
    return ret
  elif pattern_type == 'AssignmentPattern':
    return pattern_hoisting(pattern['left'], pattern)
  elif pattern_type == 'Property':
    return pattern_hoisting(pattern['value'], pattern)
  elif pattern_type == 'RestElement':
    return pattern_hoisting(pattern['argument'], pattern)
  else:
    error('pattern_hoisting: %s %s'%(pattern['type'], node['type']))
  return []

def var_hoisting(node, parent, sym_list):
  node_type = node['type']
  if node_type in ['FunctionDeclaration', 'FunctionExpression',
                   'ClassDeclaration', 'ClassExpression']:
    return
  elif parent != None and \
       parent['type'] == 'VariableDeclaration' and \
       parent['kind'] == 'var' and \
       node_type == 'VariableDeclarator':
    symbols = pattern_hoisting(node['id'], node)
    sym_list += symbols
  else:
    for key in PROP_DICT[node_type]:
      if key not in node:
        continue
      child = node[key]

      if type(child) == dict and \
         'type' in child and \
         child['type'] not in TERM_TYPE:
        var_hoisting(child, node, sym_list)
      elif type(child) == list:
        for _child in child:
          if _child != None:
            var_hoisting(_child, node, sym_list)

def func_hoisting(node, sym_list):
  if node == None: return

  node_type = node['type']
  for key in PROP_DICT[node_type]:
    if key not in node:
      continue
    child = node[key]

    if type(child) == dict and 'type' in child:
      if child['type'] == 'FunctionDeclaration':
        sym_list.append(Symbol(child['id'], child, JSType.js_func))
      elif child['type'] == 'BlockStatement':
        func_hoisting(child, sym_list)
    elif type(child) == list:
      for _child in child:
        if _child == None: continue
        if _child['type'] == 'FunctionDeclaration':
          sym_list.append(Symbol(_child['id'], _child, JSType.js_func))
        elif _child['type'] == 'BlockStatement':
          func_hoisting(_child, sym_list)

def resolve_id(node, parent, symbols, is_global, is_check = False, cand = [],
               hlist = []):
  if node == None : return symbols

  node_type = node['type']
  if node_type == 'Identifier':
    return resolve_identifier(node, parent, symbols, is_global, is_check, cand,
                              hlist)
  elif node_type == 'MemberExpression' and node['computed'] == False:
    return resolve_id(node['object'], node, symbols, is_global, is_check, cand,
                      hlist)
  elif node_type == 'CallExpression':
    return resolve_FuncCall(node, parent, symbols, is_global, is_check, cand,
                            hlist)
  elif node_type == 'AssignmentExpression' :
    return resolve_Assign(node, parent, symbols, is_global, is_check, cand,
                          hlist)
  elif node_type == 'VariableDeclarator':
    return resolve_VarDecl(node, parent, symbols, is_global, is_check, cand,
                           hlist)
  elif node_type in ['FunctionDeclaration', 'FunctionExpression']:
    return symbols
  elif node_type == 'IfStatement':
    return resolve_If(node, parent, symbols, is_global, is_check, cand, hlist)
  elif node_type in ['DoWhileStatement', 'WhileStatement']:
    return resolve_While(node, parent, symbols, is_global, is_check, cand,
                         hlist)
  elif node_type == 'ForStatement':
    return resolve_For(node, parent, symbols, is_global, is_check, cand, hlist)
  elif node_type in ['ForInStatement', 'ForOfStatement']:
    return resolve_ForIn(node, parent, symbols, is_global, is_check, cand,
                         hlist)
  elif node_type == 'WithStatment':
    return resolve_With(node, parent, symbols, is_global, is_check, cand,
                        hlist)
  elif node_type == 'TryStatement':
    return resolve_Try(node, parent, symbols, is_global, is_check, cand, hlist)
  elif node_type == 'Property':
    return resolve_id(node['value'], node, symbols, is_global, is_check, cand,
                      hlist)
  elif node_type in ['ClassDeclaration', 'ClassExpression']:
    return resolve_ClassDecl(node, parent, symbols, is_global, is_check, cand,
                             hlist)

  # Switch
  for key in PROP_DICT[node_type]:
    if key not in node:
      continue
    child = node[key]

    if type(child) == dict and \
       'type' in child and \
       child['type'] not in TERM_TYPE:
      resolve_id(child, node, symbols, is_global, is_check, cand, hlist)
    elif type(child) == list:
      resolve_list(child, node, symbols, is_global, is_check, cand, hlist)
  return symbols

def resolve_list(nodes, parent, symbols, is_global, is_check, cand, hlist):
  g, l = symbols
  if nodes != None:
    for x in nodes:
      g, l = resolve_id(x, parent, (g, l), is_global, is_check, cand, hlist)
  return g, l

def resolve_identifier(node, parent, symbols, is_global, is_check, cand, hlist):
  name = node['name']
  if name in ID_HARNESS_MAP and name not in builtin.BUILTINS:
    if not is_duplicate(hlist, name):
      fname = pick_one(ID_HARNESS_MAP[name])
      hlist.append(fname)
    return symbols
  if name in builtin.BUILTINS:
    return symbols
  if find_symbol(node, symbols) == None :
    types = infer_id_types(node, parent)
    change_id(node, types, symbols, cand)
  return symbols

def resolve_ClassDecl(node, parent, symbols, is_global, is_check, cand, hlist):
  if node['id'] != None and node['id']['type'] == 'Identifier':
    if is_check : return symbols
    ty = JSType.js_object
    sym = Symbol(node['id'], None, ty)
    symbols[0].append(sym)
  return symbols

def resolve_FuncCall(node, parent, symbols, is_global, is_check, cand, hlist):
  global_var, local_var = symbols
  go_flag = True
  callee_type = node['callee']['type']
  if callee_type == 'Identifier':
    name = node['callee']['name']
    if name in ID_HARNESS_MAP:
      if not is_duplicate(hlist, name):
        fname = pick_one(ID_HARNESS_MAP[name])
        hlist.append(fname)
      expr = None
    elif name in builtin.FUNCS or name in builtin.OBJS or \
      name in builtin.ARRAYS:
      expr = None
    else:
      symbol = find_symbol(node['callee'], symbols)
      if symbol == None :
        symbol = change_id(node['callee'], [JSType.js_func], symbols, cand)
      expr = symbol.expr
      go_flag = symbol.get_flag()
      symbol.set_flag(False)
  elif callee_type in ['FunctionExpression', 'ArrowFunctionExpression']:
    expr = node['callee']
  elif callee_type in ['MemberExpression', 'CallExpression',
                       'SequenceExpression']:
    resolve_id(node['callee'], node, symbols, is_global, is_check, cand, hlist)
    expr = None
  elif callee_type == 'NewExpression':
    node['callee']['callee']['name'] = 'Function'
    return symbols
  elif callee_type == 'BlockStatement':
    resolve_list(node['body'], node, symbols, is_global, is_check, cand, hlist)
    expr = None
  else:
    error('resolve_id FunctionCall fail')
    expr = None
  resolve_list(node['arguments'], node, symbols, is_global, is_check, cand,
               hlist)
  if go_flag and expr != None and \
    'params' in expr and 'body' in expr :
    l1 = []
    for arg in expr['params'] :
      if arg['type'] == 'Identifier':
        l1.append(Symbol(arg, arg))
    l1.append(Symbol('arguments', None, JSType.js_array))
    symbols = global_var, l1
    symbols = hoisting(expr['body'], symbols, False)
    resolve_id(expr['body'], node, symbols, False, False, cand, hlist)
  return global_var, local_var

def resolve_Assign(node, parent, symbols, is_global, is_check, cand, hlist):
  symbols = resolve_id(node['right'], node, symbols, is_global, is_check, cand,
                       hlist)
  if node['operator'] != '=':
    symbols = resolve_id(node['left'], node, symbols, is_global, is_check,
                         cand, hlist)
  return help_Assign(node['left'], parent, node['right'], symbols, is_global,
                     False, is_check, cand, hlist)

def get_Array_item(array, idx):
  if array == None: return None
  if array['type'] == 'ArrayExpression' and len(array['elements']) > idx:
    return array['elements'][idx]
  return None

def get_Object_prop(obj, prop):
  if obj == None: return None
  if obj['type'] == 'ObjectExpression':
    props = obj['properties']
    for assign in props:
      if assign['key'] == prop:
        return assign['value']
  return None

def help_Assign(pattern, parent, init, symbols, is_global, is_VarDecl,
                is_check, cand, hlist):
  if pattern == None: return symbols

  pattern_type = pattern['type']
  if pattern_type == 'Identifier':
    if is_check : return symbols
    ty = get_type(init, symbols)
    if is_VarDecl:
      sym = find_symbol(pattern, symbols)
      if sym == None:
        error('help_VarDecl fail')
      sym.update_type(ty)
    else :
      sym = Symbol(pattern, None, ty)
      symbols[0].append(sym)
    return symbols
  elif pattern_type == 'ArrayPattern':
    items = pattern['elements']
    for idx in range(len(items)):
      item = items[idx]
      item_init = get_Array_item(init, idx)
      symbols = help_Assign(item, pattern, item_init, symbols, is_global,
                            is_VarDecl, is_check, cand, hlist)
    return symbols
  elif pattern_type == 'ObjectPattern':
    for prop in pattern['properties']:
      prop_init = get_Object_prop(init, prop['key'])
      symbols = help_Assign(prop['value'], pattern, prop_init, symbols,
                            is_global, is_VarDecl, is_check, cand, hlist)
    return symbols
  elif pattern_type == 'MemberExpression':
    return resolve_id(pattern, parent, symbols, is_global, is_check, cand,
                      hlist)
  elif pattern_type == 'AssignmentPattern':
    # TODO : Check
    return symbols
  else:
    error('Unknown branch in help assign')

  return symbols

def resolve_VarDecl(node, parent, symbols, is_global, is_check, cand, hlist):
  symbols = resolve_id(node['init'], node, symbols, is_global, True, cand,
                       hlist)
  return help_Assign(node['id'], parent, node['init'], symbols,
                     is_global, True, is_check, cand, hlist)

def resolve_If(node, parent, symbols, is_global, is_check, cand, hlist):
  global_var, local_var = symbols
  length = len(symbols[1])
  resolve_id(node['test'], node, symbols, is_global, is_check, cand, hlist)
  ret = ([], [])
  following = [node['consequent']]
  if 'alternate' in node:
    following.append(node['alternate'])
  for x in following:
    g1, l1 = global_var[::], local_var[::]
    func_hoisting(x, l1)
    g1, l1 = resolve_id(x, node, (g1, l1), is_global, is_check, cand, hlist)
    ret = merge_symbols(ret, (g1, l1[:length]))
  return ret

def resolve_While(node, parent, symbols, is_global, is_check, cand, hlist):
  length = len(symbols[1])
  symbols = resolve_id(node['test'], node, symbols, is_global, is_check, cand,
                       hlist)
  func_hoisting(node['body'], symbols[1])
  symbols = resolve_id(node['body'], node, symbols, is_global, is_check, cand,
                       hlist)
  return symbols[0], symbols[1][:length]

def resolve_For(node, parent, symbols, is_global, is_check, cand, hlist):
  length = len(symbols[1])
  bf = to_typedic(symbols)
  symbols = resolve_id(node['init'], node, symbols, is_global, is_check, cand,
                       hlist)
  af = to_typedic(symbols)
  cand += get_cand(af, bf)
  symbols = resolve_id(node['test'], node, symbols, is_global, is_check, cand,
                       hlist)
  func_hoisting(node['body'], symbols[1])
  symbols = resolve_id(node['body'], node, symbols, is_global, is_check, cand,
                       hlist)
  symbols = resolve_id(node['update'], node, symbols, is_global, is_check, cand,
                       hlist)
  return symbols[0], symbols[1][:length]

def resolve_ForIn(node, parent, symbols, is_global, is_check, cand, hlist):
  # TODO : let..
  global_var, local_var = symbols
  if node['left'] == 'Identifier':
    global_var.append(Symbol(node['left'], node))
  else:
    symbols = resolve_id(node['left'], node, symbols, is_global, is_check, cand,
                         hlist)
  symbols = resolve_id(node['right'], node, symbols, is_global, is_check, cand,
                       hlist)
  func_hoisting(node['body'], symbols[1])
  return resolve_id(node['body'], node, symbols, is_global, is_check, cand,
                    hlist)

def resolve_With(node, parent, symbols, is_global, is_check, cand, hlist):
  # TODO
  return symbols

def resolve_Try(node, parent, symbols, is_global, is_check, cand, hlist):
  global_var, local_var= symbols
  length = len(local_var)
  ret = ([], [])
  for x in [node['block'], node['handler'], node['finalizer']]:
    g1, l1 = global_var[::], local_var[::]
    func_hoisting(x, l1)
    if x != None and x == node['handler'] and \
       x['param']['type'] == 'Identifier':
      l1.append(Symbol(x['param'], None, JSType.js_object))
    g1, l1 = resolve_id(x, node, (g1,l1), is_global, is_check, cand, hlist)
    ret = merge_symbols(ret, (g1,l1[:length]))
  return symbols

def infer_id_types(node, parent):
  if parent['type'] == 'MemberExpression':
    if parent['property']['type'] == 'Identifier':
      name = parent['property']['name']
      if name in builtin.resolve_pattern:
        return builtin.resolve_pattern[name]
    return [JSType.js_object]
  return [JSType.unknown]

def find_symbol(identifier, symbols):
  name = identifier['name']
  if name == None : return None
  for sym_list in symbols:
    for var in sym_list[::-1]:
      if var.symbol == name : return var
  return None

def find_cand(types, symbols):
  cand = []
  if JSType.unknown in types:
    return symbols[0] + symbols[1]
  for sym_list in symbols:
    for var in sym_list:
      if var.ty in types or \
         var.ty in [JSType.unknown, JSType.undefined]:
        cand.append(var)
  return cand

def pick_one(cand):
  return random.choice(cand)

def change_id(node, types, symbols, cand0):
  for tys in [types, [JSType.js_object]]:
    for syms in [cand0, symbols, (builtin.SYMS, [])]:
      if len(syms) == 0 : continue
      cand = find_cand(tys, syms)
      if len(cand) > 0:
        nxt = pick_one(cand)
        if 'name' in node and hasattr(nxt, 'symbol') :
          node['name'] = nxt.symbol
        return nxt
  error('change_id fail')

def merge_symbols(s1, s2):
  g1, l1 = s1
  g2, l2 = s2
  ret = []
  for x,y in [(g1,g2), (l1,l2)]:
    tmp = []
    if x == [] : tmp = y
    elif y == [] : tmp = x
    elif x == y : tmp = x
    else:
      for a in x:
        if a not in y:
          y.append(a)
      tmp = y
    ret.append(tmp)
  return tuple(ret)

def to_typedic(symbols):
  g, l = symbols
  g_ret , l_ret = {}, {}
  for x in g:
    g_ret[x] = x.get_type()
  for x in l:
    l_ret[x] = x.get_type()
  return g_ret, l_ret

def get_cand(af, bf):
  ret = []
  ag, al = af
  bg, bl = bf
  for d1, d2 in [(ag, bg), (al, bl)]:
    tmp = []
    for x in d1:
      if x not in d2: tmp.append(x)
      elif d1[x] != d2[x] : tmp.append(x)
    ret.append(tmp)
  return ret

def get_type_newExpr(expr):
  if 'name' in expr['callee']:
    ty = expr['callee']['name']
    if ty in builtin.ARRAYS:
      return JSType.js_array
  return JSType.js_object

def get_type(expr, symbols):
  if expr == None: return JSType.unknown
  expr_type = expr['type']
  if expr_type == 'Literal' and type(expr['value']) == bool:
    return JSType.js_bool
  elif expr_type == 'Literal' and expr['value'] == None:
    return JSType.js_null
  elif expr_type == 'Literal' and type(expr['value']) in [int, float]:
    return JSType.js_number
  elif expr_type == 'Literal' and type(expr['value']) == str:
    return JSType.js_string
  elif expr_type == 'Literal' and 'regex' in expr:
    return JSType.js_regex
  elif expr_type == 'ArrayExpression':
    return JSType.js_array
  elif expr_type in ['ObjectExpression', 'ClassExpression']:
    return JSType.js_object
  elif expr_type == 'NewExpression':
    return get_type_newExpr(expr)
  elif expr_type == 'Identifier':
    sym = find_symbol(expr, symbols)
    if sym != None:
      return sym.get_type()
  return JSType.unknown

def is_duplicate(hlist, name):
  for fname in hlist:
    if fname in ID_HARNESS_MAP[name]:
      return True
  return False
