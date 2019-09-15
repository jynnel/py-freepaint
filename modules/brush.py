from os import listdir

from modules.gl.gltypes import Program
from modules.settings import JsonLoadable

class BrushSettings(JsonLoadable):
    def __init__(self):
        self.size = 20.0
        self.softness = 1.0
        self.opacity = 1.0
        self.color = [ 0.9, 0.2, 0.4, 1.0 ]
        self.showcolor = True
        self.mixamt = 0.0

        path_v = "shaders/draw/draw.vert"
        self.progs = {}
        fragprogs = []
        for f in listdir("shaders/draw"):
            if f.endswith(".frag"):
                fragprogs.append(f.split(".")[0])
        for prog in fragprogs:
            path_f = f"shaders/draw/{prog}.frag"
            self.progs[prog] = Program(path_v, path_f)

        self.current_prog = "draw"
