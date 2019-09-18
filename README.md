# py-freepaint

A minimal digital painting app for Linux systems (running X11) written in Python. Work in progress.

![img](https://i.imgur.com/AjM06S0.png)

## Milestone 0: September 17, 2019

![img](https://i.imgur.com/finrNgp.png)

This milestone marks feature parity with prior painting apps I have written in C. There's no UI yet, but view navigation and painting feel is passable. Brush strokes are based on GLSL shaders, of which there is currently draw, blur, and smudge. Included is default-settings.json with example bindings for right-handed tablet users on QWERTY keyboards. The keybind system is very flexible; by copying the file to settings.json, it can be edited and configured for a different setup.