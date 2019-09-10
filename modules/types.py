class RGBA:
    def __init__(self, r, g, b, a):
        self.r = r
        self.g = g
        self.b = b
        self.a = a
    
    def list(self):
        return [self.r, self.g, self.b, self.a]
