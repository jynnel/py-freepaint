from ctypes import byref, c_int
from os.path import isfile
from json import loads

import sdl2

from modules.gl.glrenderer import Renderer
from modules.input.inputstate import InputState
from modules.settings import Settings
from modules.brush import Brush

class SDLApp:
    def __init__(self, title, width, height):
        self.settings = Settings()
        self.brush = Brush()

        json = {}
        if isfile("default_settings.json"):
            with open("default_settings.json", 'r') as f:
                json = loads(f.read())
        if "settings" in json:
            self.settings.from_json(json["settings"])
        if "brush" in json:
            self.brush.from_json(json["brush"])

        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            print(sdl2.SDL_GetError())
        
        pos = sdl2.SDL_WINDOWPOS_UNDEFINED
        self.window = sdl2.SDL_CreateWindow(title.encode('ascii'), pos, pos, width, height, sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_RESIZABLE )
        self.window_size = [0, 0]

        if not self.window:
            print(sdl2.SDL_GetError())
        
        wm_info = sdl2.SDL_SysWMinfo()
        sdl2.SDL_GetVersion(wm_info.version)
        print(f"SDL2 version {wm_info.version.major}.{wm_info.version.minor}.{wm_info.version.patch}")

        self.input_state = InputState(self.settings)
        if "bindings" in json:
            for binding in json["bindings"]:
                if not "motion" in binding:
                    binding["motion"] = "none"
                self.input_state.add_keybind(self.input_state, binding["keys"], binding["motion"], binding["command"])

        sdl2.SDL_ShowCursor(sdl2.SDL_ENABLE if self.settings.show_cursor else sdl2.SDL_DISABLE)
        self.windowID = sdl2.SDL_GetWindowID(self.window)

        v = sdl2.video
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_MINOR_VERSION, 2)
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_PROFILE_MASK, v.SDL_GL_CONTEXT_PROFILE_CORE)
        self.context = sdl2.SDL_GL_CreateContext(self.window)

        self.update_window_size()
        self.renderer = Renderer(self.context, self.window_size, self.input_state)

        self.event = sdl2.SDL_Event()
        
        self.running = True

    def update_window_size(self):
        w = c_int()
        h = c_int()
        sdl2.SDL_GetWindowSize(self.window, w, h)
        self.window_size = [w.value, h.value]

    def resize_window(self):
        self.update_window_size()
        self.renderer.resize_window(self.window_size)

    def close(self):
        self.renderer.close()
        sdl2.SDL_GL_DeleteContext(self.context)
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    def get_ticks(self):
        return sdl2.SDL_GetTicks()

    def delay(self, ticks):
        sdl2.SDL_Delay(int(ticks))

    def update_input_state(self):
        self.update_mouse_state()
        self.update_mod_state()
        self.parse_events()
    
    def check_keybinds(self):
        for bind in self.input_state.keybinds:
            if bind.is_active():
                print(bind)

    def update_mouse_state(self):
        m_x = c_int()
        m_y = c_int()
        mbut_mask = sdl2.SDL_GetMouseState(byref(m_x), byref(m_y))
        mouse_state = {
            "mouse1": True if mbut_mask & sdl2.SDL_BUTTON(sdl2.SDL_BUTTON_LEFT) else False,
            "mouse2": True if mbut_mask & sdl2.SDL_BUTTON(sdl2.SDL_BUTTON_RIGHT) else False,
            "mouse3": True if mbut_mask & sdl2.SDL_BUTTON(sdl2.SDL_BUTTON_MIDDLE) else False,
            "mouse4": True if mbut_mask & sdl2.SDL_BUTTON(sdl2.SDL_BUTTON_X1) else False,
            "mouse5": True if mbut_mask & sdl2.SDL_BUTTON(sdl2.SDL_BUTTON_X2) else False
        }
        self.input_state.update_mouse_state(mouse_state, m_x.value, self.window_size[1] - m_y.value)

    def update_mod_state(self):
        mod_state = sdl2.SDL_GetModState()
        self.input_state.mod_state["ctrl"] = True if mod_state & sdl2.KMOD_CTRL else False
        self.input_state.mod_state["shift"] = True if mod_state & sdl2.KMOD_SHIFT else False
        self.input_state.mod_state["alt"] = True if mod_state & sdl2.KMOD_ALT else False

    def parse_events(self):
        while sdl2.SDL_PollEvent(byref(self.event)) != 0:
            if self.event.type == sdl2.SDL_QUIT:
                self.running = False
            elif self.event.type == sdl2.SDL_WINDOWEVENT and self.event.window.windowID == self.windowID:
                if self.event.window.event == sdl2.SDL_WINDOWEVENT_SIZE_CHANGED:
                    self.resize_window()
            elif self.event.type in (sdl2.SDL_KEYDOWN, sdl2.SDL_KEYUP):
                update_keystate(self.input_state.key_state, self.event.key)

    def swap_window(self):
        sdl2.SDL_GL_SwapWindow(self.window)

def update_keystate(keystate, ev):
    if ev.keysym.sym == sdl2.SDLK_RETURN:
        keystate["enter"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_ESCAPE:
        keystate["escape"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_BACKSPACE:
        keystate["backspace"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_TAB:
        keystate["tab"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_SPACE:
        keystate["space"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_EXCLAIM:
        keystate["exclaim"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_QUOTEDBL:
        keystate["quotedbl"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_HASH:
        keystate["hash"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_PERCENT:
        keystate["percent"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_DOLLAR:
        keystate["dollar"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AMPERSAND:
        keystate["ampersand"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_QUOTE:
        keystate["quote"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_LEFTPAREN:
        keystate["leftparen"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_RIGHTPAREN:
        keystate["rightparen"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_ASTERISK:
        keystate["asterisk"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_PLUS:
        keystate["plus"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_COMMA:
        keystate["comma"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_MINUS:
        keystate["minus"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_PERIOD:
        keystate["period"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_SLASH:
        keystate["slash"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_0:
        keystate["k0"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_1:
        keystate["k1"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_2:
        keystate["k2"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_3:
        keystate["k3"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_4:
        keystate["k4"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_5:
        keystate["k5"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_6:
        keystate["k6"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_7:
        keystate["k7"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_8:
        keystate["k8"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_9:
        keystate["k9"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_COLON:
        keystate["colon"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_SEMICOLON:
        keystate["semicolon"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_LESS:
        keystate["less"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_EQUALS:
        keystate["equals"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_GREATER:
        keystate["greater"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_QUESTION:
        keystate["question"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AT:
        keystate["at"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_LEFTBRACKET:
        keystate["leftbracket"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_BACKSLASH:
        keystate["backslash"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_RIGHTBRACKET:
        keystate["rightbracket"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_CARET:
        keystate["caret"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_UNDERSCORE:
        keystate["underscore"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_BACKQUOTE:
        keystate["backquote"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_a:
        keystate["a"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_b:
        keystate["b"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_c:
        keystate["c"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_d:
        keystate["d"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_e:
        keystate["e"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_f:
        keystate["f"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_g:
        keystate["g"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_h:
        keystate["h"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_i:
        keystate["i"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_j:
        keystate["j"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_k:
        keystate["k"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_l:
        keystate["l"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_m:
        keystate["m"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_n:
        keystate["n"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_o:
        keystate["o"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_p:
        keystate["p"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_q:
        keystate["q"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_r:
        keystate["r"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_s:
        keystate["s"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_t:
        keystate["t"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_u:
        keystate["u"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_v:
        keystate["v"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_w:
        keystate["w"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_x:
        keystate["x"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_y:
        keystate["y"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_z:
        keystate["z"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_CAPSLOCK:
        keystate["capslock"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F1:
        keystate["f1"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F2:
        keystate["f2"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F3:
        keystate["f3"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F4:
        keystate["f4"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F5:
        keystate["f5"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F6:
        keystate["f6"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F7:
        keystate["f7"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F8:
        keystate["f8"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F9:
        keystate["f9"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F10:
        keystate["f10"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F11:
        keystate["f11"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F12:
        keystate["f12"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_PRINTSCREEN:
        keystate["printscreen"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_SCROLLLOCK:
        keystate["scrolllock"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_PAUSE:
        keystate["pause"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_INSERT:
        keystate["insert"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_HOME:
        keystate["home"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_PAGEUP:
        keystate["pageup"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_DELETE:
        keystate["delete"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_END:
        keystate["end"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_PAGEDOWN:
        keystate["pagedown"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_RIGHT:
        keystate["right"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_LEFT:
        keystate["left"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_DOWN:
        keystate["down"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_UP:
        keystate["up"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_NUMLOCKCLEAR:
        keystate["numlockclear"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_DIVIDE:
        keystate["kp_divide"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_MULTIPLY:
        keystate["kp_multiply"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_MINUS:
        keystate["kp_minus"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_PLUS:
        keystate["kp_plus"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_ENTER:
        keystate["kp_enter"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_1:
        keystate["kp_1"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_2:
        keystate["kp_2"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_3:
        keystate["kp_3"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_4:
        keystate["kp_4"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_5:
        keystate["kp_5"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_6:
        keystate["kp_6"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_7:
        keystate["kp_7"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_8:
        keystate["kp_8"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_9:
        keystate["kp_9"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_0:
        keystate["kp_0"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_PERIOD:
        keystate["kp_period"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_APPLICATION:
        keystate["application"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_POWER:
        keystate["power"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_EQUALS:
        keystate["kp_equals"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F13:
        keystate["f13"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F14:
        keystate["f14"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F15:
        keystate["f15"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F16:
        keystate["f16"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F17:
        keystate["f17"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F18:
        keystate["f18"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F19:
        keystate["f19"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F20:
        keystate["f20"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F21:
        keystate["f21"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F22:
        keystate["f22"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F23:
        keystate["f23"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_F24:
        keystate["f24"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_EXECUTE:
        keystate["execute"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_HELP:
        keystate["help"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_MENU:
        keystate["menu"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_SELECT:
        keystate["select"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_STOP:
        keystate["stop"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AGAIN:
        keystate["again"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_UNDO:
        keystate["undo"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_CUT:
        keystate["cut"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_COPY:
        keystate["copy"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_PASTE:
        keystate["paste"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_FIND:
        keystate["find"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_MUTE:
        keystate["mute"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_VOLUMEUP:
        keystate["volumeup"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_VOLUMEDOWN:
        keystate["volumedown"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_COMMA:
        keystate["kp_comma"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_EQUALSAS400:
        keystate["kp_equalsas400"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_ALTERASE:
        keystate["alterase"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_SYSREQ:
        keystate["sysreq"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_CANCEL:
        keystate["cancel"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_CLEAR:
        keystate["clear"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_PRIOR:
        keystate["prior"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_RETURN2:
        keystate["return2"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_SEPARATOR:
        keystate["separator"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_OUT:
        keystate["out"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_OPER:
        keystate["oper"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_CLEARAGAIN:
        keystate["clearagain"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_CRSEL:
        keystate["crsel"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_EXSEL:
        keystate["exsel"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_00:
        keystate["kp_00"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_000:
        keystate["kp_000"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_THOUSANDSSEPARATOR:
        keystate["thousandsseparator"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_DECIMALSEPARATOR:
        keystate["decimalseparator"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_CURRENCYUNIT:
        keystate["currencyunit"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_CURRENCYSUBUNIT:
        keystate["currencysubunit"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_LEFTPAREN:
        keystate["kp_leftparen"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_RIGHTPAREN:
        keystate["kp_rightparen"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_LEFTBRACE:
        keystate["kp_leftbrace"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_RIGHTBRACE:
        keystate["kp_rightbrace"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_TAB:
        keystate["kp_tab"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_BACKSPACE:
        keystate["kp_backspace"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_A:
        keystate["kp_a"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_B:
        keystate["kp_b"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_C:
        keystate["kp_c"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_D:
        keystate["kp_d"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_E:
        keystate["kp_e"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_F:
        keystate["kp_f"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_XOR:
        keystate["kp_xor"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_POWER:
        keystate["kp_power"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_PERCENT:
        keystate["kp_percent"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_LESS:
        keystate["kp_less"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_GREATER:
        keystate["kp_greater"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_AMPERSAND:
        keystate["kp_ampersand"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_DBLAMPERSAND:
        keystate["kp_dblampersand"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_VERTICALBAR:
        keystate["kp_verticalbar"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_DBLVERTICALBAR:
        keystate["kp_dblverticalbar"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_COLON:
        keystate["kp_colon"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_HASH:
        keystate["kp_hash"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_SPACE:
        keystate["kp_space"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_AT:
        keystate["kp_at"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_EXCLAM:
        keystate["kp_exclam"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMSTORE:
        keystate["kp_memstore"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMRECALL:
        keystate["kp_memrecall"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMCLEAR:
        keystate["kp_memclear"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMADD:
        keystate["kp_memadd"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMSUBTRACT:
        keystate["kp_memsubtract"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMMULTIPLY:
        keystate["kp_memmultiply"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMDIVIDE:
        keystate["kp_memdivide"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_PLUSMINUS:
        keystate["kp_plusminus"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_CLEAR:
        keystate["kp_clear"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_CLEARENTRY:
        keystate["kp_clearentry"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_BINARY:
        keystate["kp_binary"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_OCTAL:
        keystate["kp_octal"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_DECIMAL:
        keystate["kp_decimal"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KP_HEXADECIMAL:
        keystate["kp_hexadecimal"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_LCTRL:
        keystate["lctrl"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_LSHIFT:
        keystate["lshift"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_LALT:
        keystate["lalt"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_RCTRL:
        keystate["rctrl"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_RSHIFT:
        keystate["rshift"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_RALT:
        keystate["ralt"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_MODE:
        keystate["mode"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_LGUI:
        keystate["lgui"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_RGUI:
        keystate["rgui"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AUDIONEXT:
        keystate["audionext"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AUDIOPREV:
        keystate["audioprev"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AUDIOSTOP:
        keystate["audiostop"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AUDIOPLAY:
        keystate["audioplay"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AUDIOMUTE:
        keystate["audiomute"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_MEDIASELECT:
        keystate["mediaselect"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_WWW:
        keystate["www"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_MAIL:
        keystate["mail"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_CALCULATOR:
        keystate["calculator"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_COMPUTER:
        keystate["computer"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AC_SEARCH:
        keystate["ac_search"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AC_HOME:
        keystate["ac_home"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AC_BACK:
        keystate["ac_back"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AC_FORWARD:
        keystate["ac_forward"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AC_STOP:
        keystate["ac_stop"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AC_REFRESH:
        keystate["ac_refresh"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_AC_BOOKMARKS:
        keystate["ac_bookmarks"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_BRIGHTNESSDOWN:
        keystate["brightnessdown"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_BRIGHTNESSUP:
        keystate["brightnessup"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_DISPLAYSWITCH:
        keystate["displayswitch"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KBDILLUMTOGGLE:
        keystate["kbdillumtoggle"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KBDILLUMDOWN:
        keystate["kbdillumdown"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_KBDILLUMUP:
        keystate["kbdillumup"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_EJECT:
        keystate["eject"] = True if ev.type == sdl2.SDL_KEYDOWN else False
    elif ev.keysym.sym == sdl2.SDLK_SLEEP:
        keystate["sleep"] = True if ev.type == sdl2.SDL_KEYDOWN else False
