import re

functions = {'output': print, 'input': input}

class Enviroment:
    def __init__(self):
        self.code = ''
        self.vars = {}
        self.system = {}

    def eval(self, value):
        try:
            if value in self.vars.keys():
                return self.vars[value]
            else:
                return eval(value, self.vars)

        except NameError:
            return value

    def run(self):
        for line in self.code.replace('\n', ';').split(';'):
            # Whitespaces
            if line in ['', '\n', ' ']:
                continue

            # New variables
            expr = re.match(r'(list|group|dict|bool|str|int|float|null|obj|var): ?(\w*) ?= ?(.*)', line)
            if expr:
                expr = [group for group in expr.groups()]

                # When using var to automatically assign type
                if expr[0] == 'var':
                    expr[0] = str(type(self.eval(expr[2])))[8:-2]

                # Not correct type
                if type(eval(expr[2])) is not eval(expr[0]):
                    raise TypeError

                # If var exists already
                if expr[1] not in self.vars.keys():
                    self.vars[expr[1]] = self.eval(expr[0])(eval(expr[2]))
                else:
                    raise NameError
                continue

            # Existing variables
            expr = re.match(r'(\w+) ?= ?([^ ].*)', line)
            if expr:
                expr = [group for group in expr.groups()]

                # Check errors first
                if expr[0] not in self.vars:
                    raise NameError
                if type(self.eval(expr[1])) is not type(self.vars[expr[0]]):
                    raise TypeError

                self.vars[expr[0]] = self.eval(expr[1])

                continue

            # Builtin functions
            # Gets all the functions for functions variable
            expr = re.match(rf'({"|".join(functions.keys())})\((.*)\)', line)
            if expr:
                # Convery from Matach to list
                expr = [group for group in expr.groups()]

                # Run
                functions[self.eval(expr[0])](*[self.eval(arg) for arg in expr[1].split(',')])
                continue

            # Syntax errors
            raise SyntaxError

        # After running
        return 1


test = Enviroment()
test.code = """
list: x = 'x.y'.split('.')
output(x)
"""

test.run()
