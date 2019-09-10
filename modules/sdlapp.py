from ctypes import byref
import sdl2
from modules.glrenderer import Renderer

class SDLApp:
    def __init__(self, title, width, height):
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            print(sdl2.SDL_GetError())
        
        pos = sdl2.SDL_WINDOWPOS_UNDEFINED
        self.window = sdl2.SDL_CreateWindow(title.encode('ascii'), pos, pos, width, height, sdl2.SDL_WINDOW_OPENGL)

        if not self.window:
            print(sdl2.SDL_GetError())
        
        wm_info = sdl2.SDL_SysWMinfo()
        sdl2.SDL_VERSION(wm_info.version)

        self.renderer = Renderer(self.window)

        self.event = sdl2.SDL_Event()
        
        self.running = True

    def close(self):
        self.renderer.close()
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    def parse_events(self):
        while sdl2.SDL_PollEvent(byref(self.event)) != 0:
            if self.event.type == sdl2.SDL_QUIT:
                self.running = False

    def swap_window(self):
        sdl2.SDL_GL_SwapWindow(self.window)
