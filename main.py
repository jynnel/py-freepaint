#!/usr/bin/python

'''
Required libs:
    Common: numpy, OpenGL, sdl2
    Linux: Xlib
'''

import sys

from modules.sdlapp import SDLApp

FPS = 120.0
FRAME_DELTA = 1000.0 / FPS

def main(argv):
    app = SDLApp("py-fp", 580, 580)

    waitpoint = app.get_ticks() + FRAME_DELTA
    while app.running:
        app.update_input_state()
        app.check_keybinds_and_run_operators()
        
        # if app.input_state.active_operator:
        #     print(app.input_state.active_operator)

        app.renderer.render()
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
