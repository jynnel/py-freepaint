#!/usr/bin/python

'''
Required libs: numpy, OpenGL, Xlib, sdl2
'''

import sys
import time

from modules.sdlapp import SDLApp

if sys.platform.startswith("linux"):
    from modules.xdevices import Devices
elif sys.platform.startswith("win32"):
    from modules.windevices import Devices

framerate = 120.0
framedelta = 1.0 / framerate

def main(argv):
    app = SDLApp("py-freepaint", 580, 580)

    found_stylus = False
    devices = Devices()
    found_stylus = devices.add_device("stylus")

    waitpoint = time.time() + framedelta
    while app.running:
        app.parse_events()
        
        if found_stylus:
            devices.update_devices()
            if devices.is_device_active("stylus"):
                print("stylus", devices.get_device_values("stylus"))
        
        app.renderer.render()
        app.swap_window()

        now = time.time()
        if now < waitpoint:
            time.sleep(waitpoint - now)
        waitpoint = now + framedelta

    devices.close()
    app.close()
    print("Quit.")

if __name__ == '__main__':
    sys.exit(main(sys.argv))
