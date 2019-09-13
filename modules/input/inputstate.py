class InputState:
    def __init__(self, settings):
        self.settings = settings
        self.mpos_history = [(0,0), (0,0)]
        self.mpos = (0, 0)
        self.mdelta = (0, 0)
        self.key_state = {}
        init_key_state(self.key_state)

        self.mod_state = {
            "ctrl": False,
            "shift": False,
            "alt": False,
        }

        self.mouse_state = {
            "mouse1": False,
            "mouse2": False,
            "mouse3": False,
            "mouse4": False,
            "mouse5": False
        }

        self.keybinds = []

    def add_keybind(self, input_state, keys, motion, operator):
        self.keybinds.append(KeyBind(input_state, keys, motion, operator))

    def update_mouse_state(self, mouse_state, x, y):
        self.mpos = (x, y)
        self.mdelta = (self.mpos[0] - self.mpos_history[-1][0], self.mpos[1] - self.mpos_history[-1][1])
        self.mpos_history.append(self.mpos)
        if len(self.mpos_history) > 16:
            self.mpos_history = self.mpos_history[-16::]
        
        for key in mouse_state:
            self.mouse_state[key] = mouse_state[key]

class KeyBind:
    def __init__(self, input_state, keys, motion, operator):
        self.input_state = input_state
        self.keys = keys
        self.motion = motion
        self.operator = operator
        self.md_accum = [0, 0]
    
    def is_active(self):
        key_state = self.input_state.key_state
        mod_state = self.input_state.mod_state
        mouse_state = self.input_state.mouse_state
        md = self.input_state.mdelta
        deadzone = self.input_state.settings.motion_deadzone

        key_check = True
        for key in self.keys:
            if key in ("ctrl", "shift", "alt"):
                key_check = key_check & mod_state[key]
            elif key in ("mouse1", "mouse2", "mouse3", "mouse4", "mouse5"):
                key_check = key_check & mouse_state[key]
            else:
                key_check = key_check & key_state[key]
        if key_check:
            if self.motion in ("horizontal", "vertical"):
                self.md_accum[0] += md[0]
                self.md_accum[1] += md[1]
                if self.motion.startswith("h"):
                    return True if abs(self.md_accum[0]) > deadzone else False
                else:
                    return True if abs(self.md_accum[1]) > deadzone else False
            else:
                return True
        else:
            self.md_accum = [0, 0]
            return False
    
    def __str__(self):
        return f"keys: {self.keys}, motion: {self.motion}, command: {self.operator}"

def init_key_state(ks):
    ks["enter"] = False
    ks["escape"] = False
    ks["backspace"] = False
    ks["tab"] = False
    ks["space"] = False
    ks["exclaim"] = False
    ks["quotedbl"] = False
    ks["hash"] = False
    ks["percent"] = False
    ks["dollar"] = False
    ks["ampersand"] = False
    ks["quote"] = False
    ks["leftparen"] = False
    ks["rightparen"] = False
    ks["asterisk"] = False
    ks["plus"] = False
    ks["comma"] = False
    ks["minus"] = False
    ks["period"] = False
    ks["slash"] = False
    ks["k0"] = False
    ks["k1"] = False
    ks["k2"] = False
    ks["k3"] = False
    ks["k4"] = False
    ks["k5"] = False
    ks["k6"] = False
    ks["k7"] = False
    ks["k8"] = False
    ks["k9"] = False
    ks["colon"] = False
    ks["semicolon"] = False
    ks["less"] = False
    ks["equals"] = False
    ks["greater"] = False
    ks["question"] = False
    ks["at"] = False
    ks["leftbracket"] = False
    ks["backslash"] = False
    ks["rightbracket"] = False
    ks["caret"] = False
    ks["underscore"] = False
    ks["backquote"] = False
    ks["a"] = False
    ks["b"] = False
    ks["c"] = False
    ks["d"] = False
    ks["e"] = False
    ks["f"] = False
    ks["g"] = False
    ks["h"] = False
    ks["i"] = False
    ks["j"] = False
    ks["k"] = False
    ks["l"] = False
    ks["m"] = False
    ks["n"] = False
    ks["o"] = False
    ks["p"] = False
    ks["q"] = False
    ks["r"] = False
    ks["s"] = False
    ks["t"] = False
    ks["u"] = False
    ks["v"] = False
    ks["w"] = False
    ks["x"] = False
    ks["y"] = False
    ks["z"] = False
    ks["capslock"] = False
    ks["f1"] = False
    ks["f2"] = False
    ks["f3"] = False
    ks["f4"] = False
    ks["f5"] = False
    ks["f6"] = False
    ks["f7"] = False
    ks["f8"] = False
    ks["f9"] = False
    ks["f10"] = False
    ks["f11"] = False
    ks["f12"] = False
    ks["printscreen"] = False
    ks["scrolllock"] = False
    ks["pause"] = False
    ks["insert"] = False
    ks["home"] = False
    ks["pageup"] = False
    ks["delete"] = False
    ks["end"] = False
    ks["pagedown"] = False
    ks["right"] = False
    ks["left"] = False
    ks["down"] = False
    ks["up"] = False
    ks["numlockclear"] = False
    ks["kp_divide"] = False
    ks["kp_multiply"] = False
    ks["kp_minus"] = False
    ks["kp_plus"] = False
    ks["kp_enter"] = False
    ks["kp_1"] = False
    ks["kp_2"] = False
    ks["kp_3"] = False
    ks["kp_4"] = False
    ks["kp_5"] = False
    ks["kp_6"] = False
    ks["kp_7"] = False
    ks["kp_8"] = False
    ks["kp_9"] = False
    ks["kp_0"] = False
    ks["kp_period"] = False
    ks["application"] = False
    ks["power"] = False
    ks["kp_equals"] = False
    ks["f13"] = False
    ks["f14"] = False
    ks["f15"] = False
    ks["f16"] = False
    ks["f17"] = False
    ks["f18"] = False
    ks["f19"] = False
    ks["f20"] = False
    ks["f21"] = False
    ks["f22"] = False
    ks["f23"] = False
    ks["f24"] = False
    ks["execute"] = False
    ks["help"] = False
    ks["menu"] = False
    ks["select"] = False
    ks["stop"] = False
    ks["again"] = False
    ks["undo"] = False
    ks["cut"] = False
    ks["copy"] = False
    ks["paste"] = False
    ks["find"] = False
    ks["mute"] = False
    ks["volumeup"] = False
    ks["volumedown"] = False
    ks["kp_comma"] = False
    ks["kp_equalsas400"] = False
    ks["alterase"] = False
    ks["sysreq"] = False
    ks["cancel"] = False
    ks["clear"] = False
    ks["prior"] = False
    ks["return2"] = False
    ks["separator"] = False
    ks["out"] = False
    ks["oper"] = False
    ks["clearagain"] = False
    ks["crsel"] = False
    ks["exsel"] = False
    ks["kp_00"] = False
    ks["kp_000"] = False
    ks["thousandsseparator"] = False
    ks["decimalseparator"] = False
    ks["currencyunit"] = False
    ks["currencysubunit"] = False
    ks["kp_leftparen"] = False
    ks["kp_rightparen"] = False
    ks["kp_leftbrace"] = False
    ks["kp_rightbrace"] = False
    ks["kp_tab"] = False
    ks["kp_backspace"] = False
    ks["kp_a"] = False
    ks["kp_b"] = False
    ks["kp_c"] = False
    ks["kp_d"] = False
    ks["kp_e"] = False
    ks["kp_f"] = False
    ks["kp_xor"] = False
    ks["kp_power"] = False
    ks["kp_percent"] = False
    ks["kp_less"] = False
    ks["kp_greater"] = False
    ks["kp_ampersand"] = False
    ks["kp_dblampersand"] = False
    ks["kp_verticalbar"] = False
    ks["kp_dblverticalbar"] = False
    ks["kp_colon"] = False
    ks["kp_hash"] = False
    ks["kp_space"] = False
    ks["kp_at"] = False
    ks["kp_exclam"] = False
    ks["kp_memstore"] = False
    ks["kp_memrecall"] = False
    ks["kp_memclear"] = False
    ks["kp_memadd"] = False
    ks["kp_memsubtract"] = False
    ks["kp_memmultiply"] = False
    ks["kp_memdivide"] = False
    ks["kp_plusminus"] = False
    ks["kp_clear"] = False
    ks["kp_clearentry"] = False
    ks["kp_binary"] = False
    ks["kp_octal"] = False
    ks["kp_decimal"] = False
    ks["kp_hexadecimal"] = False
    ks["lctrl"] = False
    ks["lshift"] = False
    ks["lalt"] = False
    ks["rctrl"] = False
    ks["rshift"] = False
    ks["ralt"] = False
    ks["mode"] = False
    ks["lgui"] = False
    ks["rgui"] = False
    ks["audionext"] = False
    ks["audioprev"] = False
    ks["audiostop"] = False
    ks["audioplay"] = False
    ks["audiomute"] = False
    ks["mediaselect"] = False
    ks["www"] = False
    ks["mail"] = False
    ks["calculator"] = False
    ks["computer"] = False
    ks["ac_search"] = False
    ks["ac_home"] = False
    ks["ac_back"] = False
    ks["ac_forward"] = False
    ks["ac_stop"] = False
    ks["ac_refresh"] = False
    ks["ac_bookmarks"] = False
    ks["brightnessdown"] = False
    ks["brightnessup"] = False
    ks["displayswitch"] = False
    ks["kbdillumtoggle"] = False
    ks["kbdillumdown"] = False
    ks["kbdillumup"] = False
    ks["eject"] = False
    ks["sleep"] = False
