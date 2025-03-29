import sys

import Builtins
from Colors import ColorText as C
from Library import Library
import os
import Cache
import re
from Pointers import Pointer


strings = []
altered = ''
class Compiler:
    @staticmethod
    def searchLine(phrase: str, code: str):
        """
        Finds the line number of the phrase in the given paragraph. Note: the line numbers start at 1.
        :param phrase:
        :param code:
        :return:
        """
        lines = code.splitlines()
        for l, line in enumerate(lines):
            if phrase in line:
                return l + 1
        return "N/A"

    @staticmethod
    def apricompile(code: str):
        """
        Compiles Apricot code into Python code. Returns the compiled code and a dictionary containing the global enviroment variables. The enviroment variables are used during runtime for the
        compiled code.
        :param code:
        :return:
        """
        global strings, altered

        # Blank code
        if not code:
            return '', Cache.Snapshot()

        # Variables
        constants = {}
        altered = code
        direct = {r'(switch ([^:]+):)': 'match \x1a:1:', r'(this\.(\w+))': 'self.\x1a:1', r'(throw (\w+);)': 'raise \x1a:1', r'(catch( +.+)?:)': 'except \x1a:1:',
                  r'(import (.*);)': 'globals().update(load(".libraries/\x1a:1.apl"))', r'(include (\w+);)': 'import \x1a:1',
                  r'(using (.*):)': 'with \x1a:1:', r'(span\((.*)\))': 'range(\x1a:1)', r'(@(\w[\w _0-9]*))\b': "Pointer('\x1a:1', globals())", r'(\^(\w.*))\b': '\x1a:1.val',
                  r'(noop;())': 'pass', r'(\|(.+), *(.+), *(.+)\|)': 'range(\x1a:1, \x1a:2, \x1a:3)', r'((def +\w+)\(this)': '\x1a:1(self'}
        syntax = [*direct.values(), r'__init__([^)]*)', r'lambda \w+: ', r'nonlocal \w+', 'async ', 'await ', 'from .* import .*', 'for .* in .*:', '->', r'range(\d+, *\d+(?:, *\d+))']
        # nameErrors = [r'globals\(\)', r'locals\(\)']
        nameErrors = []
        syntaxPhrase = [r'\bFalse\b', r'\bTrue\b', r'func +\w+ +\w+\(self']
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
                Builtins.error('LineError', line.strip(), l + 1)

        # String replacements
        for s, string in enumerate(re.findall(r'''((["'])[^\2\s]+\2)''', altered)):
            altered = altered.replace(string[0], f'\x1a={s}')
            strings.append(string[0])

        # Syntax keyword errors
        for l, line in enumerate(altered.splitlines()):
            for syn in syntax:
                found = re.findall(re.escape(syn), line)
                if found:
                    Builtins.error('SyntaxError', found[0], l + 1, line=line, extra="Bad phrase.")

        # Syntax phrase errors
        for l, line in enumerate(altered.splitlines()):
            for syn in syntaxPhrase:
                found = re.findall(syn, line)
                if found:
                    Builtins.error('SyntaxError', found[0], l + 1, line=line, extra="Bad phrase.")

        # Name errors
        for l, line in enumerate(altered.splitlines()):
            for syn in nameErrors:
                found = re.findall(syn, line)
                if found:
                    Builtins.error('NameError', found[0], l + 1, extra=f'Function {found[0]} not defined.', line=line)

        # Pull classes to use for rest of code
        classes = ['Pointer', 'Function']
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
                Builtins.error('SyntaxError', wrongCasts[0][0], l + 1)

        # Type casting
        for cast in re.findall(rf'(< ?(int|float|str|bool|list|tuple|dict|object{classNames}) ([^>]*) ?>)', altered):
            altered = altered.replace(cast[0], f'{cast[1]}({cast[2]})')

        # Wrong __init__ with return type specified
        wrongInits = re.findall(rf'(class (\w+)(\([^)]*\))?:\n+([\t ]*)func (int|float|str|list|tuple|object|bool|null{classNames}) \2\(([^)]*)\):)', altered)
        if wrongInits:
            Builtins.error('SyntaxError', wrongInits[0][4], Compiler.searchLine(wrongInits[0][0].split('\n')[-1].strip(), altered), 'Class constructors should not return anything')

        # Correct __init__ adding return type
        replInits = re.findall(rf'(class (\w+)(\([^)]*\))?:(\n+[\t ]*)func \2\(([^)]*)\):)', altered)
        for repl in replInits:
            altered = altered.replace(repl[0], f'class {repl[1]}{repl[2]}:{repl[3]}func null {repl[1]}({repl[4]}):')

        # Functions
        functions = re.findall(rf'(( *)func +(null|int|float|str|bool|bytes|list|tuple|dict|object{classNames}) +([a-zA-Z][a-zA-Z0-9_]*)\(([^)]*)\):)', altered)
        for func in functions:
            altered = altered.replace(func[0], f'{func[1]}def {func[3]}({func[4]}{", " if func[4] else ""}*_: object) -> {func[2] if func[2] != "null" else "None"}:')

        # Constants
        for l, line in enumerate(altered.splitlines()):
            for full, name, value in re.findall(r'(const: *([a-zA-Z_][\w_]*) *= *(.*);)', line):
                if name in constants:
                    Builtins.error('ConstantError', name, l + 1, f'Cannot change value of constant "{name}"')
                else:
                    constants[name] = value
                    altered = altered.replace(full, f'# CONST')

        # Tabs
        altered = altered.replace('\t', '    ')

        # Constant replacements
        for const, value in constants.items():
            altered = re.sub(rf'\b{const}(?! *=)\b', value, altered)

        # Variable types
        for l, line in enumerate(altered.splitlines()):
            variables = [list(found) for found in re.findall(rf'((int|float|str|bool|list|tuple|dict|object{classNames}): *(\w+) *= *([^;]+);)', line)]
            for variable in variables:
                altered = altered.replace(variable[0], f'variable("{variable[2]}", {variable[3]}, {l}, globals(), "{variable[1]}")')

        # Plain var declarations
        for l, line in enumerate(altered.splitlines()):
            plainVars = re.findall(r'((?<!this\.|....\S)(\w+) *= *([^;]+);)', line)
            for plain in plainVars:
                altered = altered.replace(plain[0], f'variable("{plain[1]}", {plain[2]}, {l}, globals())')

        # __init__ keyword errors
        wrongInits = re.findall(r'(class (\w+)(\([^)]*\))?:\n[\t ]*func __init__(\([^)]*\)):)', altered)
        if wrongInits:
            Builtins.error('SyntaxError', f'__init__', Compiler.searchLine('__init__', altered))

        # Replacing constructor with __init__
        inits = re.findall(rf'(class (\w+)(\([^)]*\))?:\n+([\t ]*)def \2\(([^)]*)\) *-> *(int|float|str|list|tuple|object|bool|None{classNames}) *:)', altered)
        for init in inits:
            altered = altered.replace(init[0], f'class {init[1]}{init[2]}:\n{init[3]}def __init__(self{", " if init[4] else ""}{init[4]}) -> {init[5] if init[5] != "null" else "None"}:')

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

        # Inject strings
        for f, fill in enumerate(strings):
            altered = altered.replace(f'\x1a={f}', fill)

        # Automatic error handling wrap
        # altered = f'try:\n' + '\n'.join([f'    {line}' for line in altered.splitlines()]) + '\nexcept Exception as e:\n    exception(e)'

        # Setup
        altered += '\n'
        # Remove semicolons
        altered = altered.replace(';\n', '\n')

        # Cache
        cache = Cache.Snapshot()
        cache.save(code, altered, constants)

        return altered, cache, constants
