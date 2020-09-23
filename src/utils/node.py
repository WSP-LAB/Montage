import os

EVAL_LIST = [
  'assertAsmDirectiveFail',
  'eval',
  'evalAndLog',
  'evalAndLogResult',
  'evalInFrame',
  'completesNormally',
  'raisesException',
  'returns',
  'returnsCopyOf',
  'shouldNotBe',
  'shouldBe',
  'shouldBeDefined',
  'shouldBeEqualToString',
  'shouldBeFalse',
  'shouldBeNaN',
  'shouldBeNull',
  'shouldBeSyntaxError',
  'shouldBeTrue',
  'shouldBeType',
  'shouldBeUndefined',
  'shouldNotBeSyntaxError',
  'shouldNotThrow',
  'shouldThrow',
]

PROP_DICT = {
  'ArrayPattern': ['type', 'elements'],
  'RestElement': ['type', 'argument'],
  'AssignmentPattern': ['type', 'left', 'right'],
  'ObjectPattern': ['type', 'properties'],
  'ThisExpression': ['type'],
  'Identifier': ['type', 'name'],
  # regex might not be a child for string literals
  'Literal': ['type', 'value', 'raw', 'regex'] ,
  'ArrayExpression': ['type', 'elements'],
  'ObjectExpression': ['type', 'properties'],
  'Property': ['type', 'key', 'computed', 'value', 'kind', 'method', 'shorthand'],
  'FunctionExpression': ['type', 'id', 'params', 'body', 'generator', 'async', 'expression'],
  'ArrowFunctionExpression': ['type', 'id', 'params', 'body', 'generator', 'async', 'expression'],
  'ClassExpression': ['type', 'id', 'superClass', 'body'],
  'ClassBody': ['type', 'body'],
  'MethodDefinition': ['type', 'key', 'computed', 'value', 'kind', 'static'],
  'TaggedTemplateExpression': ['type', 'tag', 'quasi'],
  'TemplateElement': ['type', 'value', 'tail'],
  'TemplateLiteral': ['type', 'quasis', 'expressions'],
  'MemberExpression': ['type', 'computed', 'object', 'property'],
  'Super': ['type'],
  'MetaProperty': ['type', 'meta', 'property'],
  'CallExpression': ['type', 'callee', 'arguments'],
  'NewExpression': ['type', 'callee', 'arguments'],
  'Import': ['type'],
  'SpreadElement': ['type', 'argument'],
  'UpdateExpression': ['type', 'operator', 'argument', 'prefix'],
  'AwaitExpression': ['type', 'argument'],
  'UnaryExpression': ['type', 'operator', 'argument', 'prefix'],
  'BinaryExpression': ['type', 'operator', 'left', 'right'],
  'LogicalExpression': ['type', 'operator', 'left', 'right'],
  # alternate might not be a child of ConditionalExpression
  'ConditionalExpression': ['type', 'test', 'consequent', 'alternate'],
  'YieldExpression': ['type', 'argument', 'delegate'],
  'AssignmentExpression': ['type', 'operator', 'left', 'right'],
  'SequenceExpression': ['type', 'expressions'],
  'BlockStatement': ['type', 'body'],
  'BreakStatement': ['type', 'label'],
  'ClassDeclaration': ['type', 'id', 'superClass', 'body'],
  'ContinueStatement': ['type', 'label'],
  'DebuggerStatement': ['type'],
  'DoWhileStatement': ['type', 'body', 'test'],
  'EmptyStatement': ['type'],
  # directive might not be a child of ExpressionStatement
  'ExpressionStatement': ['type', 'expression', 'directive'],
  'ForStatement': ['type', 'init', 'test', 'update', 'body'],
  'ForInStatement': ['type', 'left', 'right', 'body', 'each'],
  'ForOfStatement': ['type', 'left', 'right', 'body'],
  'FunctionDeclaration': ['type', 'id', 'params', 'body', 'generator', 'async', 'expression'],
  # alternate might not be a child of IfStatement
  'IfStatement': ['type', 'test', 'consequent', 'alternate'],
  'LabeledStatement': ['type', 'label', 'body'],
  'ReturnStatement': ['type', 'argument'],
  'SwitchStatement': ['type', 'discriminant', 'cases'],
  'SwitchCase': ['type', 'test', 'consequent'],
  'ThrowStatement': ['type', 'argument'],
  'TryStatement': ['type', 'block', 'handler', 'finalizer'],
  'CatchClause': ['type', 'param', 'body'],
  'VariableDeclaration': ['type', 'declarations', 'kind'],
  'VariableDeclarator': ['type', 'id', 'init'],
  'WhileStatement': ['type', 'test', 'body'],
  'WithStatement': ['type', 'object', 'body'],
  'Program': ['type', 'sourceType', 'body'],
  'ImportDeclaration': ['type', 'specifiers', 'source'],
  # imported might not be a child of ImportSpecifier
  'ImportSpecifier': ['type', 'local', 'imported'],
  'ExportAllDeclaration': ['type', 'source'],
  'ExportDefaultDeclaration': ['type', 'declaration'],
  'ExportNamedDeclaration': ['type', 'declaration', 'specifiers', 'source'],
  'ExportSpecifier': ['type', 'exported', 'local'],
}

TERM_TYPE = [
  'DebuggerStatement',
  'ThisExpression',
  'Super',
  'EmptyStatement',
  'Import',
]

def get_define_node(seed_dir):
  node = {
    'type': 'IfStatement',
    'test': {
      'type': 'BinaryExpression',
      'operator': '==',
      'left': {
        'type': 'UnaryExpression',
        'operator': 'typeof',
        'argument': {
          'type': 'Identifier',
          'name': 'load'
        },
        'prefix': True
      },
      'right': {
        'type': 'Literal',
        'value': 'undefined',
        'raw': '"undefined"'
      }
    },
    'consequent': {
      'type': 'ExpressionStatement',
      'expression': {
        'type': 'AssignmentExpression',
        'operator': '=',
        'left': {
          'type': 'Identifier',
          'name': 'load'
        },
        'right': {
          'type': 'FunctionExpression',
          'id': None,
          'params':[
            {
              'type': 'Identifier',
              'name': 'js_path'
            }
          ],
          'body': {
            'type': 'BlockStatement',
            'body': [
              {
                'type': 'ExpressionStatement',
                'expression': {
                  'type': 'CallExpression',
                  'callee': {
                    'type': 'MemberExpression',
                    'computed': False,
                    'object': {
                      'type': 'Identifier',
                      'name': 'WScript'
                    },
                    'property': {
                      'type': 'Identifier',
                      'name': 'LoadScriptFile'
                    }
                  },
                  'arguments': [
                    {
                      'type': 'CallExpression',
                      'callee': {
                        'type': 'MemberExpression',
                        'computed': False,
                        'object': {
                          'type': 'Literal',
                          'value': seed_dir + '/',
                          'raw': '"' + seed_dir + '/"'
                        },
                        'property': {
                          'type': 'Identifier',
                          'name': 'concat'
                        }
                      },
                      'arguments': [
                        {
                          'type': 'Identifier',
                          'name': 'js_path'
                        }
                      ]
                    }
                  ]
                }
              }
            ]
          },
          'generator': False,
          'expression': False,
          'async': False
        }
      }
    },
    'alternate': None
  }
  return node

def get_load_node(script_path):
  node = {
    'type': 'ExpressionStatement',
    'expression': {
      'type': 'CallExpression',
      'callee': {
        'type': 'Identifier',
        'name': 'load'
      },
      'arguments': [
        {
          'type': 'Literal',
          'value': script_path,
          'raw': '"' + script_path + '"'
        }
      ]
    }
  }
  return node
