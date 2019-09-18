from copy import deepcopy

from modules.settings import JsonLoadable, BrushSettings

InputHistoryLength = 4

KeyJustReleased = -1
KeyNotPressed = 0
KeyPressed = 1

AxisHorizontal = 0
AxisVertical = 1

ReleaseCommands = ("view_flip", "color_pick", "swap_color", "set_brush")

class InputState:
    def __init__(self):
        self.stylus = None

        self.mpos = (0, 0)
        self.mpos_history = [(0.0,0.0), (0.0, 0.0)]
        self.mpos_w = (0, 0)
        self.mpos_w_history = [(0.0,0.0), (0.0, 0.0)]
        self.mdelta = (0, 0)
        self.key_state = {}
        init_key_state(self.key_state)

        self.update_input_history(self.mpos_history, (0.0, 0.0))

        self.found_stylus = False
        self.stylus_active = False
        self.stylus_history = []
        self.draw_history = []

        self.mod_state = {
            "ctrl": KeyNotPressed,
            "shift": KeyNotPressed,
            "alt": KeyNotPressed,
        }

        self.mouse_state = {
            "mouse_left": KeyNotPressed,
            "mouse_middle": KeyNotPressed,
            "mouse_right": KeyNotPressed,
            "mouse_x1": KeyNotPressed,
            "mouse_x2": KeyNotPressed
        }

        self.keybinds = []
        self.active_bind = None
        self.previous_bind = None
        self.active_axis = AxisHorizontal
        self.operator_start_mpos = (0, 0)
        self.operator_set_value = ""
        
        self.brush = BrushSettings()
        self.active_stroke = False
    
    def reset_key_state(self, state):
        for key in state:
            if state[key] == KeyJustReleased:
                state[key] = KeyNotPressed

    def add_keybind(self, binding):
        if not "keys" in binding or not "command" in binding:
            return
        
        if not "motion" in binding:
            binding["motion"] = "none"
        if not "on" in binding:
            if binding["command"] in ReleaseCommands:
                binding["on"] = "release"
            else:
                binding["on"] = "press"
        if not "to" in binding:
            binding["to"] = ""
        
        keys = binding["keys"]
        motion = binding["motion"]
        operator = binding["command"]
        on = KeyJustReleased if binding["on"] == "release" else KeyPressed
        to = binding["to"]
        
        self.keybinds.append(KeyBind(keys, motion, operator, on, to))

    def smooth_mpos(self, x, y):
        # smoothing with many points didn't seem to work right
        # x = x * a
        # y = y * a
        # for i in range(1, InputHistoryLength):
        #     p = self.input_state.mpos_history[-i]
        #     aexp = pow((1 - a), i)
        #     x += p[0] * aexp * a
        #     y += p[1] * aexp * a
        
        a = 1.0 - min(max(self.brush.smoothing, 0.0), 1.0) * 0.8
        p = self.mpos_history[-1]
        x = x * a + p[0] * (1 - a)
        y = y * a + p[1] * (1 - a)
        return x, y

    def update_input_history(self, history, val):
        history.append(val)

        hlen = len(history)
        if hlen < InputHistoryLength:
            history.extend(([val]*(InputHistoryLength-1)))
        elif hlen > InputHistoryLength:
            history.pop(0)

    def check_keybinds(self, deadzone):
        for bind in self.keybinds:
            if self.active_bind and self.active_bind != bind:
                continue

            key_check = True
            for key in bind.keys:
                if key in self.mod_state.keys():
                    key_check = key_check and bind.on == self.mod_state[key]
                elif key in self.mouse_state.keys():
                    key_check = key_check and bind.on == self.mouse_state[key]
                elif key in self.key_state.keys():
                    key_check = key_check and bind.on == self.key_state[key]
                else:
                    print("Unknown keybind key:", key)
                    key_check = False
            
            if key_check:
                if bind.motion in ("horizontal", "vertical"):
                    bind.md_accum[0] += self.mdelta[0]
                    bind.md_accum[1] += self.mdelta[1]
                    absx = abs(bind.md_accum[0])
                    absy = abs(bind.md_accum[1])
                    if not self.active_bind:
                        if bind.motion.startswith("h") and (absx > deadzone and absx > absy):
                            self.operator_start_mpos = self.mpos
                            self.active_axis = AxisHorizontal
                            self.active_bind = bind
                        elif bind.motion.startswith("v") and (absy > deadzone and absy > absx):
                            self.operator_start_mpos = self.mpos
                            self.active_axis = AxisVertical
                            self.active_bind = bind
                else:
                    self.active_bind = bind
            else:
                self.active_bind = None
                bind.md_accum = [0, 0]

class KeyBind:
    def __init__(self, keys, motion, operator, on, to):
        self.keys = keys
        self.motion = motion
        self.operator = operator
        self.on = on
        self.md_accum = [0, 0]
        self.to = to

def init_key_state(ks):
    ks["unknown"] = KeyNotPressed
    ks["space"] = KeyNotPressed
    ks["quote"] = KeyNotPressed
    ks["comma"] = KeyNotPressed
    ks["minus"] = KeyNotPressed
    ks["period"] = KeyNotPressed
    ks["slash"] = KeyNotPressed
    ks["0"] = KeyNotPressed
    ks["1"] = KeyNotPressed
    ks["2"] = KeyNotPressed
    ks["3"] = KeyNotPressed
    ks["4"] = KeyNotPressed
    ks["5"] = KeyNotPressed
    ks["6"] = KeyNotPressed
    ks["7"] = KeyNotPressed
    ks["8"] = KeyNotPressed
    ks["9"] = KeyNotPressed
    ks["semicolon"] = KeyNotPressed
    ks["equal"] = KeyNotPressed
    ks["a"] = KeyNotPressed
    ks["b"] = KeyNotPressed
    ks["c"] = KeyNotPressed
    ks["d"] = KeyNotPressed
    ks["e"] = KeyNotPressed
    ks["f"] = KeyNotPressed
    ks["g"] = KeyNotPressed
    ks["h"] = KeyNotPressed
    ks["i"] = KeyNotPressed
    ks["j"] = KeyNotPressed
    ks["k"] = KeyNotPressed
    ks["l"] = KeyNotPressed
    ks["m"] = KeyNotPressed
    ks["n"] = KeyNotPressed
    ks["o"] = KeyNotPressed
    ks["p"] = KeyNotPressed
    ks["q"] = KeyNotPressed
    ks["r"] = KeyNotPressed
    ks["s"] = KeyNotPressed
    ks["t"] = KeyNotPressed
    ks["u"] = KeyNotPressed
    ks["v"] = KeyNotPressed
    ks["w"] = KeyNotPressed
    ks["x"] = KeyNotPressed
    ks["y"] = KeyNotPressed
    ks["z"] = KeyNotPressed
    ks["left_bracket"] = KeyNotPressed
    ks["backslash"] = KeyNotPressed
    ks["right_bracket"] = KeyNotPressed
    ks["grave_accent"] = KeyNotPressed
    ks["world_1"] = KeyNotPressed
    ks["world_2"] = KeyNotPressed
    ks["escape"] = KeyNotPressed
    ks["enter"] = KeyNotPressed
    ks["tab"] = KeyNotPressed
    ks["backspace"] = KeyNotPressed
    ks["insert"] = KeyNotPressed
    ks["delete"] = KeyNotPressed
    ks["right"] = KeyNotPressed
    ks["left"] = KeyNotPressed
    ks["down"] = KeyNotPressed
    ks["up"] = KeyNotPressed
    ks["page_up"] = KeyNotPressed
    ks["page_down"] = KeyNotPressed
    ks["home"] = KeyNotPressed
    ks["end"] = KeyNotPressed
    ks["caps_lock"] = KeyNotPressed
    ks["scroll_lock"] = KeyNotPressed
    ks["num_lock"] = KeyNotPressed
    ks["print_screen"] = KeyNotPressed
    ks["pause"] = KeyNotPressed
    ks["f1"] = KeyNotPressed
    ks["f2"] = KeyNotPressed
    ks["f3"] = KeyNotPressed
    ks["f4"] = KeyNotPressed
    ks["f5"] = KeyNotPressed
    ks["f6"] = KeyNotPressed
    ks["f7"] = KeyNotPressed
    ks["f8"] = KeyNotPressed
    ks["f9"] = KeyNotPressed
    ks["f10"] = KeyNotPressed
    ks["f11"] = KeyNotPressed
    ks["f12"] = KeyNotPressed
    ks["f13"] = KeyNotPressed
    ks["f14"] = KeyNotPressed
    ks["f15"] = KeyNotPressed
    ks["f16"] = KeyNotPressed
    ks["f17"] = KeyNotPressed
    ks["f18"] = KeyNotPressed
    ks["f19"] = KeyNotPressed
    ks["f20"] = KeyNotPressed
    ks["f21"] = KeyNotPressed
    ks["f22"] = KeyNotPressed
    ks["f23"] = KeyNotPressed
    ks["f24"] = KeyNotPressed
    ks["f25"] = KeyNotPressed
    ks["kp_0"] = KeyNotPressed
    ks["kp_1"] = KeyNotPressed
    ks["kp_2"] = KeyNotPressed
    ks["kp_3"] = KeyNotPressed
    ks["kp_4"] = KeyNotPressed
    ks["kp_5"] = KeyNotPressed
    ks["kp_6"] = KeyNotPressed
    ks["kp_7"] = KeyNotPressed
    ks["kp_8"] = KeyNotPressed
    ks["kp_9"] = KeyNotPressed
    ks["kp_period"] = KeyNotPressed
    ks["kp_divide"] = KeyNotPressed
    ks["kp_multiply"] = KeyNotPressed
    ks["kp_subtract"] = KeyNotPressed
    ks["kp_add"] = KeyNotPressed
    ks["kp_enter"] = KeyNotPressed
    ks["kp_equal"] = KeyNotPressed
    ks["left_shift"] = KeyNotPressed
    ks["left_control"] = KeyNotPressed
    ks["left_alt"] = KeyNotPressed
    ks["left_super"] = KeyNotPressed
    ks["right_shift"] = KeyNotPressed
    ks["right_control"] = KeyNotPressed
    ks["right_alt"] = KeyNotPressed
    ks["right_super"] = KeyNotPressed
    ks["menu"] = KeyNotPressed
    ks["last"] = KeyNotPressed
