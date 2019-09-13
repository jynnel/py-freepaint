KeyJustReleased = -1
KeyNotPressed = 0
KeyPressed = 1

class InputState:
    def __init__(self):
        self.mpos_history = [(0,0), (0,0)]
        self.mpos = (0, 0)
        self.mdelta = (0, 0)
        self.key_state = {}
        init_key_state(self.key_state)

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
        self.active_operator = ""

    def add_keybind(self, keys, motion, operator, on):
        self.keybinds.append(KeyBind(keys, motion, operator, on))

    def update_mouse_position(self, x, y):
        self.mpos = (x, y)
        self.mdelta = (self.mpos[0] - self.mpos_history[-1][0], self.mpos[1] - self.mpos_history[-1][1])
        self.mpos_history.append(self.mpos)
        if len(self.mpos_history) > 16:
            self.mpos_history = self.mpos_history[-16::]
    
    def check_keybinds(self, deadzone):
        for bind in self.keybinds:
            if self.active_operator and self.active_operator != bind.operator:
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
                    if bind.motion.startswith("h"):
                        if not self.active_operator and (absx > deadzone and absx > absy):
                            print(self.active_operator)
                            self.active_operator = bind.operator
                            return
                    else:
                        if not self.active_operator and (absy > deadzone and absy > absx):
                            print(self.active_operator)
                            self.active_operator = bind.operator
                            return
                else:
                    self.active_operator = bind.operator
                    return
            else:
                self.active_operator = ""
                bind.md_accum = [0, 0]

class KeyBind:
    def __init__(self, keys, motion, operator, on):
        self.keys = keys
        self.motion = motion
        self.operator = operator
        self.on = on
        self.md_accum = [0, 0]
    
    # def is_active(self, input_state):
    #     key_state = input_state.key_state
    #     mod_state = input_state.mod_state
    #     mouse_state = input_state.mouse_state
    #     md = input_state.mdelta
    #     deadzone = input_state.settings.motion_deadzone

    #     active_operator = input_state.active_operator
    #     if active_operator != "" and active_operator != self.operator:
    #         return False

    #     key_check = True
    #     for key in self.keys:
    #         if key in input_state.mod_state.keys():
    #             key_check = key_check and self.on == mod_state[key]
    #         elif key in input_state.mouse_state.keys():
    #             key_check = key_check and self.on == mouse_state[key]
    #         elif key in input_state.key_state.keys():
    #             key_check = key_check and self.on == key_state[key]
    #         else:
    #             print("Unknown keybind key:", key)
    #             key_check = False
    #     if key_check:
    #         if self.motion in ("horizontal", "vertical"):
    #             self.md_accum[0] += md[0]
    #             self.md_accum[1] += md[1]
    #             absx = abs(self.md_accum[0])
    #             absy = abs(self.md_accum[1])
    #             if self.motion.startswith("h"):
    #                 if active_operator == self.operator or (absx > deadzone and absx > absy):
    #                     input_state.active_operator = self.operator
    #                     return True
    #                 else:
    #                     return False
    #             else:
    #                 if active_operator == self.operator or (absy > deadzone and absy > absx):
    #                     input_state.active_operator = self.operator
    #                     return True
    #                 else:
    #                     return False
    #         else:
    #             input_state.active_operator = self.operator
    #             return True
    #     else:
    #         input_state.active_operator = ""
    #         self.md_accum = [0, 0]
    #         return False
    
    def __str__(self):
        return f"keys: {self.keys}, motion: {self.motion}, command: {self.operator}, on: {self.on}"

def init_key_state(ks):
    ks["enter"] = KeyNotPressed
    ks["escape"] = KeyNotPressed
    ks["backspace"] = KeyNotPressed
    ks["tab"] = KeyNotPressed
    ks["space"] = KeyNotPressed
    ks["exclaim"] = KeyNotPressed
    ks["quotedbl"] = KeyNotPressed
    ks["hash"] = KeyNotPressed
    ks["percent"] = KeyNotPressed
    ks["dollar"] = KeyNotPressed
    ks["ampersand"] = KeyNotPressed
    ks["quote"] = KeyNotPressed
    ks["leftparen"] = KeyNotPressed
    ks["rightparen"] = KeyNotPressed
    ks["asterisk"] = KeyNotPressed
    ks["plus"] = KeyNotPressed
    ks["comma"] = KeyNotPressed
    ks["minus"] = KeyNotPressed
    ks["period"] = KeyNotPressed
    ks["slash"] = KeyNotPressed
    ks["k0"] = KeyNotPressed
    ks["k1"] = KeyNotPressed
    ks["k2"] = KeyNotPressed
    ks["k3"] = KeyNotPressed
    ks["k4"] = KeyNotPressed
    ks["k5"] = KeyNotPressed
    ks["k6"] = KeyNotPressed
    ks["k7"] = KeyNotPressed
    ks["k8"] = KeyNotPressed
    ks["k9"] = KeyNotPressed
    ks["colon"] = KeyNotPressed
    ks["semicolon"] = KeyNotPressed
    ks["less"] = KeyNotPressed
    ks["equals"] = KeyNotPressed
    ks["greater"] = KeyNotPressed
    ks["question"] = KeyNotPressed
    ks["at"] = KeyNotPressed
    ks["leftbracket"] = KeyNotPressed
    ks["backslash"] = KeyNotPressed
    ks["rightbracket"] = KeyNotPressed
    ks["caret"] = KeyNotPressed
    ks["underscore"] = KeyNotPressed
    ks["backquote"] = KeyNotPressed
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
    ks["capslock"] = KeyNotPressed
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
    ks["printscreen"] = KeyNotPressed
    ks["scrolllock"] = KeyNotPressed
    ks["pause"] = KeyNotPressed
    ks["insert"] = KeyNotPressed
    ks["home"] = KeyNotPressed
    ks["pageup"] = KeyNotPressed
    ks["delete"] = KeyNotPressed
    ks["end"] = KeyNotPressed
    ks["pagedown"] = KeyNotPressed
    ks["right"] = KeyNotPressed
    ks["left"] = KeyNotPressed
    ks["down"] = KeyNotPressed
    ks["up"] = KeyNotPressed
    ks["numlockclear"] = KeyNotPressed
    ks["kp_divide"] = KeyNotPressed
    ks["kp_multiply"] = KeyNotPressed
    ks["kp_minus"] = KeyNotPressed
    ks["kp_plus"] = KeyNotPressed
    ks["kp_enter"] = KeyNotPressed
    ks["kp_1"] = KeyNotPressed
    ks["kp_2"] = KeyNotPressed
    ks["kp_3"] = KeyNotPressed
    ks["kp_4"] = KeyNotPressed
    ks["kp_5"] = KeyNotPressed
    ks["kp_6"] = KeyNotPressed
    ks["kp_7"] = KeyNotPressed
    ks["kp_8"] = KeyNotPressed
    ks["kp_9"] = KeyNotPressed
    ks["kp_0"] = KeyNotPressed
    ks["kp_period"] = KeyNotPressed
    ks["application"] = KeyNotPressed
    ks["power"] = KeyNotPressed
    ks["kp_equals"] = KeyNotPressed
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
    ks["execute"] = KeyNotPressed
    ks["help"] = KeyNotPressed
    ks["menu"] = KeyNotPressed
    ks["select"] = KeyNotPressed
    ks["stop"] = KeyNotPressed
    ks["again"] = KeyNotPressed
    ks["undo"] = KeyNotPressed
    ks["cut"] = KeyNotPressed
    ks["copy"] = KeyNotPressed
    ks["paste"] = KeyNotPressed
    ks["find"] = KeyNotPressed
    ks["mute"] = KeyNotPressed
    ks["volumeup"] = KeyNotPressed
    ks["volumedown"] = KeyNotPressed
    ks["kp_comma"] = KeyNotPressed
    ks["kp_equalsas400"] = KeyNotPressed
    ks["alterase"] = KeyNotPressed
    ks["sysreq"] = KeyNotPressed
    ks["cancel"] = KeyNotPressed
    ks["clear"] = KeyNotPressed
    ks["prior"] = KeyNotPressed
    ks["return2"] = KeyNotPressed
    ks["separator"] = KeyNotPressed
    ks["out"] = KeyNotPressed
    ks["oper"] = KeyNotPressed
    ks["clearagain"] = KeyNotPressed
    ks["crsel"] = KeyNotPressed
    ks["exsel"] = KeyNotPressed
    ks["kp_00"] = KeyNotPressed
    ks["kp_000"] = KeyNotPressed
    ks["thousandsseparator"] = KeyNotPressed
    ks["decimalseparator"] = KeyNotPressed
    ks["currencyunit"] = KeyNotPressed
    ks["currencysubunit"] = KeyNotPressed
    ks["kp_leftparen"] = KeyNotPressed
    ks["kp_rightparen"] = KeyNotPressed
    ks["kp_leftbrace"] = KeyNotPressed
    ks["kp_rightbrace"] = KeyNotPressed
    ks["kp_tab"] = KeyNotPressed
    ks["kp_backspace"] = KeyNotPressed
    ks["kp_a"] = KeyNotPressed
    ks["kp_b"] = KeyNotPressed
    ks["kp_c"] = KeyNotPressed
    ks["kp_d"] = KeyNotPressed
    ks["kp_e"] = KeyNotPressed
    ks["kp_f"] = KeyNotPressed
    ks["kp_xor"] = KeyNotPressed
    ks["kp_power"] = KeyNotPressed
    ks["kp_percent"] = KeyNotPressed
    ks["kp_less"] = KeyNotPressed
    ks["kp_greater"] = KeyNotPressed
    ks["kp_ampersand"] = KeyNotPressed
    ks["kp_dblampersand"] = KeyNotPressed
    ks["kp_verticalbar"] = KeyNotPressed
    ks["kp_dblverticalbar"] = KeyNotPressed
    ks["kp_colon"] = KeyNotPressed
    ks["kp_hash"] = KeyNotPressed
    ks["kp_space"] = KeyNotPressed
    ks["kp_at"] = KeyNotPressed
    ks["kp_exclam"] = KeyNotPressed
    ks["kp_memstore"] = KeyNotPressed
    ks["kp_memrecall"] = KeyNotPressed
    ks["kp_memclear"] = KeyNotPressed
    ks["kp_memadd"] = KeyNotPressed
    ks["kp_memsubtract"] = KeyNotPressed
    ks["kp_memmultiply"] = KeyNotPressed
    ks["kp_memdivide"] = KeyNotPressed
    ks["kp_plusminus"] = KeyNotPressed
    ks["kp_clear"] = KeyNotPressed
    ks["kp_clearentry"] = KeyNotPressed
    ks["kp_binary"] = KeyNotPressed
    ks["kp_octal"] = KeyNotPressed
    ks["kp_decimal"] = KeyNotPressed
    ks["kp_hexadecimal"] = KeyNotPressed
    ks["lctrl"] = KeyNotPressed
    ks["lshift"] = KeyNotPressed
    ks["lalt"] = KeyNotPressed
    ks["rctrl"] = KeyNotPressed
    ks["rshift"] = KeyNotPressed
    ks["ralt"] = KeyNotPressed
    ks["mode"] = KeyNotPressed
    ks["lgui"] = KeyNotPressed
    ks["rgui"] = KeyNotPressed
    ks["audionext"] = KeyNotPressed
    ks["audioprev"] = KeyNotPressed
    ks["audiostop"] = KeyNotPressed
    ks["audioplay"] = KeyNotPressed
    ks["audiomute"] = KeyNotPressed
    ks["mediaselect"] = KeyNotPressed
    ks["www"] = KeyNotPressed
    ks["mail"] = KeyNotPressed
    ks["calculator"] = KeyNotPressed
    ks["computer"] = KeyNotPressed
    ks["ac_search"] = KeyNotPressed
    ks["ac_home"] = KeyNotPressed
    ks["ac_back"] = KeyNotPressed
    ks["ac_forward"] = KeyNotPressed
    ks["ac_stop"] = KeyNotPressed
    ks["ac_refresh"] = KeyNotPressed
    ks["ac_bookmarks"] = KeyNotPressed
    ks["brightnessdown"] = KeyNotPressed
    ks["brightnessup"] = KeyNotPressed
    ks["displayswitch"] = KeyNotPressed
    ks["kbdillumtoggle"] = KeyNotPressed
    ks["kbdillumdown"] = KeyNotPressed
    ks["kbdillumup"] = KeyNotPressed
    ks["eject"] = KeyNotPressed
    ks["sleep"] = KeyNotPressed
