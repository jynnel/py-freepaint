from os import listdir

from modules.gl.gltypes import Program

class JsonLoadable:
    def from_json(self, json):
        for setting in json:
            setattr(self, setting, json[setting])

class Settings(JsonLoadable):
    def __init__(self):
        self.win_start_size = [580, 580]
        self.motion_deadzone = 10
        self.double_click_time = 200
        self.show_cursor = False
        self.show_debug = True
        self.rear_color = [ 0.25, 0.25, 0.25, 1.0 ]
        self.canvas_size = [ 512, 512 ]
        self.canvas_color = [ 0.4, 0.4, 0.4, 1.0 ]

class BrushSettings(JsonLoadable):
    def __init__(self):
        self.size = 20.0
        self.softness = 1.0
        self.opacity = 1.0
        self.color = [ 1.0, 1.0, 1.0, 1.0 ]
        self.color2 = [ 0.0, 0.0, 0.0, 1.0 ]
        self.showcolor = True
        self.mixamt = 0.0
        self.smoothing = 0.5

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
