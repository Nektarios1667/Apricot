def variable(name: str, value, l: int, env: dict, varType: str = ''):
    """
    Built-in function used in compilation to handle variable creation and assignment.
    :param env:
    :param name:

    :param value:
    :param l:
    :param varType:
    :return:
    """
    value = eval(value, env)
    if varType:
        varType = eval(varType, env)

        if not isinstance(value, varType):
            exit(-2)
    else:
        exit(-1)

    try:
        env[name] = value
    except Exception as e:
        exit(-4)

env = {"variable": variable}

exec("""

def test():
    variable("num", "10", 2, globals(), "int")
    print(num)

test()
""", env, env)
