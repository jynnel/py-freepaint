#!/usr/bin/python

'''
Required libs:
    Common: numpy, OpenGL, sdl2
    Linux: Xlib
'''

import sys

from modules.sdlapp import SDLApp

if sys.platform.startswith("linux"):
    from modules.devices.xdevices import Devices
elif sys.platform.startswith("win32"):
    from modules.devices.windevices import Devices

FPS = 120.0
FRAME_DELTA = 1000.0 / FPS

def main(argv):
    app = SDLApp("py-fp", 580, 580)

    found_stylus = False
    devices = Devices()
    found_stylus = devices.add_device("stylus")

    waitpoint = app.get_ticks() + FRAME_DELTA
    while app.running:
        app.update_input_state()
        app.check_keybinds()

        if app.input_state.active_operator:
            print("active operator", app.input_state.active_operator)

        if found_stylus:
            devices.update_devices()
            if devices.is_device_active("stylus"):
                print("stylus", devices.get_device_values("stylus"))
        
        app.renderer.render()
        app.swap_window()

        now = app.get_ticks()
        if now < waitpoint:
            app.delay(waitpoint - now)
        waitpoint = app.get_ticks() + FRAME_DELTA
        # app.running = False

    devices.close()
    app.close()
    print("Quit.")

if __name__ == '__main__':
    sys.exit(main(sys.argv))
