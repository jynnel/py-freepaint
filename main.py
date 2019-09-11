#!/usr/bin/python

'''
Required libs: numpy, OpenGL, Xlib, sdl2
'''

import sys
import time

from modules.sdlapp import SDLApp

if sys.platform.startswith("linux"):
    from modules.xdevices import XDevices

framerate = 120.0
framedelta = 1.0 / framerate

def main(argv):
    app = SDLApp("py-freepaint", 580, 580)

    found_stylus = False
    if sys.platform.startswith("linux"):
        xd = XDevices()
        found_stylus = xd.add_device("stylus")

    waitpoint = time.time() + framedelta
    while app.running:
        app.parse_events()
        
        if sys.platform.startswith("linux") and found_stylus:
            xd.update_devices()
            if xd.is_device_active("stylus"):
                print("stylus", xd.get_device_values("stylus"))
        
        app.renderer.render()
        app.swap_window()

        now = time.time()
        if now < waitpoint:
            time.sleep(waitpoint - now)
        waitpoint = now + framedelta

    if sys.platform.startswith("linux"):
        xd.close()
    app.close()
    print("Quit.")

if __name__ == '__main__':
    sys.exit(main(sys.argv))
