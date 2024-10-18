from Apricode import *
from math import floor
import re
import sys
import os
from Functions import *

strings = []


def tyval(value):
    global strings

    if value[0] == '\x1a':
        return str
    try:
        return type(eval(value))
    except NameError:
        return object
    except SyntaxError:
        return tyval(inject(value, strings))

def findLine(phrase: str, paragraph: str):
    lines = paragraph.splitlines()
    for i, line in enumerate(lines):
        if phrase in line:
            return i + 1
    return "N/A"

def funcUpType(l: int, paragraph: str):
    for line in paragraph.splitlines()[l::-1]:
        if line.strip().startswith('def '):
            # Find return type annotation and remove whitespace/colon
            funcType = eval(line.split('->')[1][:-1].strip())
            return funcType if funcType is None else funcType.__name__

def indents(line: str):
    count = 0
    for char in line:
        if char == '\t':
            count += 1
        elif char == ' ':
            count += .25
        else:
            break
    return floor(count)

def apricompile(code: str, name: str):
    global strings

    # Variables
    altered = code
    varTypes = {}
    strings = []
    direct = {r'(switch ([^:]+):)': 'match \x1a:1:', r'(this\.(\w+))': 'self.\x1a:1', r'(throw (\w+);)': 'raise \x1a:1', r'(catch (\w+);)': 'except \x1a:1',
              r'(iter +(\w+) +in +([^;]+);)': 'for \x1a:1 in \x1a:2:', 'else if': 'elif', 'next;': 'continue'}
    syntax = [*direct.values(), r'__init__([^)]*)', r'lambda \w+: ', r'nonlocal \w+', 'with ', 'async ', 'await ']
    syntaxPhrase = [r'\bFalse\b', r'\bTrue\b']
    directPhrase = {r'\bnull\b': 'None'}

    # Comments
    for comm in re.findall(r'\\\\.*', altered):
        altered = altered.replace(comm, '')

    # Semicolons
    for l, line in enumerate(altered.splitlines()):
        # Strip whitespace
        line = line.strip()

        # Comments and empty lines
        if line[:2] in [r'\\', '']:
            continue

        if line[-1] not in [':', ';']:
            error('LineError', line.strip(), line.strip(), l)

    # String replacements
    for s, string in enumerate(re.findall(r'''((["'])[^\2\s]+\2)''', altered)):
        altered = altered.replace(string[0], f'\x1a@{s}')
        strings.append(string[0])

    # Syntax keyword errors
    for l, line in enumerate(altered.splitlines()):
        for syn in syntax:
            if re.findall(syn, line):
                error('SyntaxError', line, syn, l)

    # Syntax phrase errors
    for l, line in enumerate(altered.splitlines()):
        for syn in syntaxPhrase:
            if re.findall(syn, line):
                error('SyntaxError', line, syn, l)

    # Remove old type casting
    for l, line in enumerate(altered.splitlines()):
        wrongCasts = re.findall(r'((int|float|str|bool|list|tuple|dict|object)\([^)]*\))', line)
        if wrongCasts:
            error('SyntaxError', wrongCasts[0][0], line, l)

    # Functions
    functions = re.findall(r'(func +(null|int|float|str|bool|bytes|list|tuple|dict|object) +([a-zA-Z][a-zA-Z0-9_]*)\(([^)]*)\):)', altered)
    for func in functions:
        altered = altered.replace(func[0], f'def {func[2]}({func[3]}, *_: object) -> {func[1] if func[1] != "null" else "None"}:')

    # Variable types
    for l, line in enumerate(altered.splitlines()):
        variables = [list(found) for found in re.findall(r'((\w+): *(int|float|str|bool|list|tuple|dict|var|object) *= *([^;]+))', line)]
        for variable in variables:
            if variable[1] in varTypes.keys():
                error('NameError', line.strip(), variable[1], l, f'Variable with name "{variable[1]}" already created')

            if variable[2] == 'var':
                variable[2] = tyval(variable[3]).__name__
                altered = altered.replace(variable[0], f'{variable[1]}: *{variable[2]} *= *{variable[3]}')

            if tyval(variable[3]) is not eval(variable[2]):
                error('TypeError', line.strip(), variable[0], l, f'Variable type defined as -{variable[2]}- but value is -{tyval(variable[3]).__name__}-')

            varTypes[variable[1]] = tyval(variable[3])

    # Plain var declarations
    for l, line in enumerate(altered.splitlines()):
        plainVars = re.findall(r'((?<!.)(\w+) ?= ?(\S*))', line)
        for plain in plainVars:
            if plain[1] not in varTypes.keys():
                error('VariableError', line.strip(), plain[1], l, 'Variable assignment before creation')
            elif tyval(plain[2][:-1]) is not varTypes[plain[1]]:
                error('TypeError', line.strip(), plain[0], l, f'Variable type defined as -{varTypes[plain[1]].__name__}- but value is -{tyval(plain[2][:-1]).__name__}-')

    # Wrong __init__
    wrongInits = re.findall(r'(class (\w+)(\([^)]*\))?:\n[\t ]*func __init__(\([^)]*\)):)', altered)
    if wrongInits:
        error('SyntaxError', f'func __init__{wrongInits[0][3]}', f'__init__', findLine('__init__', altered))

    # Fixing __init__
    inits = re.findall(r'(class (\w+)(\([^)]*\))?:\n+[\t ]*def \2(\([^)]*\)) *-> *(int|float|str|list|tuple|object|bool|None) *:)', altered)
    for init in inits:
        altered = altered.replace(init[0], f'class {init[1]}{init[2]}:\n    def __init__{init[3]} -> {init[4] if init[4] != "null" else "None"}:')

    # Final return checks
    for l, line in enumerate(altered.splitlines()):
        funcReturns = re.findall(r'(((?:\t| {4})*)return ([^;]*);)', line)
        # 0 = full phrase, 1 = full whitespace, 2 = returning phrase
        for funcReturn in funcReturns:
            # Prevent all similar returns from being incorrectly replaced
            altered = '\n'.join([*altered.splitlines()[:l], f'{funcReturn[1]}return returnCheck({funcReturn[2]}, {funcUpType(l, altered)}, "{line}", {l})', *altered.splitlines()[l + 1:]])

    # Switch replacements
    for apr, py in direct.items():
        for found in re.findall(apr, altered):
            repl = py
            for p, part in enumerate(found):
                repl = repl.replace(f'\x1a:{p}', part)

            altered = altered.replace(found[0], repl)

    # Switch phrase replacements
    for apr, py in directPhrase.items():
        altered = re.sub(apr, py, altered)

    # Type casting
    for cast in re.findall('(<(int|float|str|bool|list|tuple|dict|object) ?(.*)>)', altered):
        altered = altered.replace(cast[0], f'{cast[1]}({cast[2]})')

    # Inject strings
    for f, fill in enumerate(strings):
        altered = altered.replace(f'\x1a@{f}', fill)

    # Setup
    altered = altered.replace(';\n', '\n')

    return Apricode(name, version=0.1, code=code, compiled=altered)

if __name__ == '__main__':
    if os.path.basename(sys.argv[0]) == 'Apricot.py':
        if '-p' in sys.argv:
            sys.argv[0] = sys.argv[sys.argv.index('-p') + 1]
        else:
            sys.exit()

    with open(sys.argv[0], 'r', encoding='utf-8-sig') as f:
        code = f.read()

    codeclass = apricompile(code, os.path.basename(sys.argv[0]))

    if '-e' in sys.argv:
        codeclass.execute()

    if '-w' in sys.argv:
        with open(sys.argv[sys.argv.index('-w') + 1], 'w') as f:
            f.write(codeclass.compiled)
