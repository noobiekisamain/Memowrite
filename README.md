# Memowrite

**Memowrite is a programming language written in plain English words.**

```
say "Hello!"
ask "What is your name?" into name
repeat 3 times
    say "Hi {name}!"
end
```

## Getting started

1. Open **Memowrite Studio** from the Start menu (or the desktop).
2. Pick a program from **Examples**, or type your own.
3. Press **F5** to run it.

You can also double-click any `.mw` file to run it, or type `memowrite yourfile.mw` in a terminal.

## What's in this folder

| | |
|---|---|
| `Examples.md` | Everything Memowrite can do, in one list |
| `examples\` | 25 ready-to-run programs (apps, games, drawings, 2D models) |
| `library\` | Code you can borrow with `use "helpers"` and `use "shapes"` |
| `File.Memory` | An example memory file. Every program gets its own File.Memory next to it for things it `remember`s |
| `MemowriteStudio.exe` | The Memowrite editor |
| `memowrite.exe` | The command-line tool (on your PATH) |
| `vscode\` | The Visual Studio Code extension (`memowrite-1.0.0.vsix`) and Visual Studio grammar |
| `memowrite\` | The Memowrite interpreter and standard library |
| `runtime\` | The engine Memowrite runs on (you never need to touch it) |

## Visual Studio Code

The installer adds the extension automatically when VS Code is installed. To add it by hand:
*Extensions* → `...` → *Install from VSIX...* → choose `vscode\memowrite-1.0.0.vsix`.

## Command line

```
memowrite game.mw          run a program
memowrite check game.mw    look for mistakes without running
memowrite new MyGame       start a new project folder
memowrite words            list every built-in word
memowrite studio           open the editor
memowrite                  the interactive Memowrite shell
```
