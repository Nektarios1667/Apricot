import inspect
import re
import sys
import types

import Cache
from Classes import *
import Functions as F
import Regex as R
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
            Compiler.log(f'{C.RED}{error}: "{line.strip()}" - "{description.strip()}" @ line {l}\n{extra}{C.RESET}' + ("\n" if extra else ""))
        else:
            Compiler.log(f'{C.RED}{error}: "{line.strip()}" @ line {l}\n{extra}{C.RESET}' + ("\n" if extra else ""))
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
    def typeCheck(value, check, l):
        if check is NoType:
            return True
        elif isinstance(check, types.FunctionType):
            return Compiler.call(check, [value], l)
        else:
            return isinstance(value, check)

    @staticmethod
    def call(func, args, l):
        # Builtin
        if func.__module__ == "builtins":
            return func(*args)

        # Check params
        a = 0
        for paramName, param in inspect.signature(func).parameters.items():
            if param.annotation is inspect._empty:
                funcLine = [l for l, line in enumerate(Compiler.code.splitlines()) if line.strip().startswith("func") or line.strip().startswith("type") and func.__name__ in line][0]
                Compiler.error("SyntaxError", funcLine + 1, description=f"{paramName}", extra="Argument missing type")

            if len(args) - 1 >= a and not Compiler.typeCheck(args[a], param.annotation, l):
                Compiler.error("ArgumentError", l + 1, description=f"{args[a]}", extra=f"Argument '{paramName}' expected -{param.annotation.__name__}- but -{type(args[a]).__name__}- was given")
            a += 1

        # Call func
        return func(*args)

    @staticmethod
    def giveback(value, returnType, l):
        if Compiler.typeCheck(value, returnType, l):
            return value
        else:
            Compiler.error('TypeError', l + 1, extra=f'Expected -{returnType.__name__}- but -{type(value).__name__}- was returned')

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
        env = {'Compiler.log': print, 'load': Compiler.load, 'Pointer': Pointer, 'variable': Compiler.variable, 'giveback': Compiler.giveback, 'null': None, 'true': True, 'false': False}
        compiled, _, _ = Compiler.compile(code, main=False)

        try:
            exec(compiled, env)
        except Exception as e:
            Compiler.error('LibraryError', e.__traceback__.tb_lineno - 1, extra=f'Error occurred during library execution')

        # Clean globals
        for var, val in dict(env).items():
            if callable(val):
                setattr(library, var, val)

        return {name:library}

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
            elif not Compiler.typeCheck(value, varType, l):
                Compiler.error('TypeError', l + 1, extra=f'Variable type defined as -\x1a{varType.__name__}\x1a- but value is -\x1a{type(value).__name__}\x1a-', description=str(value))
            else:
                env['_varTypes'][name] = varType
        else:
            if name in constants:
                Compiler.error('VariableError', l + 1, extra=f'Variable "{name}" is already a constant', description=name)
            elif name not in env:
                Compiler.error('VariableError', l + 1, extra=f'Variable "{name}" has not yet been created', description=name)
            elif not Compiler.typeCheck(value, env['_varTypes'][name], l):
                Compiler.error('TypeError', l + 1, extra=f'Variable type defined as -\x1a{env["_varTypes"][name].__name__}\x1a- but value is -\x1a{type(value).__name__}\x1a-', description=str(value))

        env[name] = value

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
    def compile(code: str, main: bool = True):
        """
        Compiles Apricot code into Python code. Returns the compiled code, a cache, and any constants.
        :param main:
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
        if main: Compiler.code = code
        compiled = code

        # String replacements
        strings = []
        for s, string in enumerate(re.findall(R.STRINGS, compiled)):
            compiled = compiled.replace(string[0], f'\x1a={s}')
            strings.append(string[0])

        # Semicolons
        for l, line in enumerate(compiled.splitlines()):
            # Strip whitespace
            line = line.strip()

            # Comments and empty lines
            if line == '' or re.match(R.INLINECOMMENTS, line):
                continue

            if line.strip()[-1] not in [':', ';']:
                warning = Compiler.warn('EOLError', l + 1, extra="Missing end of line marker")
                warnings.append(warning)

        # Comments
        for comm in re.findall(R.COMMENTS, compiled):
            compiled = compiled.replace(comm, '# There was a comment...')

        # Syntax keyword errors
        for l, line in enumerate(compiled.splitlines()):
            for syn in R.SYNTAX:
                found = re.findall(re.escape(syn), line)
                if found:
                    Compiler.error('SyntaxError', l + 1, description=found[0], extra="Bad phrase.")

        # Syntax phrase errors
        for l, line in enumerate(compiled.splitlines()):
            for syn in R.SYNTAXPHRASES:
                found = re.findall(syn, line)
                if found:
                    Compiler.error('SyntaxError', l + 1, description=found[0], extra="Bad phrase.")

        # Name errors
        for l, line in enumerate(compiled.splitlines()):
            for syn in R.NAMEERRORS:
                found = re.findall(syn, line)
                if found:
                    Compiler.error('NameError', l + 1, description=found[0], extra='Function {found[0]} not defined.')

        # Class declarations
        for l, line in enumerate(compiled.splitlines()):
            for cls in re.findall(R.CLASSES, line):
                compiled = compiled.replace(line, f'class {cls[0]}({cls[1]}):')

        # Class blocks
        for b, block in enumerate(re.findall(R.CLASSBLOCKS, compiled)):
            newBlock = block
            for func in re.findall(R.METHODS, block):
                newBlock = newBlock.replace(func[0], f'{func[1]}func {func[2]} {func[3]}(this{", " if func[4] else ""}{func[4]}):')
            compiled = compiled.replace(block, newBlock)

        # Remove old type casting
        for l, line in enumerate(compiled.splitlines()):
            wrongCasts = re.findall(R.WRONGCASTS, line)
            if wrongCasts:
                Compiler.error('SyntaxError', l + 1, description=wrongCasts[0][0])

        # Type casting
        for cast in re.findall(R.CASTING, compiled):
            compiled = compiled.replace(cast[0], f'{cast[1]}({cast[2]})')

        # Wrong __init__ with return type specified
        wrongInits = re.findall(R.WRONGINITSRETURNS, compiled)
        if wrongInits:
            Compiler.error('SyntaxError', wrongInits[0][4], F.searchLine(wrongInits[0][0].split('\n')[-1].strip(), compiled), 'Class constructors should not return anything')

        # Correct __init__ adding return type
        replInits = re.findall(R.INITS, compiled)
        for repl in replInits:
            compiled = compiled.replace(repl[0], f'{repl[1]}class {repl[2]}{repl[3]}:{repl[4]}func null {repl[2]}({repl[5]}):')

        # Constants
        for l, line in enumerate(compiled.splitlines()):
            for full, name, value in re.findall(R.CONSTS, line):
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
            variables = [list(found) for found in re.findall(R.VARS, line)]
            for variable in variables:
                compiled = compiled.replace(variable[0], f'variable("{variable[2]}", {variable[3]}, {l}, globals(), {variable[1]})')

        # Plain var declarations
        for l, line in enumerate(compiled.splitlines()):
            plainVars = re.findall(R.PLAINVARS, line)
            for plain in plainVars:
                compiled = compiled.replace(plain[0], f'variable("{plain[1]}", {plain[2]}, {l}, globals())')

        # Parameter typing
        for typeHint in re.findall(R.PARAMETERS, compiled):
            compiled = compiled.replace(typeHint[0], f'{typeHint[2]}: {typeHint[1]}')

        # Function calls with arguments
        while True:
            # Repeat until not found anymore for nested calls
            found = False
            for l, line in enumerate(compiled.splitlines()):
                # Skip function definitions since they look similar
                if re.search(R.CLASSFUNC, line):
                    continue

                # Find
                calls = re.findall(R.CALLS, line)
                found = bool(calls)
                for call in calls:
                    compiled = compiled.replace(call[0], f'call({call[1]}{call[2]}, ({call[3]},), {l})')
            if not found:
                break

        # Function returns
        current = ''
        for l, line in enumerate(compiled.splitlines()):
            # Get function or method
            func = re.match(R.SIMPLEFUNCS, line.strip())
            if func:
                current = func.group(1)
                continue
            elif re.match(R.TYPEPREDICATES, line.strip()):
                current = ''
            returning = re.match(R.RETURNS, line.strip())
            if returning and current:
                compiled = compiled.replace(returning[0], f'return giveback({returning[1]}, {current}, {l})')

        # Functions
        functions = re.findall(R.FUNCS, compiled)
        for func in functions:
            compiled = compiled.replace(func[0], f'{func[1]}def {func[3]}({func[4]}{", " if func[4] else ""}) -> {func[2] if func[2] != "null" else "None"}:')

        # Type predicates
        typePredicates = re.findall(R.TYPEPREDICATES, compiled)
        for pred in typePredicates:
            compiled = compiled.replace(pred[0], f'def {pred[1]}(value: NoType) -> bool:')

        # __init__ keyword errors
        wrongInits = re.findall(R.WRONGINITS, compiled)
        if wrongInits:
            Compiler.error('SyntaxError', F.searchLine('__init__', compiled))

        # Replacing constructor with __init__
        inits = re.findall(R.CONSTRUCTOR, compiled)
        for init in inits:
            compiled = compiled.replace(init[0], f'class {init[1]}{init[2]}:\n{init[3]}def __init__(self{", " if init[4] else ""}{init[4]}) -> {init[5] if init[5] != "null" else "None"}:')

        # Switch replacements
        for apr, py in R.DIRECT.items():
            for found in re.findall(apr, compiled):
                filledPy = py
                for p, part in enumerate(found):
                    filledPy = filledPy.replace(f'\x1a:{p}', part)

                compiled = compiled.replace(found[0], filledPy)

        # Switch phrase replacements
        for apr, py in R.DIRECTPHRASES.items():
            compiled = re.sub(apr, py, compiled)

        # Inject strings
        for f, fill in enumerate(strings):
            compiled = compiled.replace(f'\x1a={f}', fill)

        # Automatic error handling wrap
        # compiled = f'try:\n' + '\n'.join([f'\t{line}' for line in compiled.splitlines()]) + '\nexcept Exception as e:\n\timport traceback\n\terror(type(e).__name__, e.__traceback__.tb_lineno - 2)'

        # Setup
        compiled = f'{compiled}\n'
        # Remove semicolons
        compiled = compiled.replace(';\n', '\n')

        # Cache
        cache = Cache.Snapshot()
        cache.save(code, compiled, constants, warnings)
        if main: Compiler.compiled = compiled

        return compiled, cache, constants
