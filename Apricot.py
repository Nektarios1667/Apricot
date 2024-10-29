import re
import sys
import time
import traceback
import types
from typing import Literal

from numba import jit

from Colors import ColorText as C
import os
from Pointers import *
from Library import *

def inject(phrase: str):
    """
    Injects all strings into phrase by replacing \x1a@(#) with the index in the string list.
    :param phrase:
    :return:
    """
    global strings

    phrase = str(phrase)
    for f, fill in enumerate(strings):
        phrase = phrase.replace(f'\x1a@{f}', fill)
    return phrase

def getline(l: int, phrase: str):
    """
    Returns the line of the code based on l. Note: the line numbers start at 1
    :param phrase:
    :param l:
    :return:
    """
    spaced = phrase
    while '\n\n' in spaced:
        spaced = spaced.replace('\n\n', '\n//\n')

    return spaced.splitlines()[l - 1]

def fime(time: float | int, units: Literal['ms', 's', 'm', 'h', 'd']):
    factors = {'ms': .001, 's': 1, 'm': 60, 'h': 3_600, 'd': 86_400}

    seconds = time * factors[units]
    minutes = seconds/60
    hours = minutes/60
    days = hours/24
    if seconds < .1:
        return f'{seconds*1000:.1f} ms'
    elif minutes > 4:
        return f'{minutes:.1f} m'
    elif hours > 4:
        return f'{hours:.1f} h'
    elif days >= 1:
        return f'{days:.1f} d'
    else:
        return f'{seconds:.1f} s'

def error(error: str, description: str, l: int, extra: str = '', line: str = ''):
    # If line isn't specified find automatically
    line = line if line else getline(l, code)

    # Printing and closing
    print(f'{C.RED}{error}: "{inject(line.strip())}" - "{inject(description.strip())}" @ line {l}\n{extra}{C.RESET}')
    input('Press enter to exit.')
    sys.exit(-1)


def returnCheck(value, instance, l):
    # Convert None to NoneType
    instance = instance if instance is not None else types.NoneType

    # Checking
    if isinstance(value, instance):
        return value
    else:
        # Used for converting None to null
        valueStr = str(value) if value is not None else 'null'
        valueType = type(value).__name__ if value is not None else 'null'

        error('TypeError', valueStr, l + 1, f'Return type defined as -{"null" if instance is types.NoneType else instance.__name__}- but value is -{valueType}-')


def log(*args):
    if len(args) > 0:
        print('null' if args[0] is None else args[0], *args[1:])


def funcUpType(l: int, paragraph: str):
    for line in paragraph.splitlines()[l::-1]:
        if line.strip().startswith('def '):
            # Find return type annotation and remove whitespace/colon
            funcType = eval(line.split('->')[1][:-1].strip())
            return funcType if funcType is None else funcType.__name__


def tyval(value):
    """
    Returns the type of the evaluated string.
    :param value:
    :return:
    """
    global strings, env

    if value[0] == '\x1a':
        return str
    if '\x1a' in value:
        return tyval(inject(value))

    return type(eval(value, env))

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


def load(file: str):
    """
    Loads Apricot Library file and adds functions to enviroment in the corresposding module.
    :param file:
    :return:
    """
    global env

    # Checking file type
    if not file.endswith('.apl'):
        error('LibraryError', file, -1, extra='Expected file with .apl extension')
    if not os.path.exists(f'{folder}/{file}'):
        error('LibraryError', file, -1, extra='File not found')

    # Module
    name = os.path.basename(file)[:-4]
    library = Library(f'{folder}/{file}')

    # Reading
    with open(f'{folder}/{file}', 'rb') as f:
        code = f.read().decode('utf-8', errors='ignore')

    # Checking if the code is valid
    allowed = ['\t', 'func', 'class', '\n', '    ', '', r'//', 'using', 'import']
    for l, line in enumerate(code.splitlines()):
        correct = False

        for allow in allowed:
            if line.startswith(allow):
                correct = True
                break

        if not correct:
            error('LibraryError', line, l)

    # Running
    compiled, importing = apricompile(code)
    exec(compiled, importing)

    # Clean globals
    for var, val in dict(importing).items():
        if callable(val):
            setattr(library, var, val)

    env.update({name: library})

def variable(name: str, value, l: int, varType: str = ''):
    """
    Built-in function used in compilation to handle variable creation and assignment.
    :param name:
    :param value:
    :param l:
    :param varType:
    :return:
    """
    global env, varTypes

    if varType:
        varType = eval(varType, env)

        if isinstance(eval(value, env), varType) and name not in varTypes:
            env[name] = eval(value, env)
            varTypes[name] = varType
        elif name in varTypes:
            error('VariableError', name, l + 1, extra=f'Variable "{name}" is already created')
        else:
            error('TypeError', str(value), l + 1, extra=f'Variable type defined as -{varType.__name__}- but value is -{tyval(value).__name__}-')
    else:
        if name not in varTypes:
            error('VariableError', name, l + 1, extra=f'Variable "{name}" has not yet been created')
            env[name] = eval(value, env)
        elif not isinstance(eval(value, env), varTypes[name]):
            error('TypeError', str(value), l + 1, extra=f'Variable type defined as -{varTypes[name].__name__}- but value is -{tyval(value).__name__}-')
        else:
            env[name] = eval(value, env)

def apricompile(code: str):
    """
    Compiles Apricot code into Python code. Returns the compiled code and a dictionary containing the global enviroment variables. The enviroment variables are used during runtime for the
    compiled seudo-Python code.
    :param code:
    :return:
    """
    global strings, variable, varTypes

    # Variables
    env = {'log': log, 'returnCheck': returnCheck, 'load': load, 'variable': variable, 'pointer': Pointer}
    altered = code
    varTypes = {}
    strings = []
    direct = {r'(switch ([^:]+):)': 'match \x1a:1:', r'(this\.(\w+))': 'self.\x1a:1', r'(throw (\w+);)': 'raise \x1a:1', r'(catch (.+):)': 'except \x1a:1:',
              r'(for (\w[\w\d_]*) ?: ?(.*):)': 'for \x1a:1 in \x1a:2:', r'(import (.*);)': 'load(".libraries/\x1a:1.apl")', r'(include (\w+);)': 'import \x1a:1',
              r'(using (.*):)': 'with \x1a:1:', r'(span\((.*)\))': 'range(\x1a:1)', r'(@(\w[\w _0-9]*))\b': "pointer('\x1a:1', globals())", r'(\^(\w.*))\b': '\x1a:1.val'}
    syntax = [*direct.values(), r'__init__([^)]*)', r'lambda \w+: ', r'nonlocal \w+', 'async ', 'await ', 'from .* import .*', 'for .* in .*:', '->']
    nameErrors = [r'globals\(\)', r'locals\(\)']
    syntaxPhrase = [r'\bFalse\b', r'\bTrue\b']
    directPhrase = {r'\bnull\b': 'None', 'else if': 'elif', 'next;': 'continue'}

    # Comments
    for comm in re.findall(r'//.*', altered):
        altered = altered.replace(comm, '')

    # Tabs
    altered = altered.replace('\t', '    ')

    # Semicolons
    for l, line in enumerate(altered.splitlines()):
        # Strip whitespace
        line = line.strip()

        # Comments and empty lines
        if line[:2] in [r'//', '']:
            continue

        if line[-1] not in [':', ';']:
            error('LineError', line.strip(), l + 1)

    # String replacements
    for s, string in enumerate(re.findall(r'''((["'])[^\2\s]+\2)''', altered)):
        altered = altered.replace(string[0], f'\x1a={s}')
        strings.append(string[0])

    # Syntax keyword errors
    for l, line in enumerate(altered.splitlines()):
        for syn in syntax:
            found = re.findall(syn, line)
            if found:
                error('SyntaxError', found[0], l + 1)

    # Syntax phrase errors
    for l, line in enumerate(altered.splitlines()):
        for syn in syntaxPhrase:
            found = re.findall(syn, line)
            if found:
                error('SyntaxError', found[0], l + 1)

    # Name errors
    for l, line in enumerate(altered.splitlines()):
        for syn in nameErrors:
            found = re.findall(syn, line)
            if found:
                error('NameError', found[0], l + 1, extra=f'Function {found[0]} not defined.')

    # Pull classes to use for rest of code
    classes = ['pointer', 'function']
    classes.extend(re.findall(r'class (\w+)(?:\(.*\))? ?:', altered))
    classNames = f'{"|" if classes else ""}{"|".join(classes)}'

    # Remove old type casting
    for l, line in enumerate(altered.splitlines()):
        wrongCasts = re.findall(rf'((int|float|str|bool|list|tuple|dict|object)\([^)]*\))', line)
        if wrongCasts:
            error('SyntaxError', wrongCasts[0][0], l)

    # Type casting
    for cast in re.findall(rf'(< ?(int|float|str|bool|list|tuple|dict|object{classNames}) ([^>]*) ?>)', altered):
        altered = altered.replace(cast[0], f'{cast[1]}({cast[2]})')

    # Wrong __init__ with return type specified
    wrongInits = re.findall(rf'(class (\w+)(\([^)]*\))?:\n+([\t ]*)func (int|float|str|list|tuple|object|bool|null{classNames}) \2\(([^)]*)\):)', altered)
    if wrongInits:
        error('SyntaxError', wrongInits[0][4], findLine(wrongInits[0][0].split('\n')[-1].strip(), altered), 'Class constructors should not return anything')

    # Correct __init__ adding return type
    replInits = re.findall(rf'(class (\w+)(\([^)]*\))?:(\n+[\t ]*)func \2\(([^)]*)\):)', altered)
    for repl in replInits:
        altered = altered.replace(repl[0], f'class {repl[1]}{repl[2]}:{repl[3]}func null {repl[1]}({repl[4]}):')

    # Functions
    functions = re.findall(rf'(( *)func +(null|int|float|str|bool|bytes|list|tuple|dict|object{classNames}) +([a-zA-Z][a-zA-Z0-9_]*)\(([^)]*)\):)' , altered)
    for func in functions:
        altered = altered.replace(func[0], f'{func[1]}def {func[3]}({func[4]}, *_: object) -> {func[2] if func[2] != "null" else "None"}:\n{func[1]}    globals().update(locals())')

    # Variable types
    for l, line in enumerate(altered.splitlines()):
        variables = [list(found) for found in re.findall(rf'((int|float|str|bool|list|tuple|dict|object{classNames}): *(\w+) *= *([^;]+);)', line)]
        for variable in variables:
            altered = altered.replace(variable[0], f'variable("{variable[2]}", "{variable[3]}", {l}, "{variable[1]}")')

    # Plain var declarations
    for l, line in enumerate(altered.splitlines()):
        plainVars = re.findall(r'((?<!.)(\w+) *= *(\S*);)', line)
        for plain in plainVars:
            altered = altered.replace(plain[0], f'variable("{plain[1]}", "{plain[2]}", {l})')

    # __init__ keyword errors
    wrongInits = re.findall(r'(class (\w+)(\([^)]*\))?:\n[\t ]*func __init__(\([^)]*\)):)', altered)
    if wrongInits:
        error('SyntaxError', f'__init__', findLine('__init__', altered))

    # Replacing constructor with __init__
    inits = re.findall(rf'(class (\w+)(\([^)]*\))?:\n+([\t ]*)def \2\(([^)]*)\) *-> *(int|float|str|list|tuple|object|bool|None{classNames}) *:)', altered)
    for init in inits:
        altered = altered.replace(init[0], f'class {init[1]}{init[2]}:\n{init[3]}def __init__(self, {init[4]}) -> {init[5] if init[5] != "null" else "None"}:')

    # Final return checks
    for l, line in enumerate(altered.splitlines()):
        funcReturns = re.findall(r'(((?:\t| {4})*)return ([^;]*);)', line)
        # 0 = full phrase, 1 = full whitespace, 2 = returning phrase
        for funcReturn in funcReturns:
            # Prevent all similar returns from being incorrectly replaced
            altered = '\n'.join([*altered.splitlines()[:l], f'{funcReturn[1]}return returnCheck({funcReturn[2]}, {funcUpType(l, altered)}, {l})', *altered.splitlines()[l + 1:]])

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
    altered = altered + '\n' if altered[-1] != '\n' else altered
    altered = altered.replace(';\n', '\n')

    return altered, env

def run(code: str, enviroment: dict, apricode: str):
    ERRORS = {FileNotFoundError: 'FileError', FileExistsError: 'FileError'}

    try:
        exec(code, enviroment)
    except Exception as e:
        # Traceback info
        tb = traceback.extract_tb(e.__traceback__)[-1]
        l = tb[1]

        # Pull classes to use for rest of code
        classes = ['pointer', 'function']
        classes.extend(re.findall(r'class (\w+)(?:\(.*\))? ?:', code))
        classNames = f'{"|" if classes else ""}{"|".join(classes)}'

        # Puffing apricode to match compiled lines
        puffed = apricode
        for func in re.findall(rf'(( *)func +(null|int|float|str|bool|bytes|list|tuple|dict|object{classNames}) +([a-zA-Z][a-zA-Z0-9_]*)\(([^)]*)\):)', apricode):
            puffed = puffed.replace(func[0], f'{func[0]}\n//')

        # Subtract by the number of added lines
        line = getline(l, puffed)
        l = findLine(line, apricode)
        error(type(e).__name__, line, l, line=line)


if __name__ == '__main__':
    # Get file path
    # Apricot py/exe, filepath of .apr, flags such as -e or -w, filepath of compiled file for -w
    filepath = sys.argv[1]
    folder = os.path.dirname(sys.argv[1])

    # Global var setup
    strings = []
    varTypes = {}
    classes = []

    # Read and compile the code file
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        code = f.read()

    # Compile and report time
    start = time.time()
    compiled, env = apricompile(code)
    print(f'{C.CYAN}Compiled {os.path.basename(sys.argv[1])} in {fime(time.time() - start, "s")}\n{C.RESET}')

    # Execute the compiled code
    if '-e' in sys.argv:
        start = time.time()
        run(compiled, env, code)
        print(f'\n{C.CYAN}Ran {os.path.basename(sys.argv[1])} in {fime(time.time() - start, "s")}\n{C.RESET}')

    # Write the compiled code to a file if specified by -w option
    if '-w' in sys.argv:
        with open(sys.argv[sys.argv.index('-w') + 1], 'w') as f:
            f.write(compiled)

    input('Press enter to exit.')

# Executable command: pyinstaller --onefile --icon="C:\Users\nekta\Downloads\apricot.png" --distpath="C:\Program Files\Apricot" Apricot.py
# Executable run: Apricot -p C:\Users\nekta\PycharmProjects\Apricot\code.apr -e
