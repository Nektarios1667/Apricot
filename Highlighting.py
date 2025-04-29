SYNTAXCATEGORIES = r"""
\bclose\b::function
\benumerate\b::function
\binput\b::function
\blog\b::function
\bopen\b::function
\bquit\b::function
\brange\b::function

\band\b::control
\bassert\b::control
\bbreak\b::control
\bcatch\b::control
\belse\b::control
\bfinally\b::control
\bfor\b::control
\bif\b::control
\bimport\b::control
\bin\b::control
\binclude\b::control
\bnext\b::control
\bnoop\b::control
\bor\b::control
\breturn\b::control
\btry\b::control
\busing\b::control
\bwhile\b::control

\bFunction\b::type
\bPointer\b::type
\bbool\b::type
\bconst\b::type
\bfloat\b::type
\bint\b::type
\blist\b::type
\bnull\b::type
\bobject\b::type
\bstr\b::type
\btuple\b::type
\bvar\b::type
\btrue\b::type
\bfalse\b::type

\bclass\b::oop
\bfunc\b::oop
\binherits\b::oop
\bthis\b::oop
\btype\b::oop
\bvalue\b::oop

#^[^;]+(?:\/\/)?$::warn

//.*::comment
("|')[^\1]*?\1::string
\d+(?:\.\d+)?::number
"""

CONSOLE = r"""
Warning::#edcd15
Log::#1db1de
Issue::#ff512e
Error::#ff2e2e
System::#8378ab
"""

SYNTAXCOLORS = r"""
function::#346eeb
control::#e09110
type::#ba71f0
oop::#f26181
comment::#969696
string::#3b8f3f
number::#389ba1
warn::#969409
"""