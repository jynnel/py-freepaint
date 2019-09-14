from ctypes import byref, c_int
from os.path import isfile

from OpenGL import GL
from OpenGL.GL import shaders
from numpy import array, float32

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
        uniform_count = GL.glGetProgramiv(self.id, GL.GL_ACTIVE_UNIFORMS)
        for i in range(uniform_count):
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
                    # GL.glActiveTexture( GL.GL_TEXTURE0 )
                    # GL.glUniform1i( u["index"], 0 )
                    values[key].use()
                if u["type"] == GL.GL_FLOAT_MAT4:
                    GL.glUniformMatrix4fv( u["index"], 1, GL.GL_FALSE, array(values[key], dtype=float32) )
                if u["type"] == GL.GL_FLOAT_VEC4:
                    GL.glUniform4fv( u["index"], 1, array(values[key], dtype=float32) )
                if u["type"] == GL.GL_FLOAT_VEC2:
                    GL.glUniform2fv( u["index"], 1, array(values[key], dtype=float32) )
                if u["type"] == GL.GL_FLOAT:
                    GL.glUniform1f( u["index"], values[key] )
                if u["type"] == GL.GL_INT:
                    GL.glUniform1i( u["index"], values[key] )

class VertexArrayObject:
    def __init__(self, progID, verts_list, uvs_list):
        verts = array(verts_list, dtype=float32)
        uvs = array(uvs_list, dtype=float32)

        vao_id = GL.glGenVertexArrays(1)

        vxbuf_id = GL.glGenBuffers(1)
        uvbuf_id = GL.glGenBuffers(1)
        
        GL.glBindVertexArray( vao_id )
        
        GL.glBindBuffer( GL.GL_ARRAY_BUFFER, vxbuf_id )
        GL.glBufferData( GL.GL_ARRAY_BUFFER, verts.nbytes, verts, GL.GL_STATIC_DRAW)
        
        v_pos_attrib = GL.glGetAttribLocation( progID, "v_pos" )
        GL.glEnableVertexAttribArray( v_pos_attrib )
        GL.glVertexAttribPointer(
            v_pos_attrib,
            3,
            GL.GL_FLOAT,
            GL.GL_FALSE,
            0,
            None,
        )
        
        GL.glBindBuffer( GL.GL_ARRAY_BUFFER, uvbuf_id )
        GL.glBufferData( GL.GL_ARRAY_BUFFER, uvs.nbytes, uvs, GL.GL_STATIC_DRAW)
        
        v_uv_attrib = GL.glGetAttribLocation( progID, "v_uv" )
        GL.glEnableVertexAttribArray( v_uv_attrib )
        GL.glVertexAttribPointer(
            v_uv_attrib,
            2,
            GL.GL_FLOAT,
            GL.GL_FALSE,
            0,
            None,
        )

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

        self.id = vao_id

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
    def __init__(self, width, height, color, gen_mipmaps, dummy):
        self.width = width
        self.height = height
        self.color = color
        self.gen_mipmaps = gen_mipmaps

        if dummy:
            self.id = 0
            return
        
        self.texture = Texture(width, height, gen_mipmaps)
        
        fb_id = GL.glGenFramebuffers( 1 )
        GL.glBindFramebuffer( GL.GL_FRAMEBUFFER, fb_id )
        GL.glFramebufferTexture2D( GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.texture.id, 0 )

        status = GL.glCheckFramebufferStatus( GL.GL_FRAMEBUFFER )
        for s in FRAMEBUFFER_STATUS:
            if status == FRAMEBUFFER_STATUS[s]:
                self.status = s

        GL.glClearColor( color[0], color[1], color[2], color[3] )
        GL.glClear( GL.GL_COLOR_BUFFER_BIT )
        
        self.id = fb_id
        
        if gen_mipmaps:
            self.update_mipmaps()
    
    def update_mipmaps(self):
        self.use()
        self.texture.use()
        GL.glGenerateMipmap( GL.GL_TEXTURE_2D )

    def clear(self):
        GL.glBindFramebuffer( GL.GL_FRAMEBUFFER, self.id )
        GL.glClearColor( self.color[0], self.color[1], self.color[2], self.color[3] )
        GL.glClear( GL.GL_COLOR_BUFFER_BIT )

    def use(self):
        GL.glBindFramebuffer( GL.GL_FRAMEBUFFER, self.id )

class RenderTarget:
    def __init__(self, prog_args, vao_args, fb_args):
        self.program = Program(prog_args["vertex shader path"], prog_args["fragment shader path"])
        self.vao = VertexArrayObject(self.program.id, vao_args["vertices"], vao_args["uvs"])
        if "dummy" not in fb_args:
            fb_args["dummy"] = False
        self.fb = Framebuffer(fb_args["width"], fb_args["height"], fb_args["color"], fb_args["generate mipmaps"], fb_args["dummy"])
    
    def render(self, uniforms):
        self.program.use()
        self.fb.use()
        self.vao.use()

        self.program.set_uniforms(uniforms)

        GL.glClearColor( self.fb.color[0], self.fb.color[1], self.fb.color[2], self.fb.color[3] )
        GL.glClear( GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT )

        GL.glDrawArrays( GL.GL_TRIANGLE_STRIP, 0, 4 )

class DualFramebuffer:
    def __init__(self, width, height, color, gen_mipmaps):
        self.toggle = 0
        self.size = [width, height]

        self.fbs = [
            Framebuffer(width, height, color, gen_mipmaps, False),
            Framebuffer(width, height, color, gen_mipmaps, False)
        ]

    def get_texture(self, i):
        return self.fbs[i].texture.id
    
    def render(self, vao, program, uniforms):
        program.use()
        vao.use()
        
        fb = self.fbs[self.toggle]
        fb.use()

        GL.glViewport(0, 0, self.size[0], self.size[1])

        self.fbs[0 if self.toggle else 1].texture.use()
        
        program.set_uniforms(uniforms)

        GL.glDrawArrays( GL.GL_TRIANGLE_STRIP, 0, 4 )

        if fb.gen_mipmaps:
            fb.update_mipmaps()

        self.toggle = 0 if self.toggle else 1
    
    def clear(self):
        for fb in self.fbs:
            fb.clear()
