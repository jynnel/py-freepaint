#!/usr/bin/python

'''
Required libs:
    Common: numpy, OpenGL, sdl2
    Linux: Xlib
'''

import sys
import os

dname = os.path.abspath(os.path.dirname(sys.argv[0]))
os.chdir(dname)

from modules.sdlapp import App

FPS = 120.0
FRAME_DELTA = 1000.0 / FPS

def main(argv):
    app = App("py-fp")

    waitpoint = app.get_ticks() + FRAME_DELTA
    while app.running:
        app.update_input_state()

        if not app.paused:
            app.check_keybinds_and_run_operators()
            app.render()
        app.swap_window()

        now = app.get_ticks()
        if now < waitpoint:
            app.delay(waitpoint - now)
        waitpoint = app.get_ticks() + FRAME_DELTA
        # app.running = False

    app.close()
    print("Quit.")

if __name__ == '__main__':
    sys.exit(main(sys.argv))
