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
                input_state.draw_history = []
                input_state.active_stroke = False
                return

            mpw = input_state.mpos_w_history
            cur_mpos = input_state.mpos_w

            if not input_state.active_stroke:
                mpw[-2] = cur_mpos
                mpw[-1] = cur_mpos
            
            begin = ((mpw[-2][0] + mpw[-1][0]) / 2.0, (mpw[-2][1] + mpw[-1][1]) / 2.0)
            mid = mpw[-1]
            end = ((mpw[-1][0] + cur_mpos[0]) / 2.0, (mpw[-1][1] + cur_mpos[1]) / 2.0)

            num = max(floor((vec2f_dist(end, mid) + vec2f_dist(mid, begin)) / 2.0), 1)

            pressure = input_state.stylus["pressure"]
            radius = input_state.brush.size * 0.5

            p_pressure = input_state.stylus_history[-1]["pressure"] if input_state.stylus_history else pressure
            pressure_change_increment = (pressure - p_pressure) / num
            
            opacity = input_state.brush.opacity / ( radius if num > 1 else 2.0 )

            if num == 1:
                delta = (0, 0)
            else:
                delta = ((cur_mpos[0] - mpw[-1][0]) / num, (cur_mpos[1] - mpw[-1][1]) / num)
            
            motion = ( -1.0 * delta[0], -1.0 * delta[1] )
            
            if input_state.active_stroke and mid == end:
                return
            
            if input_state.active_stroke and num == 1:
                num = 0

            for i in range(num):
                p_pressure += pressure_change_increment
                
                # BUG sometimes it doesn't catch up or has bad spacing (two points equal)
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
                        "motion": motion,
                    }
                )
                input_state.update_input_history(input_state.draw_history, curve_pos)
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
        
        elif op == "view_pan":
            xy = input_state.mdelta
            renderer.view_translate(xy[0], xy[1])
        
        elif op == "view_rot":
            angle = input_state.mdelta[input_state.active_axis] * -0.005
            xy = input_state.operator_start_mpos
            renderer.view_rotate_at_point(xy[0], xy[1], angle)

        elif op == "view_zoom":
            scale = 1.0 + (input_state.mdelta[input_state.active_axis] * -0.01)
            xy = input_state.operator_start_mpos
            renderer.view_scale_at_point(xy[0], xy[1], scale)

        elif op == "color_pick":
            pass

        elif op == "view_reset":
            pass

        elif op == "view_flip":
            if finish:
                return
            
            x = input_state.mpos[0]
            renderer.view_flip_at_point(x)
        
        elif op == "set_brush":
            name = input_state.operator_set_value
            if name in input_state.brush.progs:
                print(f"Set brush: {name}")
                input_state.brush.current_prog = name
            else:
                print(f"Unknown brush: {name}")

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
    
