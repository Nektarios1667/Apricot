

def inject(phrase: str, strings: list[str]):
    """
    Injects all strings into phrase by replacing \x1a@{#} with the index in the string list.
    :param strings:
    :param phrase:
    :return:
    """
    phrase = str(phrase)
    for f, fill in enumerate(strings):
        phrase = phrase.replace(f'\x1a@{f}', fill)
    return phrase

def getLine(line: int, code: str):
    """
    Gets the line based on the index. Note: the line numbers start at 1.
    :param line:
    :param code:
    :return:
    """
    # Double lines
    while "\n\n" in code:
        code = code.replace('\n\n', '\n//\n')

    # Return
    lines = code.splitlines()

    if lines and line < len(lines):
        return lines[line - 1]
    else:
        return "N/A"

def searchLine(phrase: str, code: str):
    """
    Finds the line number of the phrase in the given paragraph. Note: the line numbers start at 1.
    :param phrase:
    :param code:
    :return:
    """
    lines = code.splitlines()
    for l, line in enumerate(lines):
        if phrase in line:
            return l + 1
    return "N/A"
