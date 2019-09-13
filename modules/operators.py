class Operators:
    def __init__(self):
        pass

    def draw(self, canvas, vao, program, uniforms):
        canvas.render(vao, program, uniforms)
    
    def clear(self, canvas):
        canvas.clear()