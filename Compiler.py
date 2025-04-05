import os
import re
import sys

import Cache
import Functions as F
from Library import Library
from Pointers import Pointer
from Text import ColorText as C


class Compiler:
    code = ''
    compiled = ''

    @staticmethod
    def error(error: str, l: int, line: str = '', description: str = '', extra: str = ''):
        # If line isn't specified
        line = line or F.getLine(l, Compiler.code)
    
        # Printing and closing
        if description:
            Compiler.log(f'{C.RED}{error}: "{line.strip()}" - "{description.strip()}" @ line {l}\n{extra}{C.RESET}' + "\n" if extra else "")
        else:
            Compiler.log(f'{C.RED}{error}: "{line.strip()}" @ line {l}\n{extra}{C.RESET}' + "\n" if extra else "")
        if '-w' in sys.argv:
            with open(sys.argv[sys.argv.index('-w') + 1], 'w') as f:
                f.write(Compiler.compiled)
    
        sys.exit(-1)

    @staticmethod
    def warn(warning: str, l: int, line: str = '', description: str = '', extra: str = ''):
        # If line isn't specified find automatically
        line = line or F.getLine(l, Compiler.code)
        # Printing
        if description:
            Compiler.log(f'{C.YELLOW}{warning}: "{line.strip()}" - "{description.strip()}" @ line {l}\n{extra}{C.RESET}' + "\n" if extra else "")
        else:
            Compiler.log(f'{C.YELLOW}{warning}: "{line.strip()}" @ line {l}\n{extra}{C.RESET}' + "\n" if extra else "")

        # Return back for logging
        return warning, l, line, description, extra

    @staticmethod
    def giveback(value, returnType, line):
        if isinstance(value, returnType):
            return value
        else:
            Compiler.error('TypeError', line + 1, extra=f'Expected -{returnType.__name__}- but -{type(value).__name__}- was returned')

    @staticmethod
    def load(file: str):
        """
        Loads Apricot Library file and adds functions to enviroment in the corresposding module.
        :param file:
        :return:
        """
        # Get file path
        folder = os.path.dirname(sys.argv[0])
        path = folder + ("\\" if folder else "") + file
    
        # Checking file type
        if not file.endswith('.apl'):
            Compiler.error('LibraryError', -1, line=path, extra='Wrong file type')
        if not os.path.exists(path):
            Compiler.error('LibraryError', -1, line=path, extra='File not found')
    
        # Module
        name = os.path.basename(file)[:-4]
        library = Library(path)
    
        # Reading
        with open(path, 'rb') as f:
            code = f.read().decode('utf-8', errors='ignore')
    
        # Checking if the code is valid
        allowed = ['\t', 'func', 'class', '\n', '    ', '', r'//', 'using', 'import']
        for l, line in enumerate(code.splitlines()):
            for allow in allowed:
                if line.startswith(allow):
                    break

            else:
                Compiler.error('LibraryError', l + 1)
    
        # Running
        env = {'Compiler.log': print, 'load': Compiler.load, 'Pointer': Pointer, 'variable': Compiler.variable,  'giveback': Compiler.giveback, 'null': None, 'true': True, 'false': False}
        compiled, _, _ = Compiler.compile(code)
        exec(compiled, env)
    
        # Clean globals
        for var, val in dict(env).items():
            if callable(val):
                setattr(library, var, val)
    
        return {name: library}

    @staticmethod
    def variable(name: str, value, l: int, env: dict, varType: type = ''):
        """
        Built-in function used in compilation to handle variable creation and assignment.
        :param env:
        :param name:
        :param value:
        :param l:
        :param varType:
        :return:
        """
        constants = env["_constants"]
    
        # value = eval(value, env)
        if varType:
            if name in constants:
                Compiler.error('VariableError', l + 1, extra=f'Variable "{name}" is already a constant', description=name)
            elif not isinstance(value, varType):
                Compiler.error('TypeError', l + 1, extra=f'Variable type defined as -\x1a{varType.__name__}\x1a- but value is -\x1a{type(value).__name__}\x1a-', description=str(value))
        else:
            if name in constants:
                Compiler.error('VariableError', l + 1, extra=f'Variable "{name}" is already a constant', description=name)
            elif name not in env:
                Compiler.error('VariableError', l + 1, extra=f'Variable "{name}" has not yet been created', description=name)
            elif not isinstance(value, type(env[name])):
                Compiler.error('TypeError', l + 1, extra=f'Variable type defined as -\x1a{type(env[name]).__name__}\x1a- but value is -\x1a{type(value).__name__}\x1a-', description=str(value))
    
        try:
            env[name] = value
        except Exception as e:
            Compiler.error('CompilationError', -1, line="{S.BOLDERLINE}Recreated Line:{S.UNBOLDERLINE} {name} = {value}", extra='An error occurred during compilation')
    
    @staticmethod
    def log(*values: object, sep: str | None = "\n", end: str | None = "\n", flush: bool = False):
        values = [str(value) for value in values]
    
        # Replace renames
        objectRenames = {'Callable': 'Function', 'print': 'log', 'None': 'null', 'True': 'true', 'False': 'false'}
        for v, value in enumerate(values):
            for repl in re.findall(r'\x1a(\w+)\x1a', str(value)):
                # Check if it needs a replacement
                if repl not in objectRenames:
                    values[v] = values[v].replace(f'\x1a{repl}\x1a', repl)
                    continue
    
                # Replace
                values[v] = values[v].replace(f'\x1a{repl}\x1a', objectRenames[repl])
    
        # Print
        print(*values, sep=sep, end=end, flush=flush)
    
    @staticmethod
    def compile(code: str):
        """
        Compiles Apricot code into Python code. Returns the compiled code, a cache, and any constants.
        :param code:
        :return:
        """
        # Blank code
        if not code:
            return '', Cache.Snapshot()

        if code[0] == '$':
            Compiler.error("Test error", 1)

        # Variables
        warnings = []
        constants = {}
        Compiler.code = code
        compiled = code
        direct = {r'(switch ([^:]+):)': 'match \x1a:1:', r'(this\.(\w+))': 'self.\x1a:1', r'(throw (\w+);)': 'raise \x1a:1', r'(catch( +.+)?:)': 'except \x1a:1:',
                  r'(import (.*);)': 'globals().update(load(".libraries/\x1a:1.apl"))', r'(include (\w+);)': 'import \x1a:1',
                  r'(using (.*):)': 'with \x1a:1:', r'(span\((.*)\))': 'range(\x1a:1)', r'(@(\w[\w _0-9]*))\b': "Pointer('\x1a:1', globals())", r'(\^(\w.*))\b': '\x1a:1.val',
                  r'(noop;())': 'pass', r'(\((.+)\.\.(.+)\.\.(.+)\))': 'range(\x1a:1, \x1a:2, \x1a:3)', r'(\((.+)\.\.(.+)\))': 'range(\x1a:1, \x1a:2)', r'((def +\w+)\(this)':
                      '\x1a:1(self'}
        syntax = [*direct.values(), r'__init__([^)]*)', r'lambda \w+: ', r'nonlocal \w+', 'async ', 'await ', 'from .* import .*', 'for .* in .*:', '->', r'range(\d+, *\d+(?:, *\d+))']
        # nameErrors = [r'globals\(\)', r'locals\(\)']
        nameErrors = []
        syntaxPhrase = [r'func +\w+ +\w+\(self']
        directPhrase = {'else if': 'elif', 'next;': 'continue', r'\btrue\b': 'True', r'\bfalse\b': 'False'}
    
        # String replacements
        strings = []
        for s, string in enumerate(re.findall(r'''((["'])[^(?:\2)]+\2)''', compiled)):
            compiled = compiled.replace(string[0], f'\x1a={s}')
            strings.append(string[0])
    
        # Semicolons
        for l, line in enumerate(compiled.splitlines()):
            # Strip whitespace
            line = line.strip()
    
            # Comments and empty lines
            if line == '' or re.match(r'.*//.*$', line):
                continue
    
            if line.strip()[-1] not in [':', ';']:
                warning = Compiler.warn('EOLError', l + 1, extra="Missing end of line marker")
                warnings.append(warning)
    
        # Comments
        for comm in re.findall(r'//.*', compiled):
            compiled = compiled.replace(comm, '# There was a comment...')
    
        # Syntax keyword errors
        for l, line in enumerate(compiled.splitlines()):
            for syn in syntax:
                found = re.findall(re.escape(syn), line)
                if found:
                    Compiler.error('SyntaxError', l + 1, description=found[0], extra="Bad phrase.")
    
        # Syntax phrase errors
        for l, line in enumerate(compiled.splitlines()):
            for syn in syntaxPhrase:
                found = re.findall(syn, line)
                if found:
                    Compiler.error('SyntaxError', l + 1, description=found[0], extra="Bad phrase.")
    
        # Name errors
        for l, line in enumerate(compiled.splitlines()):
            for syn in nameErrors:
                found = re.findall(syn, line)
                if found:
                    Compiler.error('NameError', l + 1, description=found[0], extra='Function {found[0]} not defined.')
    
        # Pull classes to use for rest of code
        classes = ['Pointer', 'Function']
        classes.extend(re.findall(r'class (\w+) *(?:inherits)? *(?:[_a-zA-Z][\w_]*)* *:', compiled))
        classNames = f'{"|" if classes else ""}{"|".join(classes)}'
    
        # Class declarations
        for l, line in enumerate(compiled.splitlines()):
            for cls in re.findall(r'class (\w+) *(?:inherits)? *([_a-zA-Z][\w_]*)? *:', line):
                compiled = compiled.replace(line, f'class {cls[0]}({cls[1]}):')

        # Class blocks
        for b, block in enumerate(re.findall(r'class\s+\w+(?:\([^)]+\))?:\s*\n(?:[ \t]+[^\n]*\n?|\n)*', compiled)):
            for func in re.findall(rf'(( *)func +(null|int|float|str|bool|bytes|list|tuple|dict|object{classNames}) +([a-zA-Z][a-zA-Z0-9_]*)\(([^)]*)\):)', block):
                compiled = compiled.replace(block, block.replace(func[0], f'{func[1]}func {func[2]} {func[3]}(this{", " if func[4] else ""}{func[4]}):'))

        # Remove old type casting
        for l, line in enumerate(compiled.splitlines()):
            wrongCasts = re.findall(rf'((int|float|str|bool|list|tuple|dict|object)\([^)]*\))', line)
            if wrongCasts:
                Compiler.error('SyntaxError', l + 1, description=wrongCasts[0][0])
    
        # Type casting
        for cast in re.findall(rf'(< ?(int|float|str|bool|list|tuple|dict|object{classNames}) ([^>]*) ?>)', compiled):
            compiled = compiled.replace(cast[0], f'{cast[1]}({cast[2]})')
    
        # Wrong __init__ with return type specified
        wrongInits = re.findall(rf'(class (\w+)(\([^)]*\))?:\n+([\t ]*)func (int|float|str|list|tuple|object|bool|null{classNames}) \2\(([^)]*)\) *:)', compiled)
        if wrongInits:
            Compiler.error('SyntaxError', wrongInits[0][4], F.searchLine(wrongInits[0][0].split('\n')[-1].strip(), compiled), 'Class constructors should not return anything')
    
        # Correct __init__ adding return type
        replInits = re.findall(rf'(([\t ]*)class (\w+)(\([^)]*\))?:([\s\S]*?)func \3\(([^)]*)\) *:)', compiled)
        for repl in replInits:
            compiled = compiled.replace(repl[0], f'{repl[1]}class {repl[2]}{repl[3]}:{repl[4]}func null {repl[2]}({repl[5]}):')
    
        # Constants
        for l, line in enumerate(compiled.splitlines()):
            for full, name, value in re.findall(r'(const: *([a-zA-Z_][\w_]*) *= *(.*);)', line):
                if name in constants:
                    Compiler.error('ConstantError', l + 1, description=name, extra='Cannot change value of constant "{name}"')
                else:
                    constants[name] = value
                    compiled = compiled.replace(full, f'# CONST')
    
        # Tabs
        compiled = compiled.replace('\t', '    ')

        # Constant replacements
        for const, value in constants.items():
            compiled = re.sub(rf'\b{const}(?! *=)\b', value, compiled)
    
        # Variable types
        for l, line in enumerate(compiled.splitlines()):
            variables = [list(found) for found in re.findall(rf'((int|float|str|bool|list|tuple|dict|object{classNames}): *(\w+) *= *([^;]+))', line)]
            for variable in variables:
                compiled = compiled.replace(variable[0], f'variable("{variable[2]}", {variable[3]}, {l}, globals(), {variable[1]})')
    
        # Plain var declarations
        for l, line in enumerate(compiled.splitlines()):
            plainVars = re.findall(r'((?<!this\.|....\S)(\w+) *= *([^;]+))', line)
            for plain in plainVars:
                compiled = compiled.replace(plain[0], f'variable("{plain[1]}", {plain[2]}, {l}, globals())')

        # Function returns
        current = ''
        for l, line in enumerate(compiled.splitlines()):
            # Get function or method
            func = re.match(fr'func (int|float|str|list|tuple|object|bool|null{classNames}) \w+', line.strip())
            if func:
                current = func.group(1)
                continue
            returning = re.match('return +([^;]+);', line.strip())
            if returning:
                compiled = compiled.replace(returning[0], f'return giveback({returning[1]}, {current}, {l})')

        # Functions
        functions = re.findall(rf'(( *)func +(null|int|float|str|bool|bytes|list|tuple|dict|object{classNames}) +([a-zA-Z][a-zA-Z0-9_]*)\(([^)]*)\):)', compiled)
        for func in functions:
            compiled = compiled.replace(func[0], f'{func[1]}def {func[3]}({func[4]}{", " if func[4] else ""}*_: object) -> {func[2] if func[2] != "null" else "None"}:')

        # __init__ keyword errors
        wrongInits = re.findall(r'(class (\w+)(\([^)]*\))?:\n[\t ]*func __init__(\([^)]*\)):)', compiled)
        if wrongInits:
            Compiler.error('SyntaxError', F.searchLine('__init__', compiled))
    
        # Replacing constructor with __init__
        inits = re.findall(rf'(class (\w+)(\([^)]*\))?:\n+([\t ]*)def \2\(([^)]*)\) *-> *(int|float|str|list|tuple|object|bool|None{classNames}) *:)', compiled)
        for init in inits:
            compiled = compiled.replace(init[0], f'class {init[1]}{init[2]}:\n{init[3]}def __init__(self{", " if init[4] else ""}{init[4]}) -> {init[5] if init[5] != "null" else "None"}:')
    
        # Switch replacements
        for apr, py in direct.items():
            for found in re.findall(apr, compiled):
                for p, part in enumerate(found):
                    py = py.replace(f'\x1a:{p}', part)

                compiled = compiled.replace(found[0], py)
    
        # Switch phrase replacements
        for apr, py in directPhrase.items():
            compiled = re.sub(apr, py, compiled)
    
        # Inject strings
        for f, fill in enumerate(strings):
            compiled = compiled.replace(f'\x1a={f}', fill)
    
        # Automatic error handling wrap
        # compiled = f'try:\n' + '\n'.join([f'    {line}' for line in compiled.splitlines()]) + ('\nexcept Exception as e:\n    print(f"\033[31m{type(e).__name__}: {e} @ line {'e.__traceback__.tb_lineno - 1}\033[0m")')
    
        # Setup
        compiled = f'{compiled}\n'
        # Remove semicolons
        compiled = compiled.replace(';\n', '\n')
    
        # Cache
        cache = Cache.Snapshot()
        cache.save(code, compiled, constants, warnings)
        Compiler.compiled = compiled

        return compiled, cache, constants
