import inspect
import typing
import textwrap
from Compiler import Compiler
def funcsSource(*functions):
    """
    Returns source code of the given functions in a single string.
    :param functions:
    :return:
    """
    embed = ''
    for function in functions:
        source = inspect.getsource(function)
        embed += f'\n{textwrap.dedent(source)}\n'
    # embed = embed.replace('@staticmethod', '')
    return embed

def getMethods(cls: object):
    """
    Returns methods of the given class.\
    :param cls:
    :return:
    """
    return [func for _, func in inspect.getmembers(cls, predicate=inspect.isfunction)]

def standalone(imports: list[str], headers: list[str], embedding: list[typing.Callable], code: str, replacements: dict[str, str] = None):
    """
    Creates a standalone python script with the given, imports, headers, embedded functions, code, and any replacements.
    :param imports:
    :param headers:
    :param embedding:
    :param code:
    :param replacements:
    :return:
    """

    # Imports
    importsString = ''
    for imp in imports:
        # Selective imports
        if '.' in imp:
            parts = imp.split('.')
            importsString += f"from {parts[0]} import {parts[1]}\n"
        else:
            importsString += f"import {imp}\n"

    # Headers
    headers = "\n".join(headers)

    # Combine into output string
    output = f'{importsString}\n{headers}\n{funcsSource(*embedding)}\n{code}'

    # Replacements
    replacements = replacements or {}
    for original, repl in replacements.items():
        output = output.replace(original, repl)

    return output
