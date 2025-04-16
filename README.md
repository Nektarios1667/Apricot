# Apricot

**Apricot** is a high-level scripting language designed for simplicity, readability, and ease of use. It supports object-oriented programming, pointers, libraries, etc.

## Features

- OOP with constructors and methods
- Constants and strong typing
- Custom types
- Pointers
- Try-catch exception handling
- Looping and conditionals
- Functions
- Simple library system

## Setup
1. Download the [source code](https://github.com/Nektarios1667/Apricot) from GitHub
2. Go to the directory of the code and run `pyinstaller --onefile Apricot.py`
3. The executable will be outputed in the `dist` directory
4. It can now be moved to any location

## Syntax Example
```
include math;
import functions;

// Constant definition
const: PI = 3.1415926;

// Class
class improvedString inherits str:
    func improvedString(value): // Initialization function
        this.value = value;

    // Method
    func str setChar(char, idx):
        this.value = this.value[:idx] + char[0] + this.value[idx + 1:];


// Function
func int factorial(value):
    int: product = 1;
    // For loop
    for num in (2..value+1):
        product = product * num;

    return product;

// Custom type predicate
type hashtag:
    if isinstance(value, str):
        return value[0] == '#';
    else:
        return false;

// Variable with custom type
hashtag: myHashtag = "#tag";

// Function call
log(factorial(10));

// Object
improvedString: imprStr = improvedString("test");
// Method calling
imprStr.setChar('_', 0);
// Property
log(imprStr.value);

// While loop
int: n = 0;
while n**2 < 100:
    n += 1;

// Try-catch
try:
    // Type casting
    int: age = <int 'thirty four'>;
catch:
    log('Value not a number.');

// Function references
Function: fact = factorial;
log(fact(2));

// Library
log(functions.multiAdd(1, 2, 3));

// Pointers
int: number = 0;
Pointer: point = @number;
number = number + 1;
log(^point);

// Const
log(PI);

```

## Commands

Use Apricot.py to compile, run, or manage Apricot files:

```bash
# Compile an Apricot file
Apricot compile code.apr output.py

# Compile and run standalone
Apricot standalone code.apr standalone.py

# Execute a Python file compiled by Apricot
Apricot execute compiled.py

# Run Apricot script directly
Apricot run code.apr
# Run Apricot script directly and output compiled code
Apricot run code.apr -w out.py

# Clear or manage cache
Apricot clearcache
Apricot uncache directory
```

## Notes

- `.apr` and `.apricot` are valid file extensions for Apricot code.  
- `.apl`, `aprlib`, `apricotlib`, and `apricotlibrary` are valid file extensions for Apricot Libraries.

## License
This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. You are free to copy, share, and adapt the material, as long as you give appropriate credit, do not use it for commercial purposes, and distribute any modified versions under the same license. Full license details are available at https://creativecommons.org/licenses/by-nc-sa/4.0/.
