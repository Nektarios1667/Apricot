import inspect
import io
import sys
import time
from typing import Callable

import requests

import Cache
from Cache import CacheLoader
from Classes import *
from Compiler import Compiler
import Functions as F
import Packager
import Regex
from Text import ColorText as C

DEFAULTENV = {'inspect': inspect, 'Function': Callable, 'log': Compiler.log, 'error': Compiler.error, 'load': Compiler.load, 'call': Compiler.call, 'Pointer': Pointer, 'var': Inferred, 'variable': Compiler.variable, 'giveback': Compiler.giveback, 'NoType': NoType, 'null': None, 'true': True, 'false': False, '_constants': {}, '_varTypes': {}}

def compileCode(code: str, file: str, output: str, standalone: bool = False, noCache: bool = False):
    # Setup
    env = DEFAULTENV

    # Time
    start = time.perf_counter()

    # Load cache
    cache = CacheLoader.find(code)
    if not noCache and cache is not None:
        # Load
        compiled, consts = cache.compiled, cache.consts
        caching = None
        env["_constants"] = cache.consts

        # Load warnings
        for warning in cache.warnings:
            Compiler.warn(*warning)
        # Print uncache
        duration = round((time.perf_counter() - start) * 1000, 1)
        print(f'{C.CYAN}Uncached ".cache\\_cache_.pkl" [{duration} ms]\n{C.RESET}')

    # Recompile
    else:
        compiled, caching, consts = Compiler.compile(code)
        env["_constants"] = consts
        duration = round((time.perf_counter() - start)*1000, 1)
        print(f'{C.CYAN}Compiled {os.path.basename(file)} [{duration} ms]\n{C.RESET}')

    # Write the compiled code to a file
    # Embed if specified
    compiled = f'_constants = {consts}\n{compiled}'
    if standalone:
        imports = ['inspect', 're', 'sys', 'os', 'time', 'pickle', 'typing.Callable', 'types']
        embeds = [*Packager.getMethods(Compiler), F.getLine, F.searchLine, Library, C, Cache.Snapshot, Cache.CacheLoader, Pointer, NoType, Regex]
        repl = {'Compiler.': '', 'F.': '', 'R.': '', 'Cache.': '', 'C.': 'ColorText.', 'folder = os.path.dirname(sys.argv[1])': 'folder = os.path.dirname(sys.argv[0])'}
        headers = [f'_constants = {consts}', '_varTypes = {}', 'Function = Callable', 'with open(rf"{sys.argv[0]}", "r") as f:\n\tcode = f.read()']

        compiled = Packager.standalone(imports, headers, embeds, compiled, replacements=repl, removals=["@staticmethod"])

    # Write
    if output:
        with open(output, 'w') as f:
            f.write(compiled)

    # Caching
    if not noCache and caching is not None:
        CacheLoader.store(caching)

    # Returning
    return compiled, env, duration

def execute(code: str, env: dict = None):
    # Setup
    start = time.perf_counter()
    env = env or DEFAULTENV

    # Buffer
    captureBuffer = io.StringIO()
    sys.stdout = captureBuffer
    # Execute
    exec(code, env, env)
    # Reset buffer
    sys.stdout = sys.__stdout__
    captured = captureBuffer.getvalue()
    print(captured)

    # Prints
    duration = round((time.perf_counter() - start) * 1000, 1)
    print(f'\n{C.CYAN}Ran {os.path.basename(sys.argv[0])} [{duration} ms]\n{C.RESET}')

    return captured, duration

def uncache(output=''):
    os.makedirs(output, exist_ok=True)

    for s, snapshot in enumerate(CacheLoader.load()):
        with open(f'{output}/snapshot_code-{s}.apr', 'w') as f:
            f.write(snapshot.code)
        with open(f'{output}/snapshot_compiled-{s}.apy', 'w') as f:
            f.write(snapshot.compiled)

def run(code: str, file: str, output: str, noCache: bool = False):
    compiled, env, compileTime = compileCode(code, file, output, noCache=noCache)
    output, runTime = execute(compiled, env)
    return output, compileTime, runTime

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
        print(f"Failed to fetch library: {resp.status_code}")


def main():
    # Empty
    if len(sys.argv) < 2:
        sys.argv = [sys.argv[0], *input("Enter command:").split(' ')]

    # Commands
    if sys.argv[1] == "compile":
        requireArgs(4, 4)

        # Check
        if sys.argv[2].split('.')[-1].lower() not in ("apr", "apricot"):
            raise ValueError("Expected Apricot file")
        else:
            with open(sys.argv[2], 'r') as f:
                code = f.read()

        compileCode(code, sys.argv[2], sys.argv[3])

    elif sys.argv[1] == "standalone":
        requireArgs(4, 4)

        # Check
        if sys.argv[2].split('.')[-1].lower() not in ("apr", "apricot"):
            raise ValueError("Expected Apricot file")
        else:
            with open(sys.argv[2], 'r') as f:
                code = f.read()

        compileCode(code, sys.argv[2], sys.argv[3], standalone=True)

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
        uncache(sys.argv[2])

    elif sys.argv[1] == "clearcache":
        requireArgs(2, 2)
        CacheLoader.clear()

    elif sys.argv[1] == "run":

        # Check
        if sys.argv[2].split('.')[-1].lower() not in ("apr", "apricot"):
            raise ValueError("Expected Apricot file")
        else:
            with open(sys.argv[2], 'r') as f:
                code = f.read()

        requireArgs(3, 6)
        run(code, sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else '', '--nocache' in sys.argv)

    elif sys.argv[1] == "install":
        requireArgs(3, 3)

        install()

    else:
        raise RuntimeError("Unknown command")


# Entry
if __name__ == '__main__':
    main()
