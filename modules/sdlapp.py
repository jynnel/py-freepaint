from sys import platform
from ctypes import byref, c_int
from os.path import isfile
from json import loads

import sdl2

if platform.startswith("linux"):
    from modules.devices.xdevices import Devices
elif platform.startswith("win32"):
    from modules.devices.windevices import Devices

from modules.math import vec2f_mat4_mul_inverse
from modules.gl.glrenderer import Renderer
from modules.inputstate import InputState, KeyPressed, KeyNotPressed, KeyJustReleased, InputHistoryLength
from modules.operators import Operators
from modules.settings import Settings
from modules.ui_imgui import UI

class App:
    def __init__(self, title):
        self.paused = False
        self.settings = Settings()
        self.ops = Operators()

        json = {}
        if isfile("settings.json"):
            with open("settings.json", 'r') as f:
                json = loads(f.read())
        elif isfile("default_settings.json"):
            with open("default_settings.json", 'r') as f:
                json = loads(f.read())
        if "settings" in json:
            self.settings.from_json(json["settings"])
        
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            print(sdl2.SDL_GetError())
        
        v = sdl2.video
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_MINOR_VERSION, 3)
        v.SDL_GL_SetAttribute(v.SDL_GL_CONTEXT_PROFILE_MASK, v.SDL_GL_CONTEXT_PROFILE_CORE)

        width = self.settings.win_start_size[0]
        height = self.settings.win_start_size[1]
        pos = sdl2.SDL_WINDOWPOS_UNDEFINED
        self.window = sdl2.SDL_CreateWindow(title.encode('ascii'), pos, pos, width, height, sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_RESIZABLE )

        if not self.window:
            print(sdl2.SDL_GetError())
        
        self.window_size = [0, 0]
        self.update_window_size()
        self.windowID = sdl2.SDL_GetWindowID(self.window)

        wm_info = sdl2.SDL_SysWMinfo()
        sdl2.SDL_GetVersion(wm_info.version)
        print(f"SDL2 version {wm_info.version.major}.{wm_info.version.minor}.{wm_info.version.patch}")

        self.cursor_crosshair = sdl2.SDL_CreateSystemCursor( sdl2.SDL_SYSTEM_CURSOR_CROSSHAIR )
        self.cursor_arrow = sdl2.SDL_CreateSystemCursor( sdl2.SDL_SYSTEM_CURSOR_ARROW )
        self.set_cursor(self.cursor_crosshair)
        self.set_cursor_visibility(self.settings.show_cursor)
        
        self.context = sdl2.SDL_GL_CreateContext(self.window)

        self.input_state = InputState()
        if "bindings" in json:
            for binding in json["bindings"]:
                self.input_state.add_keybind(binding)
        if "brush" in json:
            self.input_state.brush.from_json(json["brush"])

        self.devices = Devices()
        self.input_state.found_stylus = self.devices.add_device("stylus")

        self.renderer = Renderer(self.window_size, self.settings.canvas_size, self.input_state)

        self.event = sdl2.SDL_Event()
        
        self.running = True

        self.ui = UI(self.window)

    def update_window_size(self):
        w = c_int()
        h = c_int()
        sdl2.SDL_GetWindowSize(self.window, w, h)
        self.window_size = [w.value, h.value]

    def resize_window(self):
        self.update_window_size()
        self.renderer.resize_window(self.window_size)

    def close(self):
        self.devices.close()
        self.renderer.close()
        self.ui.close()
        sdl2.SDL_GL_DeleteContext(self.context)
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    def get_ticks(self):
        return sdl2.SDL_GetTicks()

    def delay(self, ticks):
        sdl2.SDL_Delay(int(ticks))

    def update_input_state(self):
        if self.input_state.found_stylus:
            self.devices.update_devices()
            self.input_state.stylus = self.devices.get_device_values("stylus")
            self.input_state.stylus_active = self.devices.is_device_active("stylus")
        self.parse_events()
    
    def check_keybinds_and_run_operators(self):
        self.input_state.previous_bind = self.input_state.active_bind
        self.input_state.check_keybinds(self.settings.motion_deadzone)
        
        finish = False
        if self.input_state.active_bind == None and self.input_state.previous_bind:
            finish = True
            self.input_state.active_bind = self.input_state.previous_bind
        
        if self.input_state.active_bind:
            self.ops.do(self.input_state.active_bind, finish, self.renderer, self.input_state)
        
        if finish:
            self.input_state.active_bind = None

    def render(self):
        self.renderer.render()
        result = self.ui.do_ui(self.input_state)
        if result == "quit":
            self.running = False

    def show_cursor(self):
        sdl2.SDL_ShowCursor(sdl2.SDL_ENABLE)

    def set_cursor(self, cursor):
        sdl2.SDL_SetCursor(cursor)

    def set_cursor_visibility(self, to):
        sdl2.SDL_ShowCursor(sdl2.SDL_ENABLE if to else sdl2.SDL_DISABLE)

    def parse_events(self):
        self.input_state.reset_key_state(self.input_state.mouse_state)
        self.input_state.reset_key_state(self.input_state.mod_state)
        self.input_state.reset_key_state(self.input_state.key_state)

        if self.ui.is_any_window_hovered():
            self.set_cursor(self.cursor_arrow)
            self.set_cursor_visibility(True)
        else:
            self.set_cursor(self.cursor_crosshair)
            self.set_cursor_visibility(self.settings.show_cursor)

        while sdl2.SDL_PollEvent(byref(self.event)) != 0:
            if self.event.type == sdl2.SDL_QUIT:
                self.running = False
            elif self.event.type == sdl2.SDL_WINDOWEVENT and self.event.window.windowID == self.windowID:
                if self.event.window.event == sdl2.SDL_WINDOWEVENT_SIZE_CHANGED:
                    self.resize_window()
                elif self.event.window.event == sdl2.SDL_WINDOWEVENT_ENTER:
                    self.paused = False
                elif self.event.window.event == sdl2.SDL_WINDOWEVENT_LEAVE:
                    self.paused = True
            elif self.event.type in (sdl2.SDL_KEYDOWN, sdl2.SDL_KEYUP):
                update_key_state(self.input_state.key_state, self.input_state.mod_state, self.event.key)
            elif self.event.type in (sdl2.SDL_MOUSEBUTTONDOWN, sdl2.SDL_MOUSEBUTTONUP):
                if not self.ui.want_mouse_capture():
                    update_mouse_state(self.input_state.mouse_state, self.event)
            self.ui.process_event(self.event)
        self.ui.process_inputs()
        
        m_x = c_int()
        m_y = c_int()
        sdl2.SDL_GetMouseState(byref(m_x), byref(m_y))
        x = m_x.value
        y = self.window_size[1] - m_y.value

        x, y = self.input_state.smooth_mpos(x, y)

        if (x, y) != self.input_state.mpos_history[-1]:
            self.input_state.update_input_history(self.input_state.mpos_history, self.input_state.mpos)
            self.input_state.update_input_history(self.input_state.mpos_w_history, self.input_state.mpos_w)

        self.input_state.mpos = (x, y)
        self.input_state.mdelta = (self.input_state.mpos[0] - self.input_state.mpos_history[-1][0], self.input_state.mpos[1] - self.input_state.mpos_history[-1][1])
        self.input_state.mpos_w = vec2f_mat4_mul_inverse( self.renderer.view_transform, (x, y) )

    def swap_window(self):
        sdl2.SDL_GL_SwapWindow(self.window)

def update_mouse_state(mouse_state, ev):
    if ev.button.button == sdl2.SDL_BUTTON_LEFT:
        mouse_state["mouse_left"] = KeyPressed if ev.type == sdl2.SDL_MOUSEBUTTONDOWN else (KeyJustReleased if ev.type == sdl2.SDL_MOUSEBUTTONUP else KeyNotPressed)
    elif ev.button.button == sdl2.SDL_BUTTON_MIDDLE:
        mouse_state["mouse_middle"] = KeyPressed if ev.type == sdl2.SDL_MOUSEBUTTONDOWN else (KeyJustReleased if ev.type == sdl2.SDL_MOUSEBUTTONUP else KeyNotPressed)
    elif ev.button.button == sdl2.SDL_BUTTON_RIGHT:
        mouse_state["mouse_right"] = KeyPressed if ev.type == sdl2.SDL_MOUSEBUTTONDOWN else (KeyJustReleased if ev.type == sdl2.SDL_MOUSEBUTTONUP else KeyNotPressed)
    elif ev.button.button == sdl2.SDL_BUTTON_X1:
        mouse_state["mouse_x1"] = KeyPressed if ev.type == sdl2.SDL_MOUSEBUTTONDOWN else (KeyJustReleased if ev.type == sdl2.SDL_MOUSEBUTTONUP else KeyNotPressed)
    elif ev.button.button == sdl2.SDL_BUTTON_X2:
        mouse_state["mouse_x2"] = KeyPressed if ev.type == sdl2.SDL_MOUSEBUTTONDOWN else (KeyJustReleased if ev.type == sdl2.SDL_MOUSEBUTTONUP else KeyNotPressed)

def update_key_state(key_state, mod_state, ev):
    if ev.keysym.sym in (sdl2.SDLK_LCTRL, sdl2.SDLK_RCTRL):
        mod_state["ctrl"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym in (sdl2.SDLK_LSHIFT, sdl2.SDLK_RSHIFT):
        mod_state["shift"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym in (sdl2.SDLK_LALT, sdl2.SDLK_RALT):
        mod_state["alt"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_RETURN:
        key_state["enter"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_ESCAPE:
        key_state["escape"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_BACKSPACE:
        key_state["backspace"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_TAB:
        key_state["tab"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_SPACE:
        key_state["space"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_EXCLAIM:
        key_state["exclaim"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_QUOTEDBL:
        key_state["quotedbl"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_HASH:
        key_state["hash"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_PERCENT:
        key_state["percent"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_DOLLAR:
        key_state["dollar"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AMPERSAND:
        key_state["ampersand"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_QUOTE:
        key_state["quote"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_LEFTPAREN:
        key_state["leftparen"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_RIGHTPAREN:
        key_state["rightparen"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_ASTERISK:
        key_state["asterisk"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_PLUS:
        key_state["plus"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_COMMA:
        key_state["comma"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_MINUS:
        key_state["minus"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_PERIOD:
        key_state["period"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_SLASH:
        key_state["slash"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_0:
        key_state["0"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_1:
        key_state["1"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_2:
        key_state["2"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_3:
        key_state["3"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_4:
        key_state["4"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_5:
        key_state["5"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_6:
        key_state["6"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_7:
        key_state["7"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_8:
        key_state["8"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_9:
        key_state["9"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_COLON:
        key_state["colon"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_SEMICOLON:
        key_state["semicolon"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_LESS:
        key_state["less"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_EQUALS:
        key_state["equals"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_GREATER:
        key_state["greater"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_QUESTION:
        key_state["question"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AT:
        key_state["at"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_LEFTBRACKET:
        key_state["leftbracket"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_BACKSLASH:
        key_state["backslash"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_RIGHTBRACKET:
        key_state["rightbracket"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_CARET:
        key_state["caret"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_UNDERSCORE:
        key_state["underscore"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_BACKQUOTE:
        key_state["backquote"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_a:
        key_state["a"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_b:
        key_state["b"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_c:
        key_state["c"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_d:
        key_state["d"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_e:
        key_state["e"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_f:
        key_state["f"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_g:
        key_state["g"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_h:
        key_state["h"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_i:
        key_state["i"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_j:
        key_state["j"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_k:
        key_state["k"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_l:
        key_state["l"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_m:
        key_state["m"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_n:
        key_state["n"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_o:
        key_state["o"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_p:
        key_state["p"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_q:
        key_state["q"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_r:
        key_state["r"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_s:
        key_state["s"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_t:
        key_state["t"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_u:
        key_state["u"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_v:
        key_state["v"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_w:
        key_state["w"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_x:
        key_state["x"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_y:
        key_state["y"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_z:
        key_state["z"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_CAPSLOCK:
        key_state["capslock"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F1:
        key_state["f1"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F2:
        key_state["f2"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F3:
        key_state["f3"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F4:
        key_state["f4"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F5:
        key_state["f5"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F6:
        key_state["f6"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F7:
        key_state["f7"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F8:
        key_state["f8"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F9:
        key_state["f9"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F10:
        key_state["f10"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F11:
        key_state["f11"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F12:
        key_state["f12"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_PRINTSCREEN:
        key_state["printscreen"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_SCROLLLOCK:
        key_state["scrolllock"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_PAUSE:
        key_state["pause"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_INSERT:
        key_state["insert"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_HOME:
        key_state["home"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_PAGEUP:
        key_state["pageup"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_DELETE:
        key_state["delete"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_END:
        key_state["end"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_PAGEDOWN:
        key_state["pagedown"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_RIGHT:
        key_state["right"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_LEFT:
        key_state["left"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_DOWN:
        key_state["down"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_UP:
        key_state["up"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_NUMLOCKCLEAR:
        key_state["numlockclear"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_DIVIDE:
        key_state["kp_divide"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_MULTIPLY:
        key_state["kp_multiply"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_MINUS:
        key_state["kp_minus"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_PLUS:
        key_state["kp_plus"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_ENTER:
        key_state["kp_enter"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_1:
        key_state["kp_1"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_2:
        key_state["kp_2"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_3:
        key_state["kp_3"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_4:
        key_state["kp_4"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_5:
        key_state["kp_5"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_6:
        key_state["kp_6"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_7:
        key_state["kp_7"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_8:
        key_state["kp_8"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_9:
        key_state["kp_9"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_0:
        key_state["kp_0"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_PERIOD:
        key_state["kp_period"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_APPLICATION:
        key_state["application"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_POWER:
        key_state["power"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_EQUALS:
        key_state["kp_equals"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F13:
        key_state["f13"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F14:
        key_state["f14"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F15:
        key_state["f15"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F16:
        key_state["f16"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F17:
        key_state["f17"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F18:
        key_state["f18"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F19:
        key_state["f19"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F20:
        key_state["f20"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F21:
        key_state["f21"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F22:
        key_state["f22"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F23:
        key_state["f23"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_F24:
        key_state["f24"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_EXECUTE:
        key_state["execute"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_HELP:
        key_state["help"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_MENU:
        key_state["menu"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_SELECT:
        key_state["select"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_STOP:
        key_state["stop"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AGAIN:
        key_state["again"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_UNDO:
        key_state["undo"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_CUT:
        key_state["cut"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_COPY:
        key_state["copy"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_PASTE:
        key_state["paste"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_FIND:
        key_state["find"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_MUTE:
        key_state["mute"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_VOLUMEUP:
        key_state["volumeup"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_VOLUMEDOWN:
        key_state["volumedown"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_COMMA:
        key_state["kp_comma"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_EQUALSAS400:
        key_state["kp_equalsas400"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_ALTERASE:
        key_state["alterase"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_SYSREQ:
        key_state["sysreq"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_CANCEL:
        key_state["cancel"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_CLEAR:
        key_state["clear"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_PRIOR:
        key_state["prior"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_RETURN2:
        key_state["return2"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_SEPARATOR:
        key_state["separator"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_OUT:
        key_state["out"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_OPER:
        key_state["oper"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_CLEARAGAIN:
        key_state["clearagain"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_CRSEL:
        key_state["crsel"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_EXSEL:
        key_state["exsel"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_00:
        key_state["kp_00"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_000:
        key_state["kp_000"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_THOUSANDSSEPARATOR:
        key_state["thousandsseparator"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_DECIMALSEPARATOR:
        key_state["decimalseparator"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_CURRENCYUNIT:
        key_state["currencyunit"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_CURRENCYSUBUNIT:
        key_state["currencysubunit"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_LEFTPAREN:
        key_state["kp_leftparen"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_RIGHTPAREN:
        key_state["kp_rightparen"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_LEFTBRACE:
        key_state["kp_leftbrace"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_RIGHTBRACE:
        key_state["kp_rightbrace"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_TAB:
        key_state["kp_tab"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_BACKSPACE:
        key_state["kp_backspace"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_A:
        key_state["kp_a"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_B:
        key_state["kp_b"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_C:
        key_state["kp_c"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_D:
        key_state["kp_d"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_E:
        key_state["kp_e"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_F:
        key_state["kp_f"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_XOR:
        key_state["kp_xor"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_POWER:
        key_state["kp_power"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_PERCENT:
        key_state["kp_percent"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_LESS:
        key_state["kp_less"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_GREATER:
        key_state["kp_greater"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_AMPERSAND:
        key_state["kp_ampersand"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_DBLAMPERSAND:
        key_state["kp_dblampersand"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_VERTICALBAR:
        key_state["kp_verticalbar"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_DBLVERTICALBAR:
        key_state["kp_dblverticalbar"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_COLON:
        key_state["kp_colon"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_HASH:
        key_state["kp_hash"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_SPACE:
        key_state["kp_space"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_AT:
        key_state["kp_at"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_EXCLAM:
        key_state["kp_exclam"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMSTORE:
        key_state["kp_memstore"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMRECALL:
        key_state["kp_memrecall"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMCLEAR:
        key_state["kp_memclear"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMADD:
        key_state["kp_memadd"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMSUBTRACT:
        key_state["kp_memsubtract"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMMULTIPLY:
        key_state["kp_memmultiply"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_MEMDIVIDE:
        key_state["kp_memdivide"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_PLUSMINUS:
        key_state["kp_plusminus"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_CLEAR:
        key_state["kp_clear"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_CLEARENTRY:
        key_state["kp_clearentry"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_BINARY:
        key_state["kp_binary"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_OCTAL:
        key_state["kp_octal"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_DECIMAL:
        key_state["kp_decimal"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KP_HEXADECIMAL:
        key_state["kp_hexadecimal"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_LCTRL:
        key_state["lctrl"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_LSHIFT:
        key_state["lshift"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_LALT:
        key_state["lalt"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_RCTRL:
        key_state["rctrl"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_RSHIFT:
        key_state["rshift"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_RALT:
        key_state["ralt"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_MODE:
        key_state["mode"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_LGUI:
        key_state["lgui"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_RGUI:
        key_state["rgui"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AUDIONEXT:
        key_state["audionext"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AUDIOPREV:
        key_state["audioprev"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AUDIOSTOP:
        key_state["audiostop"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AUDIOPLAY:
        key_state["audioplay"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AUDIOMUTE:
        key_state["audiomute"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_MEDIASELECT:
        key_state["mediaselect"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_WWW:
        key_state["www"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_MAIL:
        key_state["mail"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_CALCULATOR:
        key_state["calculator"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_COMPUTER:
        key_state["computer"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AC_SEARCH:
        key_state["ac_search"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AC_HOME:
        key_state["ac_home"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AC_BACK:
        key_state["ac_back"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AC_FORWARD:
        key_state["ac_forward"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AC_STOP:
        key_state["ac_stop"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AC_REFRESH:
        key_state["ac_refresh"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_AC_BOOKMARKS:
        key_state["ac_bookmarks"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_BRIGHTNESSDOWN:
        key_state["brightnessdown"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_BRIGHTNESSUP:
        key_state["brightnessup"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_DISPLAYSWITCH:
        key_state["displayswitch"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KBDILLUMTOGGLE:
        key_state["kbdillumtoggle"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KBDILLUMDOWN:
        key_state["kbdillumdown"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_KBDILLUMUP:
        key_state["kbdillumup"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_EJECT:
        key_state["eject"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
    elif ev.keysym.sym == sdl2.SDLK_SLEEP:
        key_state["sleep"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
