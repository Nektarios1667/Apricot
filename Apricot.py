import sys
import time
from Colors import ColorText as C
from Compiler import Compiler
from Library import *
from Cache import CacheLoader
import Builtins

def main():
    global code
    # Setup
    env = Builtins.defaultEnv

    # Time
    start = time.perf_counter()

    # Read and compile the code file
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        code = f.read()
        Builtins.setCode(code)

    # Load cache
    cache = CacheLoader.find(code)
    if "-nocache" not in sys.argv and cache is not None:
        compiled = cache.apricode
        caching = None
        env["_constants"] = cache.consts
        print(f'{C.CYAN}Uncached ".cache\\_cache_.pkl" [{(time.perf_counter() - start) * 1000:.1f} ms]\n{C.RESET}')
    # Recompile
    else:
        compiled, caching, consts = Compiler.apricompile(code)
        env["_constants"] = consts
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

# Entry
if __name__ == '__main__':
    main()
