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
