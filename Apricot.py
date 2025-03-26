import sys
import time
from Colors import ColorText as C
from Compiler import Compiler
from Library import *
from Cache import CacheLoader


if __name__ == '__main__':
    # Global var setup
    strings = []
    varTypes = {}
    classes = []
    constants = {}
    altered = ''

    # Cache loading
    cached, snapshots, regexes = CacheLoader.load()

    # Read and compile the code file
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        code = f.read()

    # Compile and report time
    start = time.time()
    for snap in snapshots:
        if snap.compare(code):
            compiled = snap.grab()
            _, env, snapshot = Compiler.apricompile('', cached)
            print(f'{C.CYAN}Uncached ".cache\\_cache_.pkl" [{round(time.time() - start, 4) * 1000:.1f} ms]\n{C.RESET}')
            break
    else:
        # Compilation
        compiled, env, snapshot = Compiler.apricompile(code, cached)

        # Messages
        if compiled[-1] == '\x05':
            print(f'{C.CYAN}Skipping execution of internal code [{round(time.time() - start, 4) * 1000:.1f} ms]\n{C.RESET}')
        else:
            print(f'{C.CYAN}Compiled {os.path.basename(sys.argv[1])} [{round(time.time() - start, 4) * 1000:.1f} ms]\n{C.RESET}')

    # Execute the compiled code
    if '-e' in sys.argv and compiled[-1] != '\x05':
        start = time.time()
        exec(compiled, env, env)
        print(f'\n{C.CYAN}Ran {os.path.basename(sys.argv[1])} [{round(time.time() - start, 4) * 1000:.1f} ms]\n{C.RESET}')

    # Caching
    CacheLoader.store(cached, snapshot)

    # Write the compiled code to a file if specified by -w option
    if '-w' in sys.argv:
        with open(sys.argv[sys.argv.index('-w') + 1], 'w') as f:
            f.write(compiled)

    input('Press enter to exit.')
