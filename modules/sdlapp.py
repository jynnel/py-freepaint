from ctypes import byref, c_int, c_uint32

import sdl2

from modules.glrenderer import Renderer
from modules.input import InputState

class SDLApp:
    def __init__(self, title, width, height):
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            print(sdl2.SDL_GetError())
        
        pos = sdl2.SDL_WINDOWPOS_UNDEFINED
        self.window = sdl2.SDL_CreateWindow(title.encode('ascii'), pos, pos, width, height, sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_RESIZABLE )
        self.window_size = [0, 0]

        if not self.window:
            print(sdl2.SDL_GetError())
        
        wm_info = sdl2.SDL_SysWMinfo()
        sdl2.SDL_GetVersion(wm_info.version)
        print(f"SDL2 version {wm_info.version.major}.{wm_info.version.minor}.{wm_info.version.patch}")

        self.input_state = InputState()
        sdl2.SDL_ShowCursor(sdl2.SDL_DISABLE)

        v = sdl2.video
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_MINOR_VERSION, 2)
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_PROFILE_MASK, v.SDL_GL_CONTEXT_PROFILE_CORE)
        self.context = sdl2.SDL_GL_CreateContext(self.window)

        self.renderer = Renderer(self.context, self.get_window_size(), self.input_state)

        self.event = sdl2.SDL_Event()
        
        self.running = True

    def get_window_size(self):
        w = c_int()
        h = c_int()
        sdl2.SDL_GetWindowSize(self.window, w, h)
        self.window_size = [w.value, h.value]
        return self.window_size

    def close(self):
        self.renderer.close()
        sdl2.SDL_GL_DeleteContext(self.context)
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    def get_ticks(self):
        return sdl2.SDL_GetTicks()

    def delay(self, ticks):
        sdl2.SDL_Delay(c_uint32(int(ticks)))

    def parse_events(self):
        while sdl2.SDL_PollEvent(byref(self.event)) != 0:
            if self.event.type == sdl2.SDL_QUIT:
                self.running = False
            elif self.event.type == sdl2.SDL_MOUSEMOTION:
                x = self.event.motion.x
                y = self.window_size[1] - self.event.motion.y
                self.input_state.update_mpos(x, y)

    def swap_window(self):
        sdl2.SDL_GL_SwapWindow(self.window)
