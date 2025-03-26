import re

# Example input
code = """
include math;
import functions;

const: pi = 3.1415926;

class improvedString inherits str {
    func improvedString(value) {
        this.value = value;
    }
    func int setChar(char, idx) {
        this.value = this.value[:idx] + char[0] + this.value[idx + 1:];
        return this.value;
    }
}

func int factorial(value) {
int: product = 1;

for num :: range(2, value + 1) {
    ~product = ~product * num;
}

return ~product;
}

for i :: |0, 10, 2| {
    log(factorial(i));
}

int: n = 0;
while n**2 < 100 {
    n += 1;
}

try {
    int: age = <int '12.0')>;
}
catch {
    log('Value not a number.');
}

int: number = 0;
pointer: point = @number;
number = number + 1;
log(^point);
log(pi);

"""


def bracesConvert(apricode: str):
    lines = apricode.splitlines()
    result = []
    indents = [0]  # Stack to track current indentation levels

    for line in lines:
        # Check opening
        if line.strip().endswith('{'):
            headerIndent = len(line) - len(line.lstrip('\t'))
            result.append(line.replace('{', ':'))  # Remove `{`
            indents.append(headerIndent + 1)
            continue

        # Check closing
        if line.strip().endswith('}'):
            line = line.replace('}', '')
            indents.pop()

        # Regular line
        currentIndent = indents
        result.append('\t' * currentIndent[-1] + line.lstrip())

    return "\n".join(result)


# Convert braces to Python indentation
compiled = bracesConvert(code)
print(compiled)
