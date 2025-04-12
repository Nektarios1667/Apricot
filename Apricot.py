import inspect
import os
import sys
import time
from typing import Callable

import requests

import Cache
from Cache import CacheLoader
from Compiler import Compiler
import Functions as F
import Library
import Packager
from Pointers import Pointer
from Text import ColorText as C

DEFAULTENV = {'inspect': inspect, 'Function': Callable, 'log': Compiler.log, 'error': Compiler.error, 'load': Compiler.load, 'call': Compiler.call, 'Pointer': Pointer, 'variable': Compiler.variable, 'giveback': Compiler.giveback, 'null': None, 'true': True, 'false': False}

def compileCode(standalone: bool):
    # Setup
    env = DEFAULTENV

    # Time
    start = time.perf_counter()

    # Read and compile the code file
    with open(sys.argv[2], 'r', encoding='utf-8') as f:
        code = f.read()

    # Load cache
    cache = CacheLoader.find(code)
    if "--nocache" not in sys.argv and cache is not None:
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
        print(f'{C.CYAN}Compiled {os.path.basename(sys.argv[2])} [{(time.perf_counter() - start) * 1000:.1f} ms]\n{C.RESET}')

    # Write the compiled code to a file
    # Embed if specified
    compiled = f'_constants = {consts}\n{compiled}'
    if standalone:
        imports = ['inspect', 're', 'sys', 'os', 'time', 'pickle', 'typing.Callable']
        embeds = [*Packager.getMethods(Compiler), F.getLine, F.searchLine, Library, C, Cache.Snapshot, Cache.CacheLoader, Pointer]
        repl = {'Compiler.': '', 'F.': '', 'Cache.': '', 'C.': 'ColorText.', 'folder = os.path.dirname(sys.argv[1])': 'folder = os.path.dirname(sys.argv[0])'}
        headers = [f'_constants = {consts}', 'Function = Callable', 'with open(rf"{sys.argv[0]}", "r") as f:\n\tcode = f.read()']

        compiled = Packager.standalone(imports, headers, embeds, compiled, replacements=repl, removals=["@staticmethod"])

    # Write
    if sys.argv[1] in ['compile', 'standalone']:
        with open(sys.argv[3], 'w') as f:
            f.write(compiled)
    elif '-w' in sys.argv:
        with open(sys.argv[sys.argv.index('-w') + 1], 'w') as f:
            f.write(compiled)

    # Caching
    if "--nocache" not in sys.argv and caching is not None:
        CacheLoader.store(caching)

    # Returning
    return compiled, env

def execute(code: str, env: dict = None):
    start = time.perf_counter()
    env = env or DEFAULTENV
    exec(code, env, env)
    print(f'\n{C.CYAN}Ran {os.path.basename(sys.argv[0])} [{(time.perf_counter() - start) * 1000:.1f} ms]\n{C.RESET}')

    input("Press any key to exit.")


def uncache():
    os.makedirs(sys.argv[2], exist_ok=True)

    for s, snapshot in enumerate(CacheLoader.load()):
        with open(f'{sys.argv[2]}/snapshot_code-{s}.apr', 'w') as f:
            f.write(snapshot.code)
        with open(f'{sys.argv[2]}/snapshot_compiled-{s}.apy', 'w') as f:
            f.write(snapshot.compiled)

def run():
    compiled, env = compileCode(False)
    execute(compiled, env)

def requireArgs(least: int, most: int):
    if len(sys.argv) < least:
        raise ValueError(f"Expected at least {least} arguments")
    elif len(sys.argv) > most:
        raise ValueError(f"Expected at most {most} arguments")

def fetchRegistry():
    resp = requests.get('https://raw.githubusercontent.com/Nektarios1667/Apricot-Library-Registry/refs/heads/main/registry.json')
    if not resp.ok:
        raise Exception(f"Failed to fetch registry: {resp.status_code}")
    return resp.json()

def install():
    registry = fetchRegistry()
    libraryId = registry[sys.argv[2]]['id']

    resp = requests.get(f'https://api.github.com/gists/{libraryId}')
    if resp.ok:
        data = resp.json()
        for name, lib in data["files"].items():
            with open(f'.libraries\\{name}', 'w') as f:
                f.write(lib['content'])
    else:
        print("Failed to fetch library")


def main():
    # Empty
    if len(sys.argv) < 2:
        sys.argv = [sys.argv[0], *input("Enter command:").split(' ')]

    # Commands
    if sys.argv[1] == "compile":
        requireArgs(4, 4)

        # Check
        if sys.argv[2].split('.')[-1].lower() not in ["apr", "apricot"]:
            raise ValueError("Expected Apricot file")

        compileCode(False)

    elif sys.argv[1] == "standalone":
        requireArgs(4, 4)

        # Check
        if sys.argv[2].split('.')[-1].lower() not in ["apr", "apricot"]:
            raise ValueError("Expected Apricot file")

        compileCode(True)

    elif sys.argv[1] == "execute":
        requireArgs(3, 4)

        # Check
        if sys.argv[2].split('.')[-1] != "py":
            raise ValueError("Expected Python file")

        # Exec
        with open(sys.argv[2]) as f:
            code = f.read()
            execute(code)

    elif sys.argv[1] == "uncache":
        requireArgs(3, 3)
        uncache()

    elif sys.argv[1] == "clearcache":
        requireArgs(2, 2)
        CacheLoader.clear()

    elif sys.argv[1] == "run":

        # Check
        if sys.argv[2].split('.')[-1].lower() not in ["apr", "apricot"]:
            raise ValueError("Expected Apricot file")

        requireArgs(3, 6)
        run()

    elif sys.argv[1] == "install":
        requireArgs(3, 3)

        install()

    else:
        raise RuntimeError("Unknown command")


# Entry
if __name__ == '__main__':
    main()
