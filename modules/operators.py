from math import floor

from modules.math import vec2f_dist

class Operators:
    def __init__(self):
        pass
    
    def do(self, op, finish, renderer, input_state):
        if not op:
            return
        
        elif op == "canvas_draw":
            if finish:
                input_state.active_stroke = False
                return

            if input_state.stylus:
                pressure = input_state.stylus["Abs Pressure"]
            else:
                print("no stylus pressure 1")
                pressure = 1.0
            
            radius = input_state.brush.size * 0.5

            if input_state.draw_history:
                if input_state.mpos_w == input_state.draw_history[-1]:
                    return
                cur_mpos = input_state.mpos_w
                prev_mpos = input_state.draw_history[-1]
                num = floor(vec2f_dist(cur_mpos, prev_mpos))

                mpos_move = [(cur_mpos[0] - prev_mpos[0]) / num, (cur_mpos[1] - prev_mpos[1]) / num]

                p_pressure = input_state.pressure_history[-1] if input_state.pressure_history else 1.0
                pressure_change_increment = (pressure - p_pressure) / num
            else:
                prev_mpos = input_state.mpos_w
                num = 0
                mpos_move = [0, 0]
                print("no history pressure 1")
                p_pressure = 1.0
                pressure_change_increment = 0.0
            
            if not input_state.active_stroke:
                num = 0
                p_pressure = pressure
                prev_mpos = input_state.mpos_w
            
            opacity = input_state.brush.opacity / (radius if num else 1.0)

            for _ in range(num + 1):
                p_pressure += pressure_change_increment
                prev_mpos = [prev_mpos[0] + mpos_move[0], prev_mpos[1] + mpos_move[1]]

                self.canvas_draw(
                    renderer.canvas,
                    renderer.screen.vao,
                    input_state.brush.progs[input_state.brush.current_prog],
                    {
                        "brushcolor": input_state.brush.color,
                        "softness": input_state.brush.softness,
                        "radius": radius,
                        "pressure": p_pressure,
                        "opacity": opacity,
                        "mpos": prev_mpos,
                    }
                )
            
            input_state.update_draw_history(input_state.mpos_w)
            if input_state.stylus:
                input_state.update_pressure_history(pressure)
            
            if not input_state.active_stroke:
                input_state.active_stroke = True
        
        elif op == "canvas_clear":
            self.canvas_clear(renderer.canvas)
        
        elif op == "brush_resize":
            amount = input_state.mdelta[input_state.active_axis] * 1.5
            self.brush_resize(input_state.brush, amount)
        
        elif op == "brush_soften":
            amount = input_state.mdelta[input_state.active_axis] / 180.0
            self.brush_soften(input_state.brush, amount)

    def canvas_draw(self, canvas, vao, program, uniforms):
        canvas.render(vao, program, uniforms)
    
    def canvas_clear(self, canvas):
        canvas.clear()
    
    def brush_resize(self, brush, amount):
        brush.showcolor = True
        brush.size = max(brush.size + amount, 1.0)
    
    def brush_soften(self, brush, amount):
        brush.showcolor = True
        brush.softness = min(max(brush.softness - amount, 0.0), 1.0)
    
