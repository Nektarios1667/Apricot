from io import StringIO
from math import floor
import re
from colored import Fore, Style
from typing import Literal, get_type_hints

def inject(phrase: str):
    for f, fill in enumerate(strings):
        phrase = phrase.replace(f'\x1a@{f}', fill)
    return phrase

def error(error: str, description: str, line: str, row: int | Literal["N/A"], extra: str = ''):
    print(f'{Fore.RED}{error}: "{inject(line)}" - "{inject(description)}" @ line {row}\n{extra}{Style.RESET}')
    exit(-1)

def tyval(value):
    if value[0] == '\x1a':
        return str

    return type(eval(value))

def findLine(phrase: str, paragraph: str):
    lines = paragraph.splitlines()
    for i, line in enumerate(lines):
        if phrase in line:
            return i + 1
    return "N/A"

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

def funcCheck(func: tuple, altered: str):
    # Line number
    defLine = findLine(func[0], altered) - 1

    # Indents
    indented = indents(func[0])

    # Function text
    function = func[0]
    for l, line in enumerate(altered.splitlines()[defLine + 1:]):  # Defline starts on definition so add oen to start with actual content
        if indents(line) <= indented:
            break
        else:
            function += f'\n{line}'

    # Execute function to add to globals
    exec(function, globals())
    call = globals()[func[1]]

    # Check return type hint
    expected = get_type_hints(call).get('return', None)

    # Function lines
    for l, line in enumerate(function.splitlines()[1:]):  # Defline starts on definition so add oen to start with actual content
        if indents(line) <= indented:
            break
        elif line.strip()[:6] == 'return' and tyval(line.strip()[6:-1]).__name__ != expected.__name__:
            error('TypeError', line.strip(), line.strip()[6:-1].strip(), l, f'Function return defined as -{tyval(line.strip()[6:-1]).__name__}- but value with type -{expected.__name__}- was returned')


# Code
with open('code.apr', 'r') as f:
    code = f.read()

# Variables
altered = code
varTypes = {}
syntax = [r'def [a-zA-Z][a-zA-Z0-9_]*\([^)]*\)', r'def \([^)]*\)']
strings = []

# Void buffer
voidIO = StringIO

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
        errors = re.findall(syn, line)
        if errors:
            error('SyntaxError', line, errors[0], l)

# Functions
functions = re.findall(r'(func (null|int|float|str|bool|bytes|list|tuple|dict) ([a-zA-Z][a-zA-Z0-9_]*)\(([^)]*)\):)', altered)
for func in functions:
    altered = altered.replace(func[0], f'def {func[2]}({func[3]}, *_) -> {func[1] if func[1] != "null" else "None"}:')

# Variable types
for l, line in enumerate(altered.splitlines()):
    variables = [list(found) for found in re.findall(r'((\w+): ?(int|float|str|bool|list|tuple|dict|var) ?= ?([^;]+))', line)]
    for variable in variables:
        if variable[1] in varTypes.keys():
            error('NameError', line.strip(), variable[1], l, f'Variable with name "{variable[1]}" already created')

        if variable[2] == 'var':
            variable[2] = tyval(variable[3]).__name__
            altered = altered.replace(variable[0], f'{variable[1]}: {variable[2]} = {variable[3]}')

        if tyval(variable[3]) is not eval(variable[2]):
            error('TypeError', line.strip(), variable[0], l, f'Variable type defined as -{variable[2]}- but value is -{tyval(variable[3]).__name__}-')

        varTypes[variable[1]] = tyval(variable[3])

# Plain var declarations
for l, line in enumerate(altered.splitlines()):
    plainVars = re.findall(r'((?<!.)(\w+) ?= ?(\S*))', line)
    for plain in plainVars:
        if plain[1] not in varTypes.keys():
            error('VariableError', plain[1], line.strip(), l, 'Variable assignment before creation')
        elif tyval(plain[2][:-1]) is not varTypes[plain[1]]:
            error('TypeError', line.strip(), plain[0], l, f'Variable type defined as -{varTypes[plain[1]].__name__}- but value is -{tyval(plain[2][:-1]).__name__}-')

# Wrong __init__
wrongInits = re.findall(r'(class (\w+)(\([^)]*\))?:\n[\t ]*func __init__(\([^)]*\)):)', altered)
if wrongInits:
    error('SyntaxError', f'func __init__{wrongInits[0][3]}', f'__init__', findLine('__init__', altered))

# Fixing __init__
inits = re.findall(r'(class (\w+)(\([^)]*\))?:\n[\t ]*func \2(\([^)]*\)):)', altered)
for init in inits:
    altered = altered.replace(init[0], f'class {init[1]}{init[2]}:\n    def __init__{init[3]}:')

# Final type checks
functions = re.findall(r'(def ([a-zA-Z][a-zA-Z0-9_]*)(\([^)]*\)) -> (None|int|float|str|bool|list|tuple|dict):)', altered)
for func in functions:
    funcCheck(func, altered)

# Inject strings
for f, fill in enumerate(strings):
    altered = altered.replace(f'\x1a@{f}', fill)

exec(altered)
