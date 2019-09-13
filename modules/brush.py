from modules.settings import JsonLoadable

class Brush(JsonLoadable):
    def __init__(self):
        self.size = 20.0
        self.softness = 1.0
        self.opacity = 1.0
        self.color = [ 0.9, 0.2, 0.4, 1.0 ]
        self.showcolor = True
        self.mixamt = 0.0
