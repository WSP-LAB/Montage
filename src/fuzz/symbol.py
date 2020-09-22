from enum import Enum

from fuzz.resolve_bug import error

class JSType(Enum):
  unknown = 0
  undefined = 1
  js_bool = 2
  js_null = 3
  js_number = 4
  js_string = 5
  js_regex = 6
  js_array = 7
  js_object = 8
  js_func = 9

class Symbol:
  def __init__(self, identifier, expr, ty = None):
    if ('type' in identifier and
        identifier['type'] == 'Identifier'):
      self.symbol = identifier['name']
    else:
      self.symbol = identifier
    if type(self.symbol) not in [str, bytes]:
      error('self.symbol is not string')

    if ty == None:
      self.ty = to_jstype(expr)
    else:
      self.ty = ty
    self.expr = expr
    self.flag = True

  def update_type(self, ty):
    self.ty = ty

  def get_type(self):
    return self.ty

  def set_flag(self, flag):
    self.flag = flag

  def get_flag(self):
    return self.flag

  def __str__(self):
    ret = '%s: %s'%(self.symbol, self.ty)
    return ret

def to_jstype(expr):
  if expr['type'] == 'VariableDeclarator':
    return JSType.undefined
  elif expr['type'] == 'FunctionDeclaration':
    return JSType.js_func
  return JSType.unknown

