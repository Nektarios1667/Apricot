DIRECT = {r'(switch ([^:]+):)': 'match \x1a:1:', r'(this\.(\w+))': 'self.\x1a:1', r'(throw (\w+);)': 'raise \x1a:1', r'(catch( +.+)?:)': 'except \x1a:1:',
          r'(import (.*);)'   : 'globals().update(load(".libraries/\x1a:1.apl"))', r'(include (\w+);)': 'import \x1a:1',
          r'(using (.*):)'    : 'with \x1a:1:', r'(span\((.*)\))': 'range(\x1a:1)', r'(@(\w[\w _0-9]*))\b': "Pointer('\x1a:1', globals())", r'(\^([a-zA-Z_]\w*))': '\x1a:1.val',
          r'(noop;())'        : 'pass', r'(\((.+)\.\.(.+)\.\.(.+)\))': 'range(\x1a:1, \x1a:2, \x1a:3)', r'(\((.+)\.\.(.+)\))': 'range(\x1a:1, \x1a:2)', r'((def +\w+)\(this)': '\x1a:1(self',
          ' +&& +': ' and ', ' +\|\| +': ' +or +', '!([^=])': 'not \x1a:1'}
SYNTAX = [*DIRECT.values(), r'__init__([^)]*)', r'lambda \w+: ', r'nonlocal \w+', 'async ', 'await ', 'from .* import .*', 'for .* in .*:', '->', r'range(\d+, *\d+(?:, *\d+))', r'''f('|").*?\1''']
NAMEERRORS = [r'globals\(\)', r'locals\(\)']
SYNTAXPHRASES = [r'func +\w+ +\w+\(self', 'f=\d+']
DIRECTPHRASES = {'else if': 'elif', 'next;': 'continue', r'\btrue\b': 'True', r'\bfalse\b': 'False'}

STRINGS = r'''((["'])[^(?:\2)]+?\2)'''
INLINECOMMENTS = r'''.*//.*$'''
COMMENTS = r'''//.*'''
FORMATTEDSTRINGS = r'''$='''
CLASSNAMES = r'''class +(\w+) *(?:inherits)? *(?:[_a-zA-Z][\w_]*)* *:'''
CLASSES = r'''class +(\w+) *(?:inherits)? *([_a-zA-Z][\w_]*)* *:'''
CLASSBLOCKS = r'''class\s+\w+(?:\([^)]*\))?: *\n(?:[ \t]+.*\n*)*'''
METHODS = r'''(( *)func +([a-zA-Z_]\w*) +([a-zA-Z][a-zA-Z0-9_]*)\(([^)]*)\):)'''
WRONGCASTS = r'''((int|float|str|bool|list|tuple|dict|object)\([^)]*\))'''
CASTING = r'''(< *([a-zA-Z_]\w*) +([^>]*) *>)'''
WRONGINITSRETURNS = r'''(class (\w+)(\([^)]*\))?:\n+([\t ]*)func +([a-zA-Z_]\w*) +\2\(([^)]*)\) *:)'''
INITS = r'''(([\t ]*)class (\w+)(\([^)]*\))?:([\s\S]*?)func \3\(([^)]*)\) *:)'''
CONSTS = r'''(const: *([a-zA-Z_][\w_]*) *= *([^;]*);?)'''
ATTRIBUTES = r'''(([a-zA-Z_]\w*): *this\.(\w+) *= *([^;]+))'''
PLAINATTRIBUTES = r'''(this\.(\w+) *= *([^;]+))'''
VARS = r'''(([a-zA-Z_]\w*): *(\w+) *= *([^;]+))'''
PLAINVARS = r'''((?<!this\.|....\S)(\w+) *= *([^;]+))'''
PARAMETERS = r'''[(,] *(([a-zA-Z_]\w*) *: *([a-zA-Z_]\w*))'''
CLASSFUNC = r'''^[ \t]*func|class'''
CALLS = r'''(([a-zA-Z_]\w*\.)?([a-zA-Z_]\w*)\(([^()]+)\))'''
SIMPLEFUNCS = r'''func +([a-zA-Z_]\w*) +\w+'''
RETURNS = r'''return +([^;]+);'''
FUNCS = r'''(( *)func +([a-zA-Z_]\w*) +([a-zA-Z][a-zA-Z0-9_]*)\(([^)]*)\):)'''
WRONGINITS = r'''(class +(\w+)(\([^)]*\))?:\n[\t ]*func __init__(\([^)]*\)):)'''
TYPEPREDICATES = r'''(type +([a-zA-Z_]\w*) *:)'''
CONSTRUCTOR = r'''(class +(\w+)(\([^)]*\))?:\n+([\t ]*)def +\2\(([^)]*)\) *-> *([a-zA-Z_]\w*) *:)'''
