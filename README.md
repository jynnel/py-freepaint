# py-freepaint

A minimal digital painting app for Linux systems (running X11) written in Python. Work in progress.

![img](https://i.imgur.com/AjM06S0.png)

## Installation

### Linux (warning: alpha!)
Use your package manager to install Python >= 3.7, and pip for Python 3.
```
git clone https://github.com/vrav/py-freepaint.git
pip install Xlib numpy imgui[sdl2]

```
You may need to substitute pip and python with pip3 and python3 depending on your installation of those packages. The installation of `imgui[sdl2]` will install `PySDL2` and `PyOpenGL` as well. If you're on Arch, you can skip pip for most of these packages, as they are available via pacman.

## Current Status

A UI has been added, thanks to [pyimgui](https://github.com/swistakm/pyimgui).

Work to enhance the brush system will follow.

![img](https://i.imgur.com/riw3Gri.png)

## Milestone 0: September 17, 2019

This milestone marks feature parity with prior painting apps I have written in C. There's no UI yet, but view navigation and painting feel is passable. Brush strokes are based on GLSL shaders, of which there is currently draw, blur, and smudge. Included is default-settings.json with example bindings for right-handed tablet users on QWERTY keyboards. The keybind system is very flexible; by copying the file to settings.json, it can be edited and configured for a different setup.

![img](https://i.imgur.com/finrNgp.png)
