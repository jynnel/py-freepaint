from os.path import isfile
from ctypes import c_int

from OpenGL import GL
from OpenGL.GL import shaders
from numpy import array

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
        for key in self.uniforms:
            u = self.uniforms[key]
            if key in values:
                if u["type"] == GL.GL_SAMPLER_2D:
                    values[key].use()
                if u["type"] == GL.GL_FLOAT_MAT4:
                    GL.glUniformMatrix4fv( u["index"], 1, GL.GL_FALSE, array(values[key], dtype="float32") )
                if u["type"] == GL.GL_FLOAT_VEC4:
                    GL.glUniform4fv( u["index"], 1, array(values[key], dtype="float32") )
                if u["type"] == GL.GL_FLOAT_VEC2:
                    GL.glUniform2fv( u["index"], 1, array(values[key], dtype="float32") )
                if u["type"] == GL.GL_FLOAT:
                    GL.glUniform1f( u["index"], values[key] )
                if u["type"] == GL.GL_INT:
                    GL.glUniform1i( u["index"], values[key] )

class VertexArrayObject:
    def __init__(self, progID, verts_list, uvs_list):
        verts = array(verts_list, dtype="float32")
        uvs = array(uvs_list, dtype="float32")

        vao_id = c_int()
        GL.glGenVertexArrays(1, vao_id)

        vxbuf_id = c_int()
        uvbuf_id = c_int()
        GL.glGenBuffers(1, vxbuf_id)
        GL.glGenBuffers(1, uvbuf_id)

        GL.glBindVertexArray( vao_id.value )
        
        GL.glBindBuffer( GL.GL_ARRAY_BUFFER, vxbuf_id.value )
        GL.glBufferData( GL.GL_ARRAY_BUFFER, verts.size * verts.itemsize, verts, GL.GL_STATIC_DRAW)
        
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
        GL.glBufferData( GL.GL_ARRAY_BUFFER, uvs.size * uvs.itemsize, uvs, GL.GL_STATIC_DRAW)
        
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
        GL.glBindVertexArray( self.id )

class Texture:
    def __init__(self, width, height, gen_mipmaps):
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
        
        self.id = tex_id
        self.gen_mipmaps = gen_mipmaps
    
    def use(self):
        GL.glBindTexture( GL.GL_TEXTURE_2D, self.id )

class Framebuffer:
    def __init__(self, width, height, color, gen_mipmaps):
        self.texture = Texture(width, height, gen_mipmaps)
        
        fb_id = GL.glGenFramebuffers( 1 )
        GL.glBindFramebuffer( GL.GL_FRAMEBUFFER, fb_id )
        GL.glFramebufferTexture2D( GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.texture.id, 0 )

        status = GL.glCheckFramebufferStatus( GL.GL_FRAMEBUFFER )
        for s in FRAMEBUFFER_STATUS:
            if status == FRAMEBUFFER_STATUS[s]:
                self.status = s

        GL.glClearColor( color.r, color.g, color.b, color.a )
        GL.glClear( GL.GL_COLOR_BUFFER_BIT )
        
        self.id = fb_id
        
        self.width = width
        self.height = height
        self.color = color
        self.gen_mipmaps = gen_mipmaps
    
    def use(self):
        GL.glBindFramebuffer( GL.GL_FRAMEBUFFER, self.id )

class RenderTarget:
    def __init__(self, prog_args, vao_args, fb_args):
        self.program = Program(prog_args["vertex shader path"], prog_args["fragment shader path"])
        self.vao = VertexArrayObject(self.program.id, vao_args["vertices"], vao_args["uvs"])
        self.fb = Framebuffer(fb_args["width"], fb_args["height"], fb_args["color"], fb_args["generate mipmaps"])
    
    def render(self, uniforms):
        self.program.use()
        self.vao.use()
        self.fb.use()

        self.program.set_uniforms(uniforms)

        GL.glClearColor( self.fb.color.r, self.fb.color.g, self.fb.color.b, self.fb.color.a )
        GL.glClear( GL.GL_COLOR_BUFFER_BIT )

        GL.glDrawArrays( GL.GL_TRIANGLE_STRIP, 0, 4 )

class DualFramebuffer:
    def __init__(self, width, height, color, gen_mipmaps):
        self.toggle = 0

        self.fbs = [
            Framebuffer(width, height, color, gen_mipmaps),
            Framebuffer(width, height, color, gen_mipmaps)
        ]

    def get_texture(self, i):
        return self.fbs[i].texture.id
    
    def render(self, vao, program, uniforms):
        program.use()
        vao.use()
        
        fb = self.fbs[self.toggle]
        fb.use()

        self.fbs[0 if self.toggle else 1].texture.use()
        
        program.set_uniforms(uniforms)

        GL.glDrawArrays( GL.GL_TRIANGLE_STRIP, 0, 4 )
