from os.path import isfile
from OpenGL import GL, GLU
from OpenGL.GL import shaders
import sdl2
from math import sin
import time

from ctypes import c_int
from numpy import array

from modules.matrix import mat4_ortho
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

FRAMEBUFFER_STATUS = {
    "GL_FRAMEBUFFER_COMPLETE": GL.GL_FRAMEBUFFER_COMPLETE,
    "GL_FRAMEBUFFER_UNDEFINED": GL.GL_FRAMEBUFFER_UNDEFINED,
    "GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT": GL.GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT,
    "GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT": GL.GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT,
    "GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER": GL.GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER,
    "GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER": GL.GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER,
    "GL_FRAMEBUFFER_UNSUPPORTED": GL.GL_FRAMEBUFFER_UNSUPPORTED,
    "GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE": GL.GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE,
    "GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS": GL.GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS,
}

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

        self.system_framebuffer_id = GL.glGetIntegerv( GL.GL_FRAMEBUFFER_BINDING )

        self.canvas = DualRenderTarget(
            {
                "vertex shader path": "shaders/canvas.vert",
                "fragment shader path": "shaders/canvas.frag",
            }, {
                "vertices": array([v * 512 for v in DEFAULT_CANVAS["verts"]], dtype="float32"),
                "uvs": array(DEFAULT_CANVAS["uvs"], dtype="float32"),
            }, {
                "width": 512,
                "height": 512,
                "color": RGBA(0.5, 0.5, 0.5, 1),
                "generate mipmaps": True
            }
        )

        self.screen = RenderTarget(
            {
                "vertex shader path": "shaders/screen.vert",
                "fragment shader path": "shaders/screen.frag",
            }, {
                "vertices": array(DEFAULT_SCREENQUAD["verts"], dtype="float32"),
                "uvs": array(DEFAULT_SCREENQUAD["uvs"], dtype="float32"),
            }, {
                "width": self.window_size[0].value,
                "height": self.window_size[1].value,
                "color": RGBA(0.0, 0.0, 0.0, 1),
                "generate mipmaps": False
            }
        )

        GL.glBindFramebuffer( GL.GL_FRAMEBUFFER, self.system_framebuffer_id )

    def close(self):
        sdl2.SDL_GL_DeleteContext(self.context)

    def render(self):
        GL.glClearColor(abs(sin(time.time())), 0, 0, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

class Shader:
    def __init__(self, fpath):
        if not isfile(fpath):
            print("ERROR: Shader path %s not found."%fpath)
            self.valid = False
        
        with open(fpath, 'r') as f:
            self.source = f.read()
        
        isfrag = fpath.endswith(".frag")

        self.id = shaders.compileShader(self.source, GL.GL_FRAGMENT_SHADER if isfrag else GL.GL_VERTEX_SHADER)

class Program:
    def __init__(self, v_fpath, f_fpath):
        self.vertex_shader = Shader(v_fpath)
        self.fragment_shader = Shader(f_fpath)

        self.id = shaders.compileProgram(self.vertex_shader.id, self.fragment_shader.id)

        self.uniforms = {}
        uniform_count = c_int()
        GL.glGetProgramiv(self.id, GL.GL_ACTIVE_UNIFORMS, uniform_count)
        for i in range(uniform_count.value):
            name, size, datatype = GL.glGetActiveUniform(self.id, i)
            u = {}
            u["index"] = i
            u["name"] = name.decode('utf-8')
            u["size"] = size
            u["type"] = datatype
            self.uniforms[u["name"]] = u

    def use(self):
        GL.glUseProgram(self.id)

    def set_uniforms(self, values):
        pass

class VertexArrayObject:
    def __init__(self, progID, verts, uvs):
        vao_id = c_int()
        GL.glGenVertexArrays(1, vao_id)

        vxbuf_id = c_int()
        uvbuf_id = c_int()
        GL.glGenBuffers(1, vxbuf_id)
        GL.glGenBuffers(1, uvbuf_id)

        GL.glBindVertexArray( vao_id.value )
        
        GL.glBindBuffer( GL.GL_ARRAY_BUFFER, vxbuf_id.value )
        GL.glBufferData( GL.GL_ARRAY_BUFFER, verts.size, verts, GL.GL_STATIC_DRAW)
        
        v_pos_attrib = GL.glGetAttribLocation( progID, "vertexpos" )
        GL.glEnableVertexAttribArray( v_pos_attrib )
        GL.glVertexAttribPointer(
            v_pos_attrib,
            3,
            GL.GL_FLOAT,
            GL.GL_FALSE,
            0,
            0
        )
        
        GL.glBindBuffer( GL.GL_ARRAY_BUFFER, uvbuf_id.value )
        GL.glBufferData( GL.GL_ARRAY_BUFFER, uvs.size, uvs, GL.GL_STATIC_DRAW)
        
        v_uv_attrib = GL.glGetAttribLocation( progID, "vertexuv" )
        GL.glEnableVertexAttribArray( v_uv_attrib )
        GL.glVertexAttribPointer(
            v_uv_attrib,
            2,
            GL.GL_FLOAT,
            GL.GL_FALSE,
            0,
            0
        )

        self.id = vao_id.value

    def use(self):
        GL.glBindVertexArray(c_int(self.id))

class Framebuffer:
    def __init__(self, width, height, color, gen_mipmaps):
        tex_id = GL.glGenTextures( 1 )
        GL.glBindTexture( GL.GL_TEXTURE_2D, tex_id )
        GL.glTexImage2D( GL.GL_TEXTURE_2D, 0, GL.GL_RGBA16, width, height, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, None )

        GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE )
        GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE )
        
        if gen_mipmaps:
            GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAX_LEVEL, 3 )
            GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR )
            GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR )
            GL.glGenerateMipmap( GL.GL_TEXTURE_2D )
        else:
            GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR )
            GL.glTexParameteri( GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR )
        
        fb_id = GL.glGenFramebuffers( 1 )
        GL.glBindFramebuffer( GL.GL_FRAMEBUFFER, fb_id )
        GL.glFramebufferTexture2D( GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, tex_id, 0 )

        status = GL.glCheckFramebufferStatus( GL.GL_FRAMEBUFFER )
        for s in FRAMEBUFFER_STATUS:
            if status == FRAMEBUFFER_STATUS[s]:
                self.status = s

        GL.glClearColor( color.r, color.g, color.b, color.a )
        GL.glClear( GL.GL_COLOR_BUFFER_BIT )
        
        self.id = fb_id
        self.tex_id = tex_id

        self.width = width
        self.height = height
        self.color = color
        self.gen_mipmaps = gen_mipmaps

class RenderTarget:
    def __init__(self, prog_args, vao_args, fb_args):
        self.program = Program(prog_args["vertex shader path"], prog_args["fragment shader path"])
        self.vao = VertexArrayObject(self.program.id, vao_args["vertices"], vao_args["uvs"])
        self.fb = Framebuffer(fb_args["width"], fb_args["height"], fb_args["color"], fb_args["generate mipmaps"])

class DualRenderTarget:
    def __init__(self, prog_args, vao_args, fb_args):
        self.toggle = True
        self.targets = [
            RenderTarget(prog_args, vao_args, fb_args),
            RenderTarget(prog_args, vao_args, fb_args)
        ]
