DIRECT = {r'(switch ([^:]+):)': 'match \x1a:1:', r'(this\.(\w+))': 'self.\x1a:1', r'(throw (\w+);)': 'raise \x1a:1', r'(catch( +.+)?:)': 'except \x1a:1:',
          r'(import (.*);)'   : 'globals().update(load(".libraries/\x1a:1.apl"))', r'(include (\w+);)': 'import \x1a:1',
          r'(using (.*):)'    : 'with \x1a:1:', r'(span\((.*)\))': 'range(\x1a:1)', r'(@(\w[\w _0-9]*))\b': "Pointer('\x1a:1', globals())", r'(\^([a-zA-Z_]\w*))': '\x1a:1.val',
          r'(noop;())'        : 'pass', r'(\((.+)\.\.(.+)\.\.(.+)\))': 'range(\x1a:1, \x1a:2, \x1a:3)', r'(\((.+)\.\.(.+)\))': 'range(\x1a:1, \x1a:2)', r'((def +\w+)\(this)': '\x1a:1(self'}
SYNTAX = [*DIRECT.values(), r'__init__([^)]*)', r'lambda \w+: ', r'nonlocal \w+', 'async ', 'await ', 'from .* import .*', 'for .* in .*:', '->', r'range(\d+, *\d+(?:, *\d+))']
NAMEERRORS = [r'globals\(\)', r'locals\(\)']
SYNTAXPHRASES = [r'func +\w+ +\w+\(self']
DIRECTPHRASES = {'else if': 'elif', 'next;': 'continue', r'\btrue\b': 'True', r'\bfalse\b': 'False'}


STRINGS = r'''((["'])[^(?:\2)]+\2)'''
INLINECOMMENTS = r'''.*//.*$'''
COMMENTS = r'''^//.*'''
CLASSNAMES = r'''class (\w+) *(?:inherits)? *(?:[_a-zA-Z][\w_]*)* *:'''
CLASSES = r'''class (\w+) *(?:inherits)? *([_a-zA-Z][\w_]*)* *:'''
CLASSBLOCKS = r'''class\s+\w+(?:\([^)]*\))?: *\n(?:[ \t]+.*\n*)*'''
WRONGCASTS = r'''((int|float|str|bool|list|tuple|dict|object)\([^)]*\))'''
INITS = r'''(([\t ]*)class (\w+)(\([^)]*\))?:([\s\S]*?)func \3\(([^)]*)\) *:)'''
CONSTS = r'''(const: *([a-zA-Z_][\w_]*) *= *(.*);)'''
PLAINVARS = r'''((?<!this\.|....\S)(\w+) *= *([^;]+))'''
PARAMETERS = r'''[(,] *(([a-zA-Z_]\w*) *: *([a-zA-Z_]\w*))'''
CLASSFUNC = r'''^[ \t]*func|class'''
CALLS = r'''(([a-zA-Z_]\w*\.)?([a-zA-Z_]\w*)\(([^()]+)\))'''
RETURNS = r'''return +([^;]+);'''
WRONGINITS = r'''(class (\w+)(\([^)]*\))?:\n[\t ]*func __init__(\([^)]*\)):)'''
