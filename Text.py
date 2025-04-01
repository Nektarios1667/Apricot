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
        WHITE = ""
        BLACK = ""
        RESET = ""
    # Script
    else:
        RED = "\033[31m"
        YELLOW = "\033[33m"
        GREEN = "\033[32m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        WHITE = "\033[37m"
        BLACK = "\033[30m"
        RESET = "\033[0m"

class StyleText:
    # Executable
    if getattr(sys, 'frozen', False):
        BOLD = ""
        UNDERLINE = ""
        UNBOLD = ""
        UNUNDERLINE = ""
        BOLDERLINE = ""
        UNBOLDERLINE = ""
    # Script
    else:
        BOLD = "\x1b[1m"
        UNDERLINE = "\x1b[4m"
        UNBOLD = "\x1b[22m"
        UNUNDERLINE = "\x1b[24m"
        BOLDERLINE = "\x1b[1;4m"
        UNBOLDERLINE = "\x1b[22;24m"
