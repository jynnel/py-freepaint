import os

mode = "sdl"

initkeystate = '''ks["%s"] = KeyNotPressed
'''

sdl_symcheck = '''elif ev.keysym.sym == sdl2.%s:
    key_state["%s"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustReleased if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
'''

glfw_symcheck = '''elif key == glfw.%s:
    key_state["%s"] = KeyPressed if action == glfw.PRESS else (KeyJustReleased if action == glfw.RELEASE else KeyNotPressed)
'''

path = os.path.join(os.getcwd(), "codegen")
os.chdir(path)
print(os.getcwd())

if "glfw" in mode:
    path = "glfwkeys_bare"
else:
    path = "sdlkeys_bare"

with open(path, 'r') as infile:
    olist = []
    for line in infile.readlines():
        key = line.strip('\n')
        name = line.split('_', 1)[1].lower().strip('\n')
        if "glfw" in mode:
            name = name.split('_', 1)[1]
            key = key.split('_', 1)[1]

            if name == "kp_decimal": name = "kp_period"
            if name == "apostrophe": name = "quote"
            if name == "equal": name = "equals"
        
        if name == "return":
            name = "enter"
        
        if mode == "glfw":
            olist.append(glfw_symcheck%(key, name))
        elif mode == "sdl":
            olist.append(sdl_symcheck%(key, name))
        else:
            olist.append(initkeystate%name)
    
    out = ''.join(olist)
    
    # out = ''.join([case.format(line.strip('\n'), line.split('_', 1)[1].lower().strip('\n')) for line in infile.readlines()])
    # out = ''.join(["struct InputKey %s;\n"%line.split('_', 1)[1].lower().strip('\n') for line in infile.readlines()])
    # out = ''.join(['rd->input.%s.name = "%s\\0";\n'%(line.split('_', 1)[1].lower().strip('\n'), line.split('_', 1)[1].lower().strip('\n')) for line in infile.readlines()])
    with open("keycodechecks.txt", 'w') as outfile:
        outfile.write(out)
