import re

functions = {'output': print, 'input': input}

class Enviroment:
    def __init__(self):
        self.code = ''
        self.vars = {}
        self.system = {}
        self.funcs = {}

    def eval(self, value):
        evaluated = value
        try:
            if evaluated in self.vars.keys():
                return self.vars[evaluated]
            elif evaluated.split('(')[0] in self.funcs:
                # Run
                fCode, fArgs = self.funcs[evaluated.split('(')[0]]
                fArgValues = evaluated.split('(')[1].replace(', ', ',').split(',')

                for a, arg in enumerate(fArgs):
                    fCode = fCode.replace(fArgValues[a], arg)

                return self.execute(self.funcs[evaluated.split('(')[0]])
            else:
                return eval(evaluated, self.vars)

        except NameError:
            return evaluated

    def execute(self, code: str):
        skips = 0
        lines = code.replace('\n', ';').split(';')

        for l, line in enumerate(lines):
            line = line.strip()

            # Whitespaces
            if line in ['', '\n', ' ', '}'] or line[0:2] == '//':
                continue

            # Skipped lines usually function or class definitions
            if skips > 0:
                skips -= 1
                continue

            # New variables
            expr = re.match(r'(list|group|dict|bool|str|int|float|null|obj|var): ?(\w*) ?= ?(.*)', line)
            if expr:
                expr = [group for group in expr.groups()]

                # When using var to automatically assign type
                if expr[0] == 'var':
                    expr[0] = str(type(self.eval(expr[2])))[8:-2]

                # Not correct type
                if type(self.eval(expr[2])) is not self.eval(expr[0]):
                    raise TypeError(line)

                # If var exists already
                if expr[1] not in self.vars.keys():
                    self.vars[expr[1]] = self.eval(expr[0])(eval(expr[2]))
                else:
                    raise NameError(line)
                continue

            # Existing variables
            expr = re.match(r'(\w+) ?= ?([^ ].*)', line)
            if expr:
                expr = [group for group in expr.groups()]

                # Check errors first
                if expr[0] not in self.vars:
                    raise NameError(line)
                if type(self.eval(expr[1])) is not type(self.vars[expr[0]]):
                    raise TypeError(line)

                self.vars[expr[0]] = self.eval(expr[1])

                continue

            # Creating a function
            expr = re.match(r'func (\w+)\((.*)\) ?{', line)
            if expr:
                expr = [group for group in expr.groups()]

                if expr[0] in self.funcs:
                    raise NameError(line)

                # Use "l" to create func then skip next lines
                func = ''
                opens = 1
                closes = 0

                for funcline in lines[l + 1:]:
                    if funcline in ['', ' ', '\n']:
                        continue

                    if '}' in funcline:
                        closes += 1
                    if '{' in funcline:
                        opens += 1

                    if closes < opens:
                        skips += 1

                    func += f'{funcline.strip()};'

                self.funcs[expr[0]] = (func, [*expr[1].replace(', ', ',').split(',')])
                continue

            # If statement
            expr = re.match(r'if (.*) ?{', line)
            if expr:
                expr = [group for group in expr.groups()]

                # Use "l" to create func then skip next lines
                inside = 0
                opens = 1
                closes = 0

                for ifline in lines[l + 1:]:
                    if '}' in ifline:
                        closes += 1
                    if '{' in ifline:
                        opens += 1

                    if closes < opens:
                        inside += 1

                if not self.eval(expr[0]):
                    skips = inside

                continue

            # Returning
            expr = re.match(r'return (.*)', line)
            if expr:
                expr = [group for group in expr.groups()]
                return self.eval(expr[1])

            # Builtin functions
            # Gets all the functions for functions variable
            expr = re.match(rf'({"|".join(functions.keys())})\((.*)\)', line)
            if expr:
                expr = [group for group in expr.groups()]

                # Run
                functions[self.eval(expr[0])](*[self.eval(arg) for arg in expr[1].split(',')])
                continue

            # Custom functions
            expr = re.match(rf'({"|".join(self.funcs.keys())})\((.*)\)', line)
            if expr:
                expr = [group for group in expr.groups()]



                continue

            # Syntax errors
            raise SyntaxError(line)

        # After running
        return 1

    def run(self):
        self.execute(self.code)

test = Enviroment()
test.code = """
func test(a, b) {
    return a + b
}

str: result = test(1, 2)
output(result)
"""

test.run()
print(test.funcs)

x: int = 10
