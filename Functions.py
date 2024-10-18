from colored import Fore, Style
from typing import Literal

def inject(phrase: str, strings: list):
    phrase = str(phrase)
    for f, fill in enumerate(strings):
        phrase = phrase.replace(f'\x1a@{f}', fill)
    return phrase

def error(error: str, line: str, description: str, row: int | Literal["N/A"], extra: str = ''):
    print(f'{Fore.RED}{error}: "{inject(line)}" - "{inject(description)}" @ line {row}\n{extra}{Style.RESET}')
    exit(-1)
