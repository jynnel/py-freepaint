from copy import deepcopy
from math import floor

from numpy import array

from modules.math import vec2f_dist, vec2f_lerp

def spline_4p( t, p_1, p0, p1, p2 ):
    """ Catmull-Rom
        (Ps can be numpy vectors or arrays too: colors, curves ...)
        from https://stackoverflow.com/a/1295081
    """
    return (
          t*((2.0-t)*t - 1.0)   * p_1
        + (t*t*(3.0*t - 5.0) + 2.0) * p0
        + t*((4.0 - 3.0*t)*t + 1.0) * p1
        + (t-1.0)*t*t         * p2 ) / 2.0

class Operators:
    def __init__(self):
        pass
    
    def do(self, bind, finish, renderer, input_state):
        if not bind:
            return
        
        elif bind.operator == "canvas_draw":
            if finish:
                input_state.draw_history = []
                input_state.active_stroke = False
                return

            mpw = input_state.mpos_w_history
            cur_mpos = input_state.mpos_w

            if not input_state.active_stroke:
                mpw[-3] = cur_mpos
                mpw[-2] = cur_mpos
                mpw[-1] = cur_mpos
            
            p0 = array(mpw[-3], dtype="float32")
            p1 = array(mpw[-2], dtype="float32")
            p2 = array(mpw[-1], dtype="float32")
            p3 = array(cur_mpos, dtype="float32")

            spacing = max(input_state.brush.size / 128.0, 1.0)

            radius = input_state.brush.size * 0.5
            pressure = input_state.stylus["pressure"]
            p_pressure = input_state.stylus_history[-1]["pressure"] if input_state.stylus_history else pressure
            opacity_start = input_state.brush.opacity / radius
            
            delta = ((cur_mpos[0] - mpw[-1][0]), (cur_mpos[1] - mpw[-1][1]))
            motion = ( -0.5 * delta[0], -0.5 * delta[1] )
            
            pos_p = input_state.draw_history[-1] if input_state.active_stroke and input_state.draw_history else cur_mpos
            
            if input_state.active_stroke and p3[0] == p2[0] and p3[1] == p2[1]:
                return

            t = 0.0
            t_inc = 0.001
            while t < 1.0:
                t += t_inc
                xy = spline_4p(t, p0, p1, p2, p3)

                dist = min(vec2f_dist( xy, pos_p ), spacing)
                if dist < spacing:
                    continue
                
                opacity = opacity_start * dist
                pos_p = xy

                renderer.canvas.render(
                    renderer.screen.vao,
                    input_state.brush.progs[input_state.brush.current_prog],
                    {
                        "brushcolor": input_state.brush.color,
                        "softness": input_state.brush.softness,
                        "radius": radius,
                        "pressure": p_pressure,
                        "opacity": opacity,
                        "mpos": xy,
                        "motion": motion,
                    }
                )
                input_state.update_input_history(input_state.draw_history, xy)
                input_state.update_input_history(input_state.stylus_history, input_state.stylus)
            
            input_state.active_stroke = True
        
        elif bind.operator == "canvas_clear":
            renderer.canvas.clear()
        
        elif bind.operator == "brush_resize":
            brush = input_state.brush
            
            if finish:
                brush.showcolor = False
                return

            brush.showcolor = True
            amount = (input_state.mdelta[input_state.active_axis] * 1.5) / renderer.view_scale_amount
            brush.size = max(brush.size + amount, 1.0)
        
        elif bind.operator == "brush_soften":
            brush = input_state.brush

            if finish:
                brush.showcolor = False
                return
            
            brush.showcolor = True
            amount = input_state.mdelta[input_state.active_axis] / 180.0
            brush.softness = min(max(brush.softness - amount, 0.0), 1.0)
        
        elif bind.operator == "view_pan":
            xy = input_state.mdelta
            renderer.view_translate(xy[0], xy[1])
        
        elif bind.operator == "view_rot":
            angle = input_state.mdelta[input_state.active_axis] * -0.005
            xy = input_state.operator_start_mpos
            renderer.view_rotate_at_point(xy[0], xy[1], angle)

        elif bind.operator == "view_zoom":
            scale = 1.0 + (input_state.mdelta[input_state.active_axis] * -0.01)
            xy = input_state.operator_start_mpos
            renderer.view_scale_at_point(xy[0], xy[1], scale)

        elif bind.operator == "color_pick":
            if finish:
                return
            xy = input_state.mpos
            input_state.brush.color = renderer.screen.read_pixel(xy[0], xy[1])

        elif bind.operator == "view_reset":
            if finish:
                return
            
            renderer.view_reset()

        elif bind.operator == "view_flip":
            if finish:
                return
            
            x = input_state.mpos[0]
            renderer.view_flip_at_point(x)
        
        elif bind.operator == "set_brush":
            if finish:
                return
            
            name = input_state.active_bind.to
            if name in input_state.brush.progs:
                print(f"Set brush: {name}")
                input_state.brush.current_prog = name
            else:
                print(f"Unknown brush: {name}")
        
        elif bind.operator == "swap_color":
            if finish:
                return
            
            brush = input_state.brush

            print("swapping colors")
            temp = deepcopy(brush.color)
            brush.color = brush.color2
            brush.color2 = temp
            print(brush.color)
