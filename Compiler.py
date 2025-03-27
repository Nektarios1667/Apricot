import sys
from Colors import ColorText as C
from Library import Library
import os
import Cache
from Cache import outputs
import re
from Pointers import Pointer as pointer


class Compiler:

    @staticmethod
    def inject(phrase: str):
        """
        Injects all strings into phrase by replacing \x1a@{#} with the index in the string list.
        :param phrase:
        :return:
        """
        global strings

        phrase = str(phrase)
        for f, fill in enumerate(strings):
            phrase = phrase.replace(f'\x1a@{f}', fill)
        return phrase

    @staticmethod
    def getline(l: int, phrase: str):
        """
        Returns the line of the code based on l. Note: the line numbers start at 1
        :param phrase:
        :param l:
        :return:
        """
        while '\n\n' in phrase:
            phrase = phrase.replace('\n\n', '\n// There once was a double newline...\n')

        return phrase.splitlines()[l - 1]

    @staticmethod
    def bracesConvert(apricode: str):
        lines = apricode.splitlines()
        result = []
        indents = [0]  # Stack to track current indentation levels

        for line in lines:
            # Check opening
            if line.strip().endswith('{'):
                headerIndent = len(line) - len(line.lstrip('\t'))
                result.append(line.replace('{', ':'))  # Remove `{`
                indents.append(headerIndent + 1)
                continue

            # Check closing
            if line.strip().endswith('}'):
                line = line.replace('}', '')
                indents.pop()

            # Regular line
            currentIndent = indents
            result.append('\t' * currentIndent[-1] + line.lstrip())

        return "\n".join(result)

    @staticmethod
    def error(error: str, description: str, l: int, extra: str = '', line: str = ''):
        global altered, code

        # If line isn't specified find automatically
        line = line or "Unknown line"

        # Printing and closing
        print(f'{C.RED}{error}: "{Compiler.inject(line.strip())}" - "{Compiler.inject(description.strip())}" @ line {l}\n{extra}{C.RESET}')

        if '-w' in sys.argv:
            with open(sys.argv[sys.argv.index('-w') + 1], 'w') as f:
                f.write(altered)

        sys.exit(-1)

    @staticmethod
    def findLine(phrase: str, paragraph: str):
        """
        Finds the line number of the phrase in the given paragraph. Note: the line numbers start at 1
        :param phrase:
        :param paragraph:
        :return:
        """
        lines = paragraph.splitlines()
        for i, line in enumerate(lines):
            if phrase in line:
                return i + 1
        return "N/A"

    @staticmethod
    def load(file: str):
        """
        Loads Apricot Library file and adds functions to enviroment in the corresposding module.
        :param file:
        :return:
        """
        # Get file path
        folder = os.path.dirname(sys.argv[1])

        # Checking file type
        if not file.endswith('.apl'):
            Compiler.error('LibraryError', file, -1, extra='Expected file with .apl extension')
        if not os.path.exists(f'{folder}/{file}'):
            Compiler.error('LibraryError', file, -1, extra='File not found')

        # Module
        name = os.path.basename(file)[:-4]
        library = Library(f'{folder}/{file}')

        # Reading
        with open(f'{folder}/{file}', 'rb') as f:
            code = f.read().decode('utf-8', errors='ignore')

        # Checking if the code is valid
        allowed = ['\t', 'func', 'class', '\n', '    ', '', r'//', 'using', 'import']
        for l, line in enumerate(code.splitlines()):
            for allow in allowed:
                if line.startswith(allow):
                    break

            else:
                Compiler.error('LibraryError', line, l + 1)

        # Running
        compiled, importing, _ = Compiler.apricompile(code, None)
        exec(compiled, importing)

        # Clean globals
        for var, val in dict(importing).items():
            if callable(val):
                setattr(library, var, val)

        return {name: library}

    @staticmethod
    def variable(name: str, value, l: int, env: dict, varType: str = ''):
        """
        Built-in function used in compilation to handle variable creation and assignment.
        :param env:
        :param name:

        :param value:
        :param l:
        :param varType:
        :return:
        """
        global varTypes, altered

        # value = eval(value, env)
        if varType:
            varType = eval(varType, env)

            if name in varTypes:
                Compiler.error('VariableError', name, l + 1, extra=f'Variable "{name}" is already created')
            elif name in constants:
                Compiler.error('VariableError', name, l + 1, extra=f'Variable "{name}" is already a constant')
            elif not isinstance(value, varType):
                Compiler.error('TypeError', str(value), l + 1, extra=f'Variable type defined as -{varType.__name__}- but value is -{type(value).__name__}-')
        else:
            if name in constants:
                Compiler.error('VariableError', name, l + 1, extra=f'Variable "{name}" is already a constant')
            elif name not in env:
                Compiler.error('VariableError', name, l + 1, extra=f'Variable "{name}" has not yet been created')
            elif not isinstance(value, type(env[name])):
                Compiler.error('TypeError', str(value), l + 1, extra=f'Variable type defined as -{type(env[value])}- but value is -{type(value).__name__}-')

        try:
            env[name] = value
        except Exception as e:
            Compiler.error('CompilationError', 'An error occurred during compilation', l + 1)

    @staticmethod
    def apricompile(code: str, cached: dict | None):
        """
        Compiles Apricot code into Python code. Returns the compiled code and a dictionary containing the global enviroment variables. The enviroment variables are used during runtime for the
        compiled seudo-Python code.
        :param cached:
        :param code:
        :return:
        """
        global strings, varTypes, altered, constants

        # Starting enviroment
        env = {'log': print, 'load': Compiler.load, 'pointer': pointer, 'variable': Compiler.variable, 'null': None, 'true': True, 'false': False}

        # Blank code
        if not code:
            return '', env, Cache.Snapshot()

        # Checking if script is all internal
        if cached and not outputs(code, cached['regexes']['persistents']):
            return '# There was some code...\x05', env, Cache.Snapshot()

        # Variables
        constants = {}
        altered = code
        varTypes = {}
        strings = []
        direct = {r'(switch ([^:]+):)':             'match \x1a:1:', r'(this\.(\w+))': 'self.\x1a:1', r'(throw (\w+);)': 'raise \x1a:1', r'(catch( .+)?:)': 'except \x1a:1:',
                  r'(for (\w[\w\d_]*) ?:: ?(.*):)': 'for \x1a:1 in \x1a:2:', r'(import (.*);)': 'globals().update(load(".libraries/\x1a:1.apl"))', r'(include (\w+);)': 'import \x1a:1',
                  r'(using (.*):)':                 'with \x1a:1:', r'(span\((.*)\))': 'range(\x1a:1)', r'(@(\w[\w _0-9]*))\b': "pointer('\x1a:1', globals())", r'(\^(\w.*))\b': '\x1a:1.val',
                  r'(noop;())':                     'pass', r'(\|(.+), *(.+), *(.+)\|)': 'range(\x1a:1, \x1a:2, \x1a:3)'}
        syntax = [*direct.values(), r'__init__([^)]*)', r'lambda \w+: ', r'nonlocal \w+', 'async ', 'await ', 'from .* import .*', 'for .* in .*:', '->', r'range(\d+, *\d+(?:, *\d+))']
        # nameErrors = [r'globals\(\)', r'locals\(\)']
        nameErrors = []
        syntaxPhrase = [r'\bFalse\b', r'\bTrue\b']
        directPhrase = {'else if': 'elif', 'next;': 'continue', r'\btrue\b': 'True', r'\bfalse\b': 'False'}

        # Comments
        for comm in re.findall(r'//.*', altered):
            altered = altered.replace(comm, '# There was a comment...;')

        # Braces conversions
        # altered = Compiler.bracesConvert(altered)

        # Semicolons
        for l, line in enumerate(altered.splitlines()):
            # Strip whitespace
            line = line.strip()

            # Comments and empty lines
            if line[:2] in [r'//', '']:
                continue

            if line[-1] not in [':', ';']:
                Compiler.error('LineError', line.strip(), l + 1)

        # String replacements
        for s, string in enumerate(re.findall(r'''((["'])[^\2\s]+\2)''', altered)):
            altered = altered.replace(string[0], f'\x1a={s}')
            strings.append(string[0])

        # Syntax keyword errors
        for l, line in enumerate(altered.splitlines()):
            for syn in syntax:
                found = re.findall(syn, line)
                if found:
                    Compiler.error('SyntaxError', found[0], l + 1)

        # Syntax phrase errors
        for l, line in enumerate(altered.splitlines()):
            for syn in syntaxPhrase:
                found = re.findall(syn, line)
                if found:
                    Compiler.error('SyntaxError', found[0], l + 1)

        # Local variables
        for l, line in enumerate(altered.splitlines()):
            for var in re.findall(r'~[a-zA-Z_][\w_]*', line):
                altered = altered.replace(var, f'locals()["{var[1:]}"]')

        # Name errors
        for l, line in enumerate(altered.splitlines()):
            for syn in nameErrors:
                found = re.findall(syn, line)
                if found:
                    Compiler.error('NameError', found[0], l + 1, extra=f'Function {found[0]} not defined.')

        # Pull classes to use for rest of code
        classes = ['pointer', 'function']
        classes.extend(re.findall(r'class (\w+) *(?:inherits)? *(?:[_a-zA-Z][\w_]*)* ?:', altered))
        classNames = f'{"|" if classes else ""}{"|".join(classes)}'

        # Class declarations
        for l, line in enumerate(altered.splitlines()):
            for cls in re.findall(r'class (\w+) *(?:inherits)? *([_a-zA-Z][\w_]*)? ?:', line):
                altered = altered.replace(line, f'class {cls[0]}({cls[1]}):')

        # Remove old type casting
        for l, line in enumerate(altered.splitlines()):
            wrongCasts = re.findall(rf'((int|float|str|bool|list|tuple|dict|object)\([^)]*\))', line)
            if wrongCasts:
                Compiler.error('SyntaxError', wrongCasts[0][0], l + 1)

        # Type casting
        for cast in re.findall(rf'(< ?(int|float|str|bool|list|tuple|dict|object{classNames}) ([^>]*) ?>)', altered):
            altered = altered.replace(cast[0], f'{cast[1]}({cast[2]})')

        # Wrong __init__ with return type specified
        wrongInits = re.findall(rf'(class (\w+)(\([^)]*\))?:\n+([\t ]*)func (int|float|str|list|tuple|object|bool|null{classNames}) \2\(([^)]*)\):)', altered)
        if wrongInits:
            Compiler.error('SyntaxError', wrongInits[0][4], Compiler.findLine(wrongInits[0][0].split('\n')[-1].strip(), altered), 'Class constructors should not return anything')

        # Correct __init__ adding return type
        replInits = re.findall(rf'(class (\w+)(\([^)]*\))?:(\n+[\t ]*)func \2\(([^)]*)\):)', altered)
        for repl in replInits:
            altered = altered.replace(repl[0], f'class {repl[1]}{repl[2]}:{repl[3]}func null {repl[1]}({repl[4]}):')

        # Functions
        functions = re.findall(rf'(( *)func +(null|int|float|str|bool|bytes|list|tuple|dict|object{classNames}) +([a-zA-Z][a-zA-Z0-9_]*)\(([^)]*)\):)', altered)
        for func in functions:
            altered = altered.replace(func[0], f'{func[1]}def {func[3]}({func[4]}, *_: object) -> {func[2] if func[2] != "null" else "None"}:')

        # Variable types
        for l, line in enumerate(altered.splitlines()):
            variables = [list(found) for found in re.findall(rf'((int|float|str|bool|list|tuple|dict|object{classNames}): *(\w+) *= *([^;]+);)', line)]
            for variable in variables:
                altered = altered.replace(variable[0], f'variable("{variable[2]}", {variable[3]}, {l}, globals(), "{variable[1]}")')

        # Plain var declarations
        for l, line in enumerate(altered.splitlines()):
            plainVars = re.findall(r'((\w+) *= *([^;]+);)', line)
            for plain in plainVars:
                altered = altered.replace(plain[0], f'variable("{plain[1]}", {plain[2]}, {l}, globals())')

        # __init__ keyword errors
        wrongInits = re.findall(r'(class (\w+)(\([^)]*\))?:\n[\t ]*func __init__(\([^)]*\)):)', altered)
        if wrongInits:
            Compiler.error('SyntaxError', f'__init__', Compiler.findLine('__init__', altered))

        # Replacing constructor with __init__
        inits = re.findall(rf'(class (\w+)(\([^)]*\))?:\n+([\t ]*)def \2\(([^)]*)\) *-> *(int|float|str|list|tuple|object|bool|None{classNames}) *:)', altered)
        for init in inits:
            altered = altered.replace(init[0], f'class {init[1]}{init[2]}:\n{init[3]}def __init__(self, {init[4]}) -> {init[5] if init[5] != "null" else "None"}:')

        # Switch replacements
        for apr, py in direct.items():
            while re.findall(apr, altered):
                for found in re.findall(apr, altered):
                    repl = py
                    for p, part in enumerate(found):
                        repl = repl.replace(f'\x1a:{p}', part)

                    altered = altered.replace(found[0], repl)

        # Switch phrase replacements
        for apr, py in directPhrase.items():
            altered = re.sub(apr, py, altered)

        # Constants
        for l, line in enumerate(altered.splitlines()):
            for full, name, value in re.findall(r'(const: *([a-zA-Z_][\w_]*) *= *(.*);)', line):
                if name in constants:
                    Compiler.error('ConstantError', name, l + 1, f'Cannot change value of constant "{name}"')
                else:
                    constants[name] = value
                    altered = altered.replace(full, f'# CONST')

        # Tabs
        altered = altered.replace('\t', '    ')

        # Constant replacements
        for const, value in constants.items():
            for repl in re.findall(fr'\b{const}\b', altered):
                altered = altered.replace(repl, value)

        # Inject strings
        for f, fill in enumerate(strings):
            altered = altered.replace(f'\x1a={f}', fill)

        # Automatic error handling wrap
        # altered = f'try:\n' + '\n'.join([f'    {line}' for line in altered.splitlines()]) + '\nexcept Exception as e:\n    exception(e)'

        # Setup
        altered = altered + '\n' if altered[-1] != '\n' else altered + ''
        altered = altered.replace(';\n', '\n')

        # Cache
        cache = Cache.Snapshot()
        cache.save(code, altered, env)

        return altered, env, cache
