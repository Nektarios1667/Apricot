import inspect
import sys
import time
from typing import Callable

import Cache
from Compiler import Compiler
import os
from Cache import CacheLoader
import Library
import Packager
from Pointers import Pointer
from Text import ColorText as C
import Packager
import Functions as F

def main():
    # Setup
    env = {'Function': Callable, 'log': Compiler.log, 'load': Compiler.load, 'Pointer': Pointer, 'variable': Compiler.variable, 'null': None, 'true': True, 'false': False}

    # Time
    start = time.perf_counter()

    # Read and compile the code file
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        code = f.read()
        Compiler.code = code

    # Load cache
    cache = CacheLoader.find(code)
    if "-nocache" not in sys.argv and cache is not None:
        # Load
        compiled, consts = cache.compiled, cache.consts
        caching = None
        env["_constants"] = cache.consts

        # Load warnings
        for warning in cache.warnings:
            Compiler.warn(*warning)
        # Print uncache
        print(f'{C.CYAN}Uncached ".cache\\_cache_.pkl" [{(time.perf_counter() - start) * 1000:.1f} ms]\n{C.RESET}')

    # Recompile
    else:
        compiled, caching, consts = Compiler.compile(code)
        env["_constants"] = consts
        print(f'{C.CYAN}Compiled {os.path.basename(sys.argv[1])} [{(time.perf_counter() - start) * 1000:.1f} ms]\n{C.RESET}')

    # Write the compiled code to a file if specified by -w option
    if '-w' in sys.argv:
        output = compiled
        # If embedded
        if '-s' in sys.argv:
            # Setup
            imports = ['re', 'sys', 'os', 'time', 'pickle', 'typing.Callable']
            embeds = [*Packager.getMethods(Compiler), F.getLine, F.searchLine, Library, C, Cache.Snapshot, Cache.CacheLoader, Pointer]
            repl = {'Compiler.': '', 'F.': '', 'Cache.': '', 'C.': 'ColorText.', 'folder = os.path.dirname(sys.argv[1])': 'folder = os.path.dirname(sys.argv[0])'}
            headers = [f'_constants = {consts}', 'Function = Callable', 'with open(rf"{sys.argv[0]}", "r") as f:\n\tcode = f.read()']

            # Embedded
            output = Packager.standalone(imports, headers, embeds, compiled, replacements=repl, removals=["@staticmethod"])
        with open(sys.argv[sys.argv.index('-w') + 1], 'w') as f:
            f.write(output)

    # Execute the compiled code
    if '-e' in sys.argv:
        start = time.perf_counter()
        exec(compiled, env, env)
        print(f'\n{C.CYAN}Ran {os.path.basename(sys.argv[1])} [{(time.perf_counter() - start) * 1000:.1f} ms]\n{C.RESET}')

    # Caching
    if "-nocache" not in sys.argv and caching is not None:
        CacheLoader.store(caching)

    input('Press enter to exit.')

# Entry
if __name__ == '__main__':
    main()
