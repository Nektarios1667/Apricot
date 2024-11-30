import time
import traceback
import types
from Colors import ColorText as C
import os
from Pointers import *
from Library import *
import sys
import re


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


def error(error: str, description: str, l: int, extra: str = '', line: str = ''):
    global altered

    # If line isn't specified find automatically
    line = line if line else getline(l, code)

    # Printing and closing
    print(f'{C.RED}{error}: "{inject(line.strip())}" - "{inject(description.strip())}" @ line {l}\n{extra}{C.RESET}')

    if '-w' in sys.argv:
        with open(sys.argv[sys.argv.index('-w') + 1], 'w') as f:
            f.write(altered)

    sys.exit(-1)


def log(val, newline: bool = True):
    print('null' if val is None else val, '\n' if newline else '')


def funcUpType(l: int, paragraph: str):
    for line in paragraph.splitlines()[l::-1]:
        if line.strip().startswith('def '):
            # Find return type annotation and remove whitespace/colon
            funcType = eval(line.split('->')[1][:-1].strip())
            return funcType if funcType is None else funcType.__name__


def tyval(value, env):
    """
    Returns the type of the evaluated string.
    :param env:
    :param value:
    :return:
    """
    global strings

    if value[0] == '\x1a':
        return str
    if '\x1a' in value:
        return tyval(inject(value), env)

    try:
        return type(eval(value, env))
    except:
        return type(env[value])


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
            error('LibraryError', line, l + 1)

    # Running
    compiled, importing = apricompile(code)
    exec(compiled, importing)

    # Clean globals
    for var, val in dict(importing).items():
        if callable(val):
            setattr(library, var, val)

    env.update({name: library})


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

    value = eval(value, env)
    if varType:
        varType = eval(varType, env)

        if name in varTypes:
            error('VariableError', name, l + 1, extra=f'Variable "{name}" is already created')
        elif name in constants:
            error('VariableError', name, l + 1, extra=f'Variable "{name}" is already a constant')
        elif not isinstance(value, varType):
            error('TypeError', str(value), l + 1, extra=f'Variable type defined as -{varType.__name__}- but value is -{type(value).__name__}-')
    else:
        if name in constants:
            error('VariableError', name, l + 1, extra=f'Variable "{name}" is already a constant')
        elif name not in env:
            error('VariableError', name, l + 1, extra=f'Variable "{name}" has not yet been created')
        elif not isinstance(value, type(env[value])):
            error('TypeError', str(value), l + 1, extra=f'Variable type defined as -{type(env[value])}- but value is -{type(value).__name__}-')

    try:
        env[name] = value
    except:
        error('CompilationError', 'An error occurred during compilation', l + 1)

def apricompile(code: str):
    """
    Compiles Apricot code into Python code. Returns the compiled code and a dictionary containing the global enviroment variables. The enviroment variables are used during runtime for the
    compiled seudo-Python code.
    :param code:
    :return:
    """
    global strings, variable, varTypes, altered, constants

    # Variables
    env = {'log': print, 'load': load, 'pointer': pointer, 'variable': variable}
    constants = {}
    altered = code
    varTypes = {}
    strings = []
    direct = {r'(switch ([^:]+):)':            'match \x1a:1:', r'(this\.(\w+))': 'self.\x1a:1', r'(throw (\w+);)': 'raise \x1a:1', r'(catch (.+):)': 'except \x1a:1:',
              r'(for (\w[\w\d_]*) ?: ?(.*):)': 'for \x1a:1 in \x1a:2:', r'(import (.*);)': 'load(".libraries/\x1a:1.apl")', r'(include (\w+);)': 'import \x1a:1',
              r'(using (.*):)':                'with \x1a:1:', r'(span\((.*)\))': 'range(\x1a:1)', r'(@(\w[\w _0-9]*))\b': "pointer('\x1a:1', globals())", r'(\^(\w.*))\b': '\x1a:1.val',
              r'(noop;())':                    'pass'}
    syntax = [*direct.values(), r'__init__([^)]*)', r'lambda \w+: ', r'nonlocal \w+', 'async ', 'await ', 'from .* import .*', 'for .* in .*:', '->']
    # nameErrors = [r'globals\(\)', r'locals\(\)']
    nameErrors = []
    syntaxPhrase = [r'\bFalse\b', r'\bTrue\b']
    directPhrase = {r'\bnull\b': 'None', 'else if': 'elif', 'next;': 'continue', r'\btrue\b': 'True', r'\bfalse\b': 'False'}

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

    # Local variables
    for l, line in enumerate(altered.splitlines()):
        for var in re.findall(r'~[a-zA-Z_][\w_]*', line):
            altered = altered.replace(var, f'locals()["{var[1:]}"]')

    # Name errors
    for l, line in enumerate(altered.splitlines()):
        for syn in nameErrors:
            found = re.findall(syn, line)
            if found:
                error('NameError', found[0], l + 1, extra=f'Function {found[0]} not defined.')

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
            error('SyntaxError', wrongCasts[0][0], l + 1)

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
    functions = re.findall(rf'(( *)func +(null|int|float|str|bool|bytes|list|tuple|dict|object{classNames}) +([a-zA-Z][a-zA-Z0-9_]*)\(([^)]*)\):)', altered)
    for func in functions:
        altered = altered.replace(func[0], f'{func[1]}def {func[3]}({func[4]}, *_: object) -> {func[2] if func[2] != "null" else "None"}:')

    # Variable types
    for l, line in enumerate(altered.splitlines()):
        variables = [list(found) for found in re.findall(rf'((int|float|str|bool|list|tuple|dict|object{classNames}): *(\w+) *= *([^;]+);)', line)]
        for variable in variables:
            altered = altered.replace(variable[0], f'variable("{variable[2]}", "{variable[3]}", {l}, locals(), "{variable[1]}")')

    # Plain var declarations
    for l, line in enumerate(altered.splitlines()):
        plainVars = re.findall(r'((?:\n)([a-zA-Z_][\w_]*) *= *(\S*);)', line)
        for plain in plainVars:
            altered = altered.replace(plain[0], f'variable("{plain[1]}", "{plain[2]}", {l}, locals())')

    # __init__ keyword errors
    wrongInits = re.findall(r'(class (\w+)(\([^)]*\))?:\n[\t ]*func __init__(\([^)]*\)):)', altered)
    if wrongInits:
        error('SyntaxError', f'__init__', findLine('__init__', altered))

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
                error('ConstantError', name, l + 1, f'Cannot change value of constant "{name}"')
            else:
                constants[name] = value
                altered = altered.replace(full, f'# CONST')

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

    return altered, env


def run(code: str, enviroment: dict, apricode: str):
    ERRORS = {FileNotFoundError: 'FileError', FileExistsError: 'FileError'}
    exec(code, enviroment)
    # try:
    #     exec(code, enviroment)
    # except Exception as e:
    #     # Traceback info
    #     tb = traceback.extract_tb(e.__traceback__)[-1]
    #     l = tb[1]
    #
    #     # Get line info
    #     line = getline(l, apricode)
    #
    #     # Apricot error
    #     error(ERRORS.get(type(e), type(e).__name__), line, l)


if __name__ == '__main__':
    # Get file path
    # Apricot py/exe, filepath of .apr, flags such as -e or -w, filepath of compiled file for -w
    filepath = sys.argv[1]
    folder = os.path.dirname(sys.argv[1])

    # Global var setup
    strings = []
    varTypes = {}
    classes = []
    constants = {}
    altered = ''

    # Read and compile the code file
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        code = f.read()

    # Compile and report time
    start = time.time()
    compiled, env = apricompile(code)
    print(f'{C.CYAN}Compiled {os.path.basename(sys.argv[1])} in {round(time.time() - start, 4) * 1000:.1f} ms\n{C.RESET}')

    # Execute the compiled code
    if '-e' in sys.argv:
        start = time.time()
        run(compiled, env, code)
        print(f'\n{C.CYAN}Ran {os.path.basename(sys.argv[1])} in {round(time.time() - start, 4) * 1000:.1f} ms\n{C.RESET}')

    # Write the compiled code to a file if specified by -w option
    if '-w' in sys.argv:
        with open(sys.argv[sys.argv.index('-w') + 1], 'w') as f:
            f.write(compiled)

    input('Press enter to exit.')

# Executable command: pyinstaller --onefile --icon="C:\Users\nekta\Downloads\apricot.png" --distpath="C:\Program Files\Apricot" Apricot.py
# Executable run: Apricot -p C:\Users\nekta\PycharmProjects\Apricot\code.apr -e

"""Currently trying to get local variables. The problem is locals() is impossible to edit. I have tried executing it but it isn't correctly updating locals(). Sometimes it may seem like it works
such as when using return, but this is because some functions are my builtin functions which handle it better. I can't replace the code because I would have to reexecute, which I haven't tried
yet but it would not work well running a user's scipt twice. There are some quick fixes of using globals(), but this would remove scopes entirely. I could also remove the built-in variable
creation function, but that would remove a main part of Apricot. Maybe I could use some library to type check but this probably doesn't exist in a way I could use.

My current fix is to require the user to put ~var before local variables then use the compiler to replace it with globals()[var]. This actually works very well and the variables are not 
accesable outside of the scope. THe ~ isn't needed for the return function.
"""
