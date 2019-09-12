from ctypes import byref, c_int
import sdl2
from modules.glrenderer import Renderer

class SDLApp:
    def __init__(self, title, width, height):
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            print(sdl2.SDL_GetError())
        
        pos = sdl2.SDL_WINDOWPOS_UNDEFINED
        self.window = sdl2.SDL_CreateWindow(title.encode('ascii'), pos, pos, width, height, sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_RESIZABLE )
        self.window_size = [c_int(), c_int()]

        if not self.window:
            print(sdl2.SDL_GetError())
        
        wm_info = sdl2.SDL_SysWMinfo()
        sdl2.SDL_GetVersion(wm_info.version)
        print(f"SDL2 version {wm_info.version.major}.{wm_info.version.minor}.{wm_info.version.patch}")

        v = sdl2.video
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_MINOR_VERSION, 2)
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_PROFILE_MASK, v.SDL_GL_CONTEXT_PROFILE_CORE)
        self.context = sdl2.SDL_GL_CreateContext(self.window)

        self.renderer = Renderer(self.context, self.get_window_size())

        self.event = sdl2.SDL_Event()
        
        self.running = True

    def get_window_size(self):
        sdl2.SDL_GetWindowSize(self.window, self.window_size[0], self.window_size[1])
        return (self.window_size[0].value, self.window_size[1].value)

    def close(self):
        self.renderer.close()
        sdl2.SDL_GL_DeleteContext(self.context)
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    def parse_events(self):
        while sdl2.SDL_PollEvent(byref(self.event)) != 0:
            if self.event.type == sdl2.SDL_QUIT:
                self.running = False

    def swap_window(self):
        sdl2.SDL_GL_SwapWindow(self.window)
