import re
from tkinter import filedialog, messagebox
import tkinter as tk

import Apricot
from Cache import *


# Open file
def openFile():
    global file
    path = filedialog.askopenfilename(filetypes=[("Apricot files", "*.apr;*.apricot;*.apl;*.aprlib;*.apricotlib;*.apricotlibrary")])
    if path:
        file = path
        with open(path, "r") as f:
            content = f.read()
            textArea.delete("1.0", tk.END)
            textArea.insert(tk.END, content)
    syntaxHighlighting()

# Save file
def saveAsFile():
    path = filedialog.asksaveasfilename(defaultextension=".apr", filetypes=[("Apricot files", "*.apr"), ("All files", "*.*")])
    if path:
        with open(path, "w") as f:
            f.write(textArea.get("1.0", tk.END))

def saveFile():
    if file:
        with open(file, 'w') as f:
            f.write(textArea.get('1.0', tk.END))
    else:
        saveAsFile()

def newFile():
    global file

    saveFile()
    file = 'new_script.apr'
    textArea.delete("1.0", tk.END)
    textArea.insert(tk.END, '// New Apricot file')

# About dialog
def showAbout():
    messagebox.showinfo("About Apricot Editor", "Apricot Editor\nBuilt with Tkinter\nBy Nektarios")

# Syntax highlighting
def syntaxHighlighting(event=None):
    # Clear tags
    for category in syntaxHighlights.values():
        textArea.tag_remove(category, "1.0", tk.END)

    # Add tags
    code = textArea.get('1.0', tk.END)
    for highlight, category in syntaxHighlights.items():
        for match in re.finditer(highlight, code):
            startIdx = f"1.0 + {match.start()} chars"
            endIdx = f"1.0 + {match.end()} chars"
            textArea.tag_add(category, startIdx, endIdx)

# Run
def run():
    # Run
    output, compileTime, runTime = Apricot.run(textArea.get('1.0', tk.END), file, '')

    # Update output area
    outputArea.delete('1.0', tk.END)
    outputArea.insert('1.0', f"Compiled {file} [{compileTime} ms]\n\n{output}\n\nRan {file} [{runTime} ms]")

def runWithoutCache():
    # Run
    output, compileTime, runTime = Apricot.run(textArea.get('1.0', tk.END), file, '', noCache=True)

    # Update output area
    outputArea.delete('1.0', tk.END)
    outputArea.insert('1.0', f"Compiled {file} [{compileTime} ms]\n\n{output}\n\nRan {file} [{runTime} ms]")

def compileCode():
    path = filedialog.asksaveasfilename(defaultextension=".apr", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
    Apricot.compileCode(textArea.get('1.0', tk.END), file, output=path)

def standalone():
    path = filedialog.asksaveasfilename(defaultextension=".apr", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
    Apricot.compileCode(textArea.get('1.0', tk.END), file, output=path, standalone=True)

# Create main window
root = tk.Tk()
root.title("Apricot Editor")
root.geometry("1400x900")
root.bind('<KeyRelease>', syntaxHighlighting)

# Highlighted words
with open('highlighting.txt', 'r') as f:
    syntaxHighlights = {k: v for k, v in [line.strip().split('::') for line in f.readlines() if line != '\n']}

# Constants
THEMEGRAY = '#333333'

# Variables
file = ''

# Text area
textScroll = tk.Scrollbar()
textScroll.pack(side='right', fill='y')

textArea = tk.Text(root, wrap='word', font=("Consolas", 12), yscrollcommand=textScroll.set)
textArea.pack(expand=1, fill='both')

textScroll.config(command=textArea.yview)

# Highlighted colors
syntaxColors = {'function': 'blue', 'control': '#8c560b', 'type': '#550bb5', 'oop': '#700756', 'comment': '#4a4a4a', 'string': '#14571d', 'number': '#147876'}
for category, color in syntaxColors.items():
    textArea.tag_config(category, foreground=color)

# Output area
outputScroll = tk.Scrollbar()
outputScroll.pack(side='right', fill='y')

outputArea = tk.Text(root, wrap='word', height=8, font=("Consola", 12), yscrollcommand=outputScroll.set)
outputArea.pack(expand=0, fill='both')
outputArea.tag_config('system', foreground='#0BA28D')
outputArea.tag_config('warn', foreground='yellow')
outputArea.tag_config('error', foreground='red')

outputScroll.config(command=outputArea.yview)

# Create menu bar
menuBar = tk.Menu(root, background='gray')
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

# Help menu
helpMenu = tk.Menu(menuBar, tearoff=0)
helpMenu.add_command(label="About", command=showAbout)
menuBar.add_cascade(label="Help", menu=helpMenu)

# Run the app
root.mainloop()
