import re
from typing import Callable
from Pointers import Pointer
from Compiler import Compiler


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

defaultEnv = {'Function': Callable, 'log': log, 'load': Compiler.load, 'Pointer': Pointer, 'variable': Compiler.variable, 'null': None, 'true': True, 'false': False}
defaultEnvValues = ["Callable", "print", "Compiler.load", "Pointer", "Compiler.variable", "None", "True", "False"]
