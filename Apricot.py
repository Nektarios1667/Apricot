import copy
import io
import sys
import time
from typing import Callable

import requests

import Cache
from Cache import CacheLoader
from Classes import *
from Compiler import Compiler, ExitExecution
import Functions as F
import Packager
import Regex
from Text import ColorText as C, ColorText

DEFAULTENV = {'Function': Callable, 'log': Compiler.log, 'error': Compiler.error, 'load': Compiler.load, 'call': Compiler.call, 'Pointer': Pointer, 'var': Inferred, 'variable': Compiler.variable, 'instanceAttribute': Compiler.attribute, 'giveback': Compiler.giveback, 'NoType': NoType, 'null': None, 'true': True, 'false': False, '_constants': {}, '_varTypes': {}}

def compileCode(code: str, file: str, output: str = '', standalone: bool = False, noCache: bool = False):
    # Setup
    env = copy.deepcopy(DEFAULTENV)
    captureBuffer = io.StringIO()
    sys.stdout = captureBuffer

    # Time
    start = time.perf_counter()

    # Load cache
    cache = CacheLoader.find(code)
    if not noCache and cache is not None:
        # Load
        compiled, consts, console = cache.compiled, cache.consts, cache.console
        caching = None
        env["_constants"] = cache.consts

        # Print uncache
        duration = round((time.perf_counter() - start) * 1000, 1)
        print(f'{C.CYAN}Uncached ".cache\\_cache_.pkl" [{duration} ms]{C.RESET}')

        # Load warnings
        for warning in cache.warnings:
            Compiler.warn(*warning)
    # Recompile
    else:
        try:
            compiled, caching, consts, console = Compiler.compile(code)
        except ExitExecution:
            duration = round((time.perf_counter() - start)*1000, 1)
            print(f'{C.CYAN}Compiled {os.path.basename(file)} [{duration} ms]{C.RESET}')
            sys.stdout = sys.__stdout__
            captured = captureBuffer.getvalue()
            return Compiler.compiled, Compiler.constants, captured, Compiler.console

        env["_constants"] = consts
        duration = round((time.perf_counter() - start)*1000, 1)
        print(f'{C.CYAN}Compiled {os.path.basename(file)} [{duration} ms]{C.RESET}')

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

    # Output
    sys.stdout = sys.__stdout__
    captured = captureBuffer.getvalue()

    # Returning
    return compiled, env, captured, console

def execute(code: str, file: str, env: dict = None):
    # Setup
    start = time.perf_counter()
    env = env or DEFAULTENV

    # Buffer
    captureBuffer = io.StringIO()
    sys.stdout = captureBuffer
    # Execute
    try:
        exec(code, env, env)
    except ExitExecution: pass

    # Prints
    duration = round((time.perf_counter() - start) * 1000, 1)
    print(f'{C.CYAN}Ran {file} [{duration} ms]\n{C.RESET}')

    # Reset buffer
    sys.stdout = sys.__stdout__
    captured = captureBuffer.getvalue()

    return captured, duration

def uncache(output=''):
    os.makedirs(output, exist_ok=True)

    for s, snapshot in enumerate(CacheLoader.load()):
        with open(f'{output}/snapshot_code-{s}.apr', 'w') as f:
            f.write(snapshot.code)
        with open(f'{output}/snapshot_compiled-{s}.apy', 'w') as f:
            f.write(snapshot.compiled)

def run(code: str, file: str, output: str, noCache: bool = False):
    compiled, env, compileOutput, console = compileCode(code, file, output, noCache=noCache)
    exectueOutput, runTime = execute(compiled, file, env)
    return console, compileOutput + exectueOutput, runTime

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
    if getattr(sys, 'frozen', False):
        ColorText.system = 'executable'

    # Commands
    if sys.argv[1] == "compile":
        requireArgs(4, 4)

        # Check
        if sys.argv[2].split('.')[-1].lower() not in ("apr", "apricot"):
            raise ValueError("Expected Apricot file")
        else:
            with open(sys.argv[2], 'r') as f:
                code = f.read()

        print(compileCode(code, sys.argv[2], sys.argv[3])[2])

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
            print(execute(code, sys.argv[2])[0])

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
        print(run(code, sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else '', '--nocache' in sys.argv)[0])

    elif sys.argv[1] == "install":
        requireArgs(3, 3)

        install()

    else:
        raise RuntimeError("Unknown command")


# Entry
if __name__ == '__main__':
    main()
