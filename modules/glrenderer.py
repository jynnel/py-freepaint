from ctypes import c_int

from OpenGL import GL
from OpenGL.GL import shaders

from modules.math import mat4_ortho, mat4_mul, mat4_identity, mat4_translate, mat4_print
from modules.gltypes import Program, RenderTarget, DualFramebuffer
from modules.types import RGBA

DEFAULT_CANVAS = {
    "verts": [
        0, 0, 0,
        0, 1, 0,
        1, 0, 0,
        1, 1, 0,
    ],
    "uvs": [
        0, 0,
        0, 1,
        1, 0,
        1, 1,
    ]
}

DEFAULT_SCREENQUAD = {
    "verts": [
       -1,-1, 0,
       -1, 1, 0,
        1,-1, 0,
        1, 1, 0,
    ],
    "uvs": [
        0, 0,
        0, 1,
        1, 0,
        1, 1,
    ]
}

class Renderer:
    def __init__(self, context, window_size):
        self.context = context        
        self.window_size = window_size

        self.ortho_matrix = mat4_ortho(self.window_size[0], self.window_size[1])

        GL.glClearColor(0, 0, 0, 1)

        self.system_framebuffer_id = GL.glGetIntegerv( GL.GL_FRAMEBUFFER_BINDING )

        self.draw_prog = Program("shaders/draw.vert", "shaders/draw.frag")
        
        self.canvas_size = 512
        self.canvas = DualFramebuffer(self.canvas_size, self.canvas_size, RGBA(0.5, 0.5, 0.5, 1.0), True)

        self.view = RenderTarget(
            {
                "vertex shader path": "shaders/canvas.vert",
                "fragment shader path": "shaders/canvas.frag",
            }, {
                "vertices": [v * self.canvas_size for v in DEFAULT_CANVAS["verts"]],
                "uvs": DEFAULT_CANVAS["uvs"],
            }, {
                "width": self.window_size[0],
                "height": self.window_size[0],
                "color": RGBA(0.2, 0.2, 0.2, 1),
                "generate mipmaps": True
            }
        )
        self.view_transform = mat4_identity()
        hz = self.canvas_size * 0.5
        mat4_translate(self.view_transform, self.window_size[0] * 0.5 - hz, self.window_size[1] * 0.5 - hz, -0.5)
        self.view_transform_screen = mat4_mul(self.view_transform, self.ortho_matrix)

        self.screen = RenderTarget(
            {
                "vertex shader path": "shaders/screen.vert",
                "fragment shader path": "shaders/screen.frag",
            }, {
                "vertices": DEFAULT_SCREENQUAD["verts"],
                "uvs": DEFAULT_SCREENQUAD["uvs"],
            }, {
                "width": self.window_size[0],
                "height": self.window_size[1],
                "color": RGBA(0.2, 0.2, 0.4, 1),
                "generate mipmaps": False
            }
        )
        self.screen.fb.id = self.system_framebuffer_id

    def close(self):
        pass

    def render(self):
        GL.glViewport(0, 0, self.window_size[0], self.window_size[1])

        self.view.render({
            "basetexture": self.canvas.fbs[1].texture if self.canvas.toggle else self.canvas.fbs[0].texture,
            "transform": self.view_transform_screen
        })

        self.screen.render({
            "brushcolor": RGBA(1.0, 0.0, 0.0, 1.0).list(),
            "opacity": 0.8,
            "diam": 20.0,
            "mpos": (0, 0),
            "winsize": (self.window_size[0], self.window_size[1]),
            "basetexture": self.view.fb.texture,
            "showcolor": 1,
            "softness": 0.5,
        })
