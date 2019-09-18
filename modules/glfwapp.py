from time import sleep, time

from sys import platform
from ctypes import byref, c_int
from os.path import isfile
from json import loads

import glfw

if platform.startswith("linux"):
    from modules.devices.xdevices import Devices
elif platform.startswith("win32"):
    from modules.devices.windevices import Devices

from modules.math import vec2f_mat4_mul_inverse
from modules.gl.glrenderer import Renderer
from modules.inputstate import InputState, KeyPressed, KeyNotPressed, KeyJustReleased, InputHistoryLength
from modules.operators import Operators
from modules.settings import Settings

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
        
        if not glfw.init():
            return
        
        print(f"GLFW version {glfw.get_version()}.")
        
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        width = self.settings.win_start_size[0]
        height = self.settings.win_start_size[1]
        
        self.window = glfw.create_window(width, height, title, None, None)
        if not self.window:
            print("GLFW couldn't create a window.")
            glfw.terminate()
            return
        
        glfw.make_context_current(self.window)
        glfw.set_window_user_pointer(self.window, self)

        # glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_NORMAL if self.settings.show_cursor else glfw.CURSOR_DISABLED )
        # cursor = glfw.create_standard_cursor(glfw.CROSSHAIR_CURSOR)
        # glfw.set_cursor(self.window, cursor)

        self.window_size = (0, 0)
        self.update_window_size()

        self.input_state = InputState()
        if "bindings" in json:
            for binding in json["bindings"]:
                self.input_state.add_keybind(binding)
        if "brush" in json:
            self.input_state.brush.from_json(json["brush"])

        self.devices = Devices()
        self.input_state.found_stylus = self.devices.add_device("stylus")

        self.renderer = Renderer(self.window_size, self.settings.canvas_size, self.input_state)

        glfw.set_error_callback(error_callback)
        glfw.set_mouse_button_callback(self.window, mouse_button_callback)
        glfw.set_key_callback(self.window, key_callback)
        glfw.set_cursor_enter_callback(self.window, cursor_enter_callback)
        glfw.set_window_size_callback(self.window, window_size_callback)
        glfw.set_window_close_callback(self.window, window_close_callback)

    @property
    def running(self):
        return not glfw.window_should_close(self.window)

    def resize_window(self):
        self.update_window_size()
        self.renderer.resize_window(self.window_size)

    def close(self):
        self.devices.close()
        self.renderer.close()
        glfw.terminate()

    def update_window_size(self):
        self.window_size = glfw.get_window_size(self.window)

    def get_ticks(self):
        return time() * 1000

    def delay(self, ticks):
        seconds = ticks / 1000
        sleep(seconds)
    
    def update_input_state(self):
        if self.input_state.found_stylus:
            self.devices.update_devices()
            self.input_state.stylus = self.devices.get_device_values("stylus")
            self.input_state.stylus_active = self.devices.is_device_active("stylus")
        self.reset_keys()
        self.update_mpos()

        glfw.poll_events()
    
    def reset_keys(self):
        self.input_state.reset_key_state(self.input_state.mouse_state)
        self.input_state.reset_key_state(self.input_state.mod_state)
        self.input_state.reset_key_state(self.input_state.key_state)
    
    def update_mpos(self):
        xy = glfw.get_cursor_pos(self.window)
        x = xy[0]
        y = self.window_size[1] - xy[1]

        x, y = self.input_state.smooth_mpos(x, y)

        if (x, y) != self.input_state.mpos_history[-1]:
            self.input_state.update_input_history(self.input_state.mpos_history, self.input_state.mpos)
            self.input_state.update_input_history(self.input_state.mpos_w_history, self.input_state.mpos_w)

        self.input_state.mpos = (x, y)
        self.input_state.mdelta = (self.input_state.mpos[0] - self.input_state.mpos_history[-1][0], self.input_state.mpos[1] - self.input_state.mpos_history[-1][1])
        self.input_state.mpos_w = vec2f_mat4_mul_inverse( self.renderer.view_transform, (x, y) )
    
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
    
    def swap_window(self):
        glfw.swap_buffers(self.window)

def error_callback(error, description):
    print(error, description)

def window_close_callback(window):
    glfw.set_window_should_close(window, True)

def window_size_callback(window, width, height):
    app = glfw.get_window_user_pointer(window)
    app.resize_window()

def cursor_enter_callback(window, entered):
    app = glfw.get_window_user_pointer(window)
    if entered:
        app.paused = False
    else:
        app.paused = True

def mouse_button_callback(window, button, action, mods):
    app = glfw.get_window_user_pointer(window)
    mouse_state = app.input_state.mouse_state
    
    if button == glfw.MOUSE_BUTTON_LEFT:
        mouse_state["mouse_left"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif button == glfw.MOUSE_BUTTON_MIDDLE:
        mouse_state["mouse_middle"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif button == glfw.MOUSE_BUTTON_RIGHT:
        mouse_state["mouse_right"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif button == glfw.MOUSE_BUTTON_4:
        mouse_state["mouse_x1"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif button == glfw.MOUSE_BUTTON_5:
        mouse_state["mouse_x2"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)


def key_callback(window, key, scancode, action, mods):
    app = glfw.get_window_user_pointer(window)
    mod_state = app.input_state.mod_state
    key_state = app.input_state.key_state

    # fixes for dvorak for example. ugly but it works well enough for now
    name = glfw.get_key_name(key, scancode)

    if name and name in "abcdefghijklmnopqrstuvwxyz":
        mod_state[name] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
        return
    
    if name and name in "',.;-/=\\][`":
        if name == "'":
            key_state["quote"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
        elif name == ",":
            key_state["comma"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
        elif name == ".":
            key_state["period"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
        elif name == ";":
            key_state["semicolon"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
        elif name == "-":
            key_state["minus"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
        elif name == "/":
            key_state["slash"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
        elif name == "=":
            key_state["equals"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
        elif name == "\\":
            key_state["backslash"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
        elif name == "]":
            key_state["right_bracket"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
        elif name == "[":
            key_state["left_bracket"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
        elif name == "`":
            key_state["grave_accent"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)

    if key in (glfw.KEY_LEFT_CONTROL, glfw.KEY_RIGHT_CONTROL):
        mod_state["ctrl"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key in (glfw.KEY_LEFT_SHIFT, glfw.KEY_RIGHT_SHIFT):
        mod_state["shift"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key in (glfw.KEY_LEFT_ALT, glfw.KEY_RIGHT_ALT):
        mod_state["alt"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_UNKNOWN:
        key_state["unknown"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_SPACE:
        key_state["space"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_APOSTROPHE:
        key_state["quote"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_COMMA:
        key_state["comma"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_MINUS:
        key_state["minus"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_PERIOD:
        key_state["period"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_SLASH:
        key_state["slash"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_0:
        key_state["0"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_1:
        key_state["1"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_2:
        key_state["2"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_3:
        key_state["3"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_4:
        key_state["4"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_5:
        key_state["5"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_6:
        key_state["6"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_7:
        key_state["7"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_8:
        key_state["8"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_9:
        key_state["9"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_SEMICOLON:
        key_state["semicolon"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_EQUAL:
        key_state["equals"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_A:
        key_state["a"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_B:
        key_state["b"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_C:
        key_state["c"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_D:
        key_state["d"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_E:
        key_state["e"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F:
        key_state["f"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_G:
        key_state["g"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_H:
        key_state["h"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_I:
        key_state["i"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_J:
        key_state["j"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_K:
        key_state["k"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_L:
        key_state["l"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_M:
        key_state["m"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_N:
        key_state["n"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_O:
        key_state["o"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_P:
        key_state["p"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_Q:
        key_state["q"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_R:
        key_state["r"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_S:
        key_state["s"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_T:
        key_state["t"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_U:
        key_state["u"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_V:
        key_state["v"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_W:
        key_state["w"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_X:
        key_state["x"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_Y:
        key_state["y"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_Z:
        key_state["z"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_LEFT_BRACKET:
        key_state["left_bracket"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_BACKSLASH:
        key_state["backslash"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_RIGHT_BRACKET:
        key_state["right_bracket"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_GRAVE_ACCENT:
        key_state["grave_accent"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_WORLD_1:
        key_state["world_1"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_WORLD_2:
        key_state["world_2"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_ESCAPE:
        key_state["escape"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_ENTER:
        key_state["enter"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_TAB:
        key_state["tab"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_BACKSPACE:
        key_state["backspace"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_INSERT:
        key_state["insert"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_DELETE:
        key_state["delete"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_RIGHT:
        key_state["right"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_LEFT:
        key_state["left"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_DOWN:
        key_state["down"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_UP:
        key_state["up"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_PAGE_UP:
        key_state["page_up"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_PAGE_DOWN:
        key_state["page_down"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_HOME:
        key_state["home"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_END:
        key_state["end"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_CAPS_LOCK:
        key_state["caps_lock"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_SCROLL_LOCK:
        key_state["scroll_lock"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_NUM_LOCK:
        key_state["num_lock"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_PRINT_SCREEN:
        key_state["print_screen"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_PAUSE:
        key_state["pause"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F1:
        key_state["f1"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F2:
        key_state["f2"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F3:
        key_state["f3"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F4:
        key_state["f4"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F5:
        key_state["f5"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F6:
        key_state["f6"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F7:
        key_state["f7"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F8:
        key_state["f8"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F9:
        key_state["f9"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F10:
        key_state["f10"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F11:
        key_state["f11"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F12:
        key_state["f12"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F13:
        key_state["f13"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F14:
        key_state["f14"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F15:
        key_state["f15"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F16:
        key_state["f16"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F17:
        key_state["f17"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F18:
        key_state["f18"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F19:
        key_state["f19"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F20:
        key_state["f20"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F21:
        key_state["f21"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F22:
        key_state["f22"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F23:
        key_state["f23"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F24:
        key_state["f24"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_F25:
        key_state["f25"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_0:
        key_state["kp_0"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_1:
        key_state["kp_1"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_2:
        key_state["kp_2"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_3:
        key_state["kp_3"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_4:
        key_state["kp_4"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_5:
        key_state["kp_5"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_6:
        key_state["kp_6"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_7:
        key_state["kp_7"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_8:
        key_state["kp_8"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_9:
        key_state["kp_9"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_DECIMAL:
        key_state["kp_period"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_DIVIDE:
        key_state["kp_divide"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_MULTIPLY:
        key_state["kp_multiply"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_SUBTRACT:
        key_state["kp_subtract"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_ADD:
        key_state["kp_add"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_ENTER:
        key_state["kp_enter"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_KP_EQUAL:
        key_state["kp_equal"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_LEFT_SHIFT:
        key_state["left_shift"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_LEFT_CONTROL:
        key_state["left_control"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_LEFT_ALT:
        key_state["left_alt"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_LEFT_SUPER:
        key_state["left_super"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_RIGHT_SHIFT:
        key_state["right_shift"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_RIGHT_CONTROL:
        key_state["right_control"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_RIGHT_ALT:
        key_state["right_alt"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_RIGHT_SUPER:
        key_state["right_super"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_MENU:
        key_state["menu"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
    elif key == glfw.KEY_LAST:
        key_state["last"] = KeyPressed if action in (glfw.PRESS, glfw.REPEAT) else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
