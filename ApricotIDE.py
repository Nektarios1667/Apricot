import os.path
import re
import sys
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

import Apricot
from Cache import *
import Console
import Highlighting
import Regex
from Text import ColorText


def showRegex(_=None):
    # Text
    text = ''
    moduleVars = {name:getattr(Regex, name) for name in dir(Regex) if not name.startswith("__")}

    for var, val in moduleVars.items():
        text += f'{var} = {val}\n'

    # Window
    win = tk.Toplevel()
    win.title("Regex Patterns")
    textBox = tk.Text(win, wrap="none")  # Disable wrapping
    textBox.insert("1.0", text)
    textBox.pack(expand=True, fill="both")


def openConsole(_=None):
    global console
    # Window
    consoleText = console.getText()
    win = tk.Toplevel()
    win.title("Apricot Console")
    textBox = tk.Text(win, wrap="none", background=THEMEGRAY, foreground='white')  # Disable wrapping
    textBox.insert("1.0", consoleText)

    # Syntax highlighting
    consoleHighlights = {line.split('::')[0]:line.split('::')[1] for line in Highlighting.CONSOLE.splitlines() if line}
    for level, color in consoleHighlights.items():
        textBox.tag_remove(level, '1.0', tk.END)
        textBox.tag_config(level, foreground=color)
        for match in re.finditer(fr'\[[\d:.]+] *{level}:', consoleText):
            startIdx = f"1.0 + {match.start()} chars"
            endIdx = f"1.0 + {match.end()} chars"
            textBox.tag_add(level, startIdx, endIdx)

    # Disable and pack
    textBox.config(state='disabled')
    textBox.pack(expand=True, fill="both")


# Open file
def openFile(path: str = ''):
    global file
    path = path or filedialog.askopenfilename(filetypes=[("Apricot files", "*.apr;*.apricot;*.apl;*.aprlib;*.apricotlib;*.apricotlibrary")])
    if path:
        file = path
        with open(path, "r") as f:
            content = f.read()
            textArea.delete("1.0", tk.END)
            textArea.insert(tk.END, content)

    onKeyRelease()
    refreshFiles()


def selectFile(_=None):
    global file
    file = filesSelect.get(filesSelect.curselection()[0])
    with open(file, "r") as f:
        content = f.read()
        textArea.delete("1.0", tk.END)
        textArea.insert(tk.END, content)

    syntaxHighlighting()


def refreshFiles(_=None):
    global file, files
    files = []

    if file:
        filesSelect.delete(0, tk.END)
        directory = os.path.dirname(file)
        # Files
        for f in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, f)) and os.path.splitext(f)[1].lower() in ['.apr', '.apricot', '.apl', '.apricotlib', '.apricotlibrary']:
                files.append(f)
                filesSelect.insert(tk.END, f)

        # Libraries
        directory += '/.libraries'
        for f in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, f)) and os.path.splitext(f)[1].lower() in ['.apr', '.apricot', '.apl', '.apricotlib', '.apricotlibrary']:
                files.append(f'.libraries/{f}')
                filesSelect.insert(tk.END, f'.libraries/{f}')


# Save file
def saveAsFile(_=None):
    path = filedialog.asksaveasfilename(defaultextension=".apr", filetypes=[("Apricot files", "*.apr"), ("All files", "*.*")])
    if path:
        with open(path, "w") as f:
            f.write(textArea.get("1.0", 'end-1c'))


def saveFile(_=None):
    if file:
        with open(file, 'w') as f:
            f.write(textArea.get('1.0', 'end-1c'))
    else:
        saveAsFile()


def newFile(_=None):
    global file

    saveFile()
    file = 'new_script.apr'
    textArea.delete("1.0", tk.END)
    textArea.insert(tk.END, '// New Apricot file')


# About dialog
def showAbout(_=None):
    messagebox.showinfo("About Apricot Editor", "Apricot Editor\nBuilt with Tkinter\nBy Nektarios")


# Syntax highlighting
def syntaxHighlighting(_=None):
    # Clear tags
    for category in syntaxHighlights.values():
        textArea.tag_remove(category, "1.0", tk.END)

    # Add tags
    code = textArea.get('1.0', tk.END)
    for highlight, category in syntaxHighlights.items():
        for match in re.finditer(highlight, code, flags=re.MULTILINE):
            startIdx = f"1.0 + {match.start()} chars"
            endIdx = f"1.0 + {match.end()} chars"
            textArea.tag_add(category, startIdx, endIdx)


def updateOutput(text):
    # Print
    outputArea.config(state='normal')
    outputArea.delete('1.0', tk.END)
    outputArea.tag_remove('1.0', tk.END)
    outputArea.insert('1.0', text)
    outputArea.tag_add('system', '1.0', '2.0')
    outputArea.tag_add('system', f'{int(float(outputArea.index("end-1c")))}.0', f'{int(float(outputArea.index("end-1c")))}.end')

    # Colors
    for pattern, category in {'\u200B[\s\S]+?\uFEFF':'error', '\u200D[\s\S]+?\uFEFF':'system', '\u200C[\s\S]+?\uFEFF':'warn'}.items():
        for match in re.finditer(pattern, text, flags=re.MULTILINE):
            startIdx = f"1.0 + {match.start()} chars"
            endIdx = f"1.0 + {match.end()} chars"
            outputArea.tag_add(category, startIdx, endIdx)

    outputArea.config(state='disabled')


# Run
def run(_=None):
    global console
    # Run
    console, output, runTime = Apricot.run(textArea.get('1.0', tk.END), file, '')

    # Update output area
    updateOutput(output)


def runWithoutCache(_=None):
    global console
    # Run
    console, output, runTime = Apricot.run(textArea.get('1.0', tk.END), file, '', noCache=True)

    # Update output area
    updateOutput(output)


def compileCode(_=None):
    global console

    compiled, _, captured, console = Apricot.compileCode(textArea.get('1.0', tk.END), file, '')
    if compiled:
        path = filedialog.asksaveasfilename(defaultextension=".apr", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        with open(path, 'w') as f:
            f.write(compiled)
    updateOutput(captured)


def standalone(_=None):
    global console

    compiled, _, captured, console = Apricot.compileCode(textArea.get('1.0', tk.END), file, '', standalone=True)
    if compiled:
        path = filedialog.asksaveasfilename(defaultextension=".apr", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        with open(path, 'w') as f:
            f.write(compiled)
    updateOutput(captured)


def lineNumbering(_=None):
    global lineNumbers

    lineNumbers.delete('all')

    lines = len(textArea.get('1.0', tk.END).splitlines())
    for i in range(lines):
        lineNumbers.create_text(2, (i - textScroll.get()[0]*lines)*19 + 4, anchor="nw", text=str(i + 1), font=12, fill='gray')


def onKeyRelease(_=None):
    syntaxHighlighting()
    lineNumbering()


# Constants
THEMEGRAY = '#222222'

# Create main window
root = tk.Tk()
root.title("Apricot Editor")
root.geometry("1400x900")
root.bind('<KeyRelease>', onKeyRelease)
root.config(bg=THEMEGRAY)

# Highlighted words
syntaxHighlights = {k:v for k, v in [line.strip().split('::') for line in Highlighting.SYNTAXCATEGORIES.splitlines() if line and line[0] not in ['\n', '#']]}

# Variables
file = sys.argv[1] if len(sys.argv) >= 2 else ''
files = []
ColorText.system = 'ide'
console = Console.Console()

# Style
style = ttk.Style()
style.theme_use('default')

style.configure(
    "Simple.Vertical.TScrollbar",
    troughcolor=THEMEGRAY,
    background='#777777',
    relief='flat',
    borderwidth=0
)
style.map("Simple.Vertical.TScrollbar", background=[('active', '#888888')])
style.layout("Simple.Vertical.TScrollbar", [
    ('Vertical.Scrollbar.trough', {
        'children': [('Vertical.Scrollbar.thumb', {'unit': '1', 'sticky': 'nswe'})]
    })
])

# Line numbers
lineNumbers = tk.Canvas(root, width=50, bg=THEMEGRAY, bd=0, highlightthickness=0)
lineNumbers.place(x=0, y=0, relx=0, rely=0, width=50, relheight=.8)

# Text area
textScroll = ttk.Scrollbar(style='Simple.Vertical.TScrollbar')


def areaScroll(*args):
    textScroll.set(*args)
    lineNumbering()


textArea = tk.Text(root, wrap='word', font=("Consolas", 12), yscrollcommand=areaScroll, bg=THEMEGRAY, fg='white', insertbackground='white', tabs=32, highlightbackground='gray', selectbackground='#174657')
textArea.place(x=50, y=0, relx=0, rely=0, relwidth=0.8, relheight=0.8)


def barScroll(*args):
    textArea.yview(*args)
    lineNumbering()


textScroll.config(command=barScroll)
textScroll.place(x=0, y=5, relx=0.8, rely=0, relheight=0.8, height=-10)

# Highlighted colors
syntaxColors = {line.split('::')[0]: line.split('::')[1] for line in Highlighting.SYNTAXCOLORS.splitlines() if line}
for category, color in syntaxColors.items():
    textArea.tag_config(category, foreground=color)

# Output area
outputScroll = ttk.Scrollbar(style='Simple.Vertical.TScrollbar')
outputScroll.place(x=0, y=5, relx=0.8, rely=.8, relheight=0.2, height=-10)

outputArea = tk.Text(root, wrap='word', height=8, font=("Consola", 12), yscrollcommand=outputScroll.set, bg=THEMEGRAY, fg='white', insertbackground='white', state='disabled', tabs=32, highlightbackground='gray', selectbackground='#20627a')
outputArea.place(relx=0, rely=0.8, relwidth=0.8, relheight=0.2, width=50)
outputArea.tag_config('system', foreground='#0BA28D')
outputArea.tag_config('warn', foreground='yellow')
outputArea.tag_config('error', foreground='#ff1c1c')

outputScroll.config(command=outputArea.yview)

# File selector
filesSelect = tk.Listbox(bg=THEMEGRAY, fg='#9e9e9e', font=("Consola", 14), highlightbackground='gray', selectbackground='#363636', highlightcolor='darkgray', exportselection=False, activestyle='none')
filesSelect.place(relx=0.8125, rely=0, relwidth=0.1875, relheight=1.0)
filesSelect.bind("<Double-Button-1>", selectFile)


# Timed functions
def selectFirst():
    filesSelect.selection_set(0)
    filesSelect.see(0)
root.after(100, selectFirst)

# Lifts
textScroll.lift()
outputScroll.lift()

# Hotkeys
root.bind('<Control-o>', lambda event: openFile())  # Ctrl+O
root.bind('<Control-n>', newFile)
root.bind('<Control-s>', saveFile)  # Ctrl+S
root.bind('<Control-S>', saveAsFile)  # Ctrl+Shift+S
root.bind('<Control-r>', run)  # Ctrl+R
root.bind('<Control-R>', runWithoutCache)  # Ctrl+Shift+R
root.bind('<Control-C>', openConsole)  # Ctrl+Shift+C
root.bind('<Control-Alt-r>', onKeyRelease)  # Ctrl+Alt+R

# Create menu bar
menuBar = tk.Menu(root)
root.config(menu=menuBar)

# File menu
fileMenu = tk.Menu(menuBar, tearoff=0)
fileMenu.add_command(label="Open", command=openFile)
fileMenu.add_command(label="Save", command=saveFile)
fileMenu.add_command(label="Save As", command=saveAsFile)
fileMenu.add_command(label="New", command=newFile)
fileMenu.add_separator()
fileMenu.add_command(label="Exit", command=root.quit)
menuBar.add_cascade(label="File", menu=fileMenu)

# Edit menu
editMenu = tk.Menu(menuBar, tearoff=0)
menuBar.add_cascade(label="Edit", menu=editMenu)

# Run menu
runMenu = tk.Menu(menuBar, tearoff=0)
runMenu.add_command(label="Run", command=run)
runMenu.add_command(label="Run Without Cache", command=runWithoutCache)
runMenu.add_separator()
runMenu.add_command(label="Compile", command=compileCode)
runMenu.add_command(label="Standalone", command=standalone)
menuBar.add_cascade(label="Run", menu=runMenu)

# Cache menu
cacheMenu = tk.Menu(menuBar, tearoff=0)
cacheMenu.add_command(label="Clear Cache", command=CacheLoader.clear)
cacheMenu.add_command(label="Uncache", command=Apricot.uncache)
menuBar.add_cascade(label="Cache", menu=cacheMenu)

# Dev menu
devMenu = tk.Menu(menuBar, tearoff=0)
devMenu.add_command(label="Regex", command=showRegex)
devMenu.add_command(label="Console", command=openConsole)
menuBar.add_cascade(label="Dev", menu=devMenu)

# Help menu
helpMenu = tk.Menu(menuBar, tearoff=0)
helpMenu.add_command(label="About", command=showAbout)
menuBar.add_cascade(label="Help", menu=helpMenu)

# Open file
openFile(os.path.join(os.path.dirname(sys.argv[0]), file))

# Run the app
root.mainloop()
