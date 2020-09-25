from subprocess import PIPE
from subprocess import Popen

from fuzz.symbol import JSType
from fuzz.symbol import Symbol

BUILTINS = {
  'Infinity': JSType.js_number,
  'NaN': JSType.js_number,
  'undefined': JSType.undefined,
  'null' : JSType.js_null,
}

BUILTIN_ARRAYS = [
  'Array',
  'Int8Array',
  'Uint8Array',
  'Uint8ClampedArray',
  'Int16Array',
  'Uint16Array',
  'Int32Array',
  'Uint32Array',
  'Float32Array',
  'Float64Array',
]

BUILTIN_FUNCS = [
  'eval',
  'uneval',
  'isFinite',
  'isNaN',
  'parseFloat',
  'parseInt',
  'decodeURI',
  'decodeURIComponent',
  'encodeURI',
  'encodeURIComponent',
  'escape',
  'unescape',
]

BUILTIN_OBJS = [
  'Object',
  'Function',
  'Boolean',
  'Symbol',
  'Error',
  'EvalError',
  'InternalError',
  'RangeError',
  'ReferenceError',
  'SyntaxError',
  'TypeError',
  'URIError',
  'Number',
  'Math',
  'Date',
  'String',
  'RegExp',
  'Map',
  'Set',
  'WeakMap',
  'WeakSet',
  'ArrayBuffer',
  'SharedArrayBuffer',
  'Atomics',
  'DataView',
  'JSON',
  'Promise',
  'Reflect',
  'Proxy',
  'Intl',
  'WebAssembly',
  'WScript',
  '__defineGetter__',
  '__defineSetter__',
]

class BuiltIn:
  def __init__(self):
    self.ARRAYS  = BUILTIN_ARRAYS
    self.BUILTINS = BUILTINS
    self.FUNCS = BUILTIN_FUNCS
    self.OBJS = BUILTIN_OBJS
    self.SYMS = []

  def get_props(self, eng_path):
    array_props = exec_eng(eng_path, 'utils/array_getter.js')
    self.array_props = self.process_out(array_props)

    func_props = exec_eng(eng_path, 'utils/func_getter.js')
    self.func_props = self.process_out(func_props)

    obj_props = exec_eng(eng_path, 'utils/obj_getter.js')
    self.obj_props = self.process_out(obj_props)

    regex_props = exec_eng(eng_path, 'utils/regex_getter.js')
    self.regex_props = self.process_out(regex_props)

    str_props = exec_eng(eng_path, 'utils/str_getter.js')
    self.str_props = self.process_out(str_props)

  def build_resolve_pattern(self, eng_path):
    self.get_props(eng_path)
    self.resolve_pattern = {}
    for props, ty in [
      (self.array_props, JSType.js_array),
      (self.str_props, JSType.js_string),
      (self.regex_props, JSType.js_regex),
      (self.func_props, JSType.js_func),
    ]:
      for x in props:
        if x not in self.obj_props:
          if x not in self.resolve_pattern:
            self.resolve_pattern[x] = []
          self.resolve_pattern[x] += [ty]

  def process_out(self, stdout):
    stdout = stdout.decode('utf-8')
    stdout = stdout.split()
    stdout = list(set(stdout))
    return stdout

  def update_builtins(self, eng_path):
    globs = exec_eng(eng_path, 'utils/global_getter.js')
    globs = self.process_out(globs)
    self.OBJS = [x for x in self.OBJS if x in globs]
    self.FUNCS = [x for x in self.FUNCS if x in globs]

    for x in self.OBJS + self.ARRAYS:
      self.BUILTINS[x] = JSType.js_object
    for x in self.FUNCS:
      self.BUILTINS[x] = JSType.js_func

    for sym, ty in self.BUILTINS.items():
      self.SYMS.append(Symbol(sym, None, ty))

def exec_eng(eng_path, js_path):
  cmd = [eng_path, js_path]
  proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
  stdout, _ = proc.communicate()
  return stdout
