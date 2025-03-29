import types
import os
import re
import sys
from typing import Callable
from Library import Library
from Pointers import Pointer
from Colors import ColorText as C

def inject(phrase: str):
    """
    Injects all strings into phrase by replacing \x1a@{#} with the index in the string list.
    :param phrase:
    :return:
    """
    from Compiler import strings

    phrase = str(phrase)
    for f, fill in enumerate(strings):
        phrase = phrase.replace(f'\x1a@{f}', fill)
    return phrase

def error(error: str, description: str, l: int, extra: str = '', line: str = ''):
    from Compiler import altered

    # If line isn't specified find automatically
    line = line or "N/A"

    # Printing and closing
    log(f'{C.RED}{error}: "{inject(line.strip())}" - "{inject(description.strip())}" @ line {l}\n{extra}{C.RESET}')

    if '-w' in sys.argv:
        with open(sys.argv[sys.argv.index('-w') + 1], 'w') as f:
            f.write(altered)

    sys.exit(-1)

def warn(warning: str, description: str, l: int, extra: str = '', line: str = ''):
    # If line isn't specified find automatically
    line = line or "N/A"
    # Printing and closing
    log(f'{C.YELLOW}{warning}: "{inject(line.strip())}" - "{inject(description.strip())}" @ line {l}\n{extra}{C.RESET}')


def getLine(line: int, code: str):
    """
    Gets the line based on the index. Note: the line numbers start at 1.
    :param line:
    :param code:
    :return:
    """
    # Double lines
    while "\n\n" in code:
        code = code.replace('\n\n', '\n//\n')

    # Return
    lines = code.splitlines()
    return lines[min(line - 1, len(lines) - 1)]

def load(file: str):
    """
    Loads Apricot Library file and adds functions to enviroment in the corresposding module.
    :param file:
    :return:
    """
    from Compiler import Compiler

    # Get file path
    folder = os.path.dirname(sys.argv[1])

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
        for allow in allowed:
            if line.startswith(allow):
                break

        else:
            error('LibraryError', line, l + 1)

    # Running
    env = {'log': print, 'load': load, 'Pointer': Pointer, 'variable': variable, 'null': None, 'true': True, 'false': False}
    compiled, _, _ = Compiler.apricompile(code)
    exec(compiled, env)

    # Clean globals
    for var, val in dict(env).items():
        if callable(val):
            setattr(library, var, val)

    return {name: library}


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
    from Compiler import altered

    constants = env["_constants"]
    line = getLine(l + 1, altered)

    # value = eval(value, env)
    if varType:
        varType = eval(varType, env)

        if name in env:
            warn('VariableError', name, l + 1, extra=f'Variable "{name}" is already created', line=line)
        elif name in constants:
            error('VariableError', name, l + 1, extra=f'Variable "{name}" is already a constant', line=line)
        elif not isinstance(value, varType):
            error('TypeError', str(value), l + 1, extra=f'Variable type defined as -\x1a{varType.__name__}\x1a- but value is -\x1a{type(value).__name__}\x1a-', line=line)
    else:
        if name in constants:
            error('VariableError', name, l + 1, extra=f'Variable "{name}" is already a constant', line=line)
        elif name not in env:
            error('VariableError', name, l + 1, extra=f'Variable "{name}" has not yet been created', line=line)
        elif not isinstance(value, type(env[name])):
            error('TypeError', str(value), l + 1, extra=f'Variable type defined as -\x1a{type(env[value])}\x1a- but value is -\x1a{type(value).__name__}\x1a-', line=line)

    try:
        env[name] = value
    except Exception as e:
        error('CompilationError', 'An error occurred during compilation', l + 1)


def log(*values: object, sep: str | None = "\n", end : str | None = "\n", flush: bool = False):
    values = [str(value) for value in values]

    # Replace type mentions
    for v, value in enumerate(values):
        for repl in re.findall(r'\x1a(\w+)\x1a', str(value)):
            # Check if it needs a replacement
            if repl not in defaultEnvValues:
                values[v] = values[v].replace(f'\x1a{repl}\x1a', repl)
                continue

            # Replace
            values[v] = values[v].replace(f'\x1a{repl}\x1a', list(defaultEnv.keys())[defaultEnvValues.index(repl)])

    # Print
    print(*values, sep=sep, end=end, flush=flush)

defaultEnv = {'Function': Callable, 'log': log, 'load': load, 'Pointer': Pointer, 'variable': variable, 'null': None, 'true': True, 'false': False}
defaultEnvValues = ["Callable", "print", "Compiler.load", "Pointer", "Compiler.variable", "None", "True", "False"]
