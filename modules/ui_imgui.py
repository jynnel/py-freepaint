import imgui
from imgui.integrations.sdl2 import SDL2Renderer

BrushSettingsWindow = 0
ColorSettingsWindow = 1

class UI():
    def __init__(self, window):
        imgui.create_context()
        self.impl = SDL2Renderer(window)
        self.io = imgui.get_io()
        self.visible_windows = [BrushSettingsWindow, ColorSettingsWindow]

    def want_mouse_capture(self):
        return self.io.want_capture_mouse

    def process_event(self, event):
        self.impl.process_event(event)
    
    def process_inputs(self):
        self.impl.process_inputs()

    def close(self):
        self.impl.shutdown()

    def do_ui(self, input_state):
        imgui.new_frame()

        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):
                clicked, _ = imgui.menu_item("Quit", None, False, True)
                if clicked:
                    return "quit"
                imgui.end_menu()
            if imgui.begin_menu("Window", True):
                clicked, _ = imgui.menu_item("Brush Settings", None, False, True)
                if clicked and BrushSettingsWindow not in self.visible_windows:
                    self.visible_windows.append(BrushSettingsWindow)
                clicked, _ = imgui.menu_item("Color Settings", None, False, True)
                if clicked and ColorSettingsWindow not in self.visible_windows:
                    self.visible_windows.append(ColorSettingsWindow)
                imgui.end_menu()
            imgui.end_main_menu_bar()

        b = input_state.brush
        if BrushSettingsWindow in self.visible_windows:
            _, opened = imgui.begin("Brush Settings", True)
            if not opened:
                self.visible_windows.remove(BrushSettingsWindow)
            else:
                for attr in (("size", 1.0, 80.0), ("softness", 0.0, 1.0), ("smoothing", 0.0, 1.0), ("opacity", 0.0, 1.0), ("mixamount", 0.0, 1.0)):
                    changed, val = imgui.slider_float(attr[0].capitalize(), getattr(b, attr[0]), attr[1], attr[2], "%.3f", 1.0)
                    if changed:
                        setattr(b, attr[0], val)
            imgui.end()

        if ColorSettingsWindow in self.visible_windows:
            _, opened = imgui.begin("Color Settings", True)
            if not opened:
                self.visible_windows.remove(ColorSettingsWindow)
            else:
                changed, val = imgui.color_edit3("1", b.color[0], b.color[1], b.color[2])
                if changed:
                    setattr(b, "color", (*val, 1.0))
                changed, val = imgui.color_edit3("2", b.color2[0], b.color2[1], b.color2[2])
                if changed:
                    setattr(b, "color2", (*val, 1.0))
            imgui.end()

        imgui.render()
        self.impl.render(imgui.get_draw_data())

        return ""