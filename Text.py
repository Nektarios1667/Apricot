import os
import sys


class ColorText:
    # Executable
    if getattr(sys, 'frozen', False):
        RED = ""
        YELLOW = ""
        GREEN = ""
        BLUE = ""
        MAGENTA = ""
        CYAN = ""
        BLACK = ""
        RESET = ""
    # IDE
    elif os.path.basename(sys.argv[0]) == 'ApricotIDE.py':
        RED = "\u200B"
        YELLOW = "\u200C"
        CYAN = "\u200D"
        GREEN = "\u2060"
        BLUE = "\u2061"
        MAGENTA = "\u2062"
        BLACK = "\u2063"
        RESET = "\uFEFF"
    # Script
    else:
        RED = "\033[31m"
        YELLOW = "\033[33m"
        GREEN = "\033[32m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        BLACK = "\033[30m"
        RESET = "\033[0m"
