from math import floor

from modules.math import vec2f_dist, vec2f_lerp

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

            pressure = input_state.stylus["pressure"]
            radius = input_state.brush.size * 0.5
            cur_mpos = input_state.mpos_w
            prev_mpos = input_state.mpos_w_history[-2]
            
            if input_state.active_stroke and cur_mpos == prev_mpos:
                return
            
            num = max(floor((vec2f_dist(cur_mpos, prev_mpos) + vec2f_dist(prev_mpos, input_state.mpos_w_history[-3])) / 2.0), 1)

            p_pressure = input_state.stylus_history[-1]["pressure"] if input_state.stylus_history else pressure
            pressure_change_increment = (pressure - p_pressure) / num
            
            opacity = input_state.brush.opacity / ( radius if num > 1 else 2.0 )
            
            mpw = input_state.mpos_w_history
            begin = ((mpw[-3][0] + mpw[-2][0]) / 2.0, (mpw[-3][1] + mpw[-2][1]) / 2.0)
            mid = mpw[-2]
            end = ((mpw[-2][0] + mpw[-1][0]) / 2.0, (mpw[-2][1] + mpw[-1][1]) / 2.0)
            
            if input_state.active_stroke and num == 1:
                num = 0

            for i in range(num):
                p_pressure += pressure_change_increment
                
                # TODO implement an actual curve algorithm
                curve_t = float(i) / float(num)
                curve_pos = vec2f_lerp( vec2f_lerp(begin, mid, curve_t), vec2f_lerp(mid, end, curve_t), curve_t )

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
                        "mpos": curve_pos,
                    }
                )
            
            input_state.update_input_history(input_state.stylus_history, input_state.stylus)
            
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
    
