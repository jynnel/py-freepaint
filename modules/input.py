class InputState:
    def __init__(self):
        self.mpos = (0, 0)
    
    def update_mpos(self, x, y):
        self.mpos = (x, y)
