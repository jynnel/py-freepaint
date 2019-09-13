import os

initkeystate = '''ks["%s"] = False
'''

symcheck = '''elif ev.keysym.sym == sdl2.%s:
    keystate["%s"] = KeyPressed if ev.type == sdl2.SDL_KEYDOWN else (KeyJustPressed if ev.type == sdl2.SDL_KEYUP else KeyNotPressed)
'''

path = os.path.join(os.getcwd(), "codegen")
os.chdir(path)
print(os.getcwd())

with open("sdlkeys_bare", 'r') as infile:
    olist = []
    for line in infile.readlines():
        sdlk = line.strip('\n')
        name = line.split('_', 1)[1].lower().strip('\n')
        
        if name == "return":
            name = "enter"
        if name.isdigit():
            name = "k%s"%name
        
        olist.append(symcheck%(sdlk, name))
    
    out = ''.join(olist)
    
    # out = ''.join([case.format(line.strip('\n'), line.split('_', 1)[1].lower().strip('\n')) for line in infile.readlines()])
    # out = ''.join(["struct InputKey %s;\n"%line.split('_', 1)[1].lower().strip('\n') for line in infile.readlines()])
    # out = ''.join(['rd->input.%s.name = "%s\\0";\n'%(line.split('_', 1)[1].lower().strip('\n'), line.split('_', 1)[1].lower().strip('\n')) for line in infile.readlines()])
    with open("keycodechecks.txt", 'w') as outfile:
        outfile.write(out)
