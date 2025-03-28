import sys
import time
from Colors import ColorText as C
from Compiler import Compiler
from Library import *
from Cache import CacheLoader
from Pointers import Pointer

if __name__ == '__main__':
    # Global var setup
    strings = []
    varTypes = {}
    classes = []
    constants = {}
    altered = ''
    env = {'log': print, 'load': Compiler.load, 'Pointer': Pointer, 'variable': Compiler.variable, 'null': None, 'true': True, 'false': False}

    # Time
    start = time.perf_counter()

    # Read and compile the code file
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        code = f.read()

    # Load cache
    cache = CacheLoader.find(code)
    if "-nocache" not in sys.argv and cache is not None:
        compiled = cache.apricode
        caching = None
        print(f'{C.CYAN}Uncached ".cache\\_cache_.pkl" [{(time.perf_counter() - start) * 1000:.1f} ms]\n{C.RESET}')
    # Recompile
    else:
        compiled, caching = Compiler.apricompile(code)
        print(f'{C.CYAN}Compiled {os.path.basename(sys.argv[1])} [{(time.perf_counter() - start) * 1000:.1f} ms]\n{C.RESET}')

    # Write the compiled code to a file if specified by -w option
    if '-w' in sys.argv:
        with open(sys.argv[sys.argv.index('-w') + 1], 'w') as f:
            f.write(compiled)

    # Execute the compiled code
    if '-e' in sys.argv:
        start = time.perf_counter()
        exec(compiled, env, env)
        print(f'\n{C.CYAN}Ran {os.path.basename(sys.argv[1])} [{(time.perf_counter() - start) * 1000:.1f} ms]\n{C.RESET}')

    # Caching
    if "-nocache" not in sys.argv and caching is not None:
        CacheLoader.store(caching)

    input('Press enter to exit.')
