from OpenGL import GL, GLU
import sdl2
from math import sin
import time

from ctypes import c_int

from matrix import mat4_ortho

class Renderer:
    def __init__(self, window):
        self.window = window

        v = sdl2.video
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_MINOR_VERSION, 2)
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_PROFILE_MASK, v.SDL_GL_CONTEXT_PROFILE_CORE)
        self.context = sdl2.SDL_GL_CreateContext(self.window)
        
        self.window_size = [c_int(), c_int()]
        sdl2.SDL_GetWindowSize(self.window, self.window_size[0], self.window_size[1])

        self.ortho_matrix = mat4_ortho(self.window_size[0].value, self.window_size[1].value)

        GL.glClearColor(0, 0, 0, 1)
    
    def close(self):
        sdl2.SDL_GL_DeleteContext(self.context)

    def render(self):
        GL.glClearColor(abs(sin(time.time())), 0, 0, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
