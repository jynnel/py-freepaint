import os
import sys

def replace_module_imports(infile, imported, platform):
    out = ""
    with open(infile, 'r') as f:
        platform_check = ""
        for line in f.readlines():
            if "platform.startswith" in line:
                if "linux" in line:
                    platform_check = "linux"
                elif "win32" in line:
                    platform_check = "win32"
            elif line.strip().startswith("from modules"):
                if platform_check and platform != platform_check:
                    platform_check = ""
                    continue
                else:
                    platform_check = ""
                importfile = "/".join(line.split()[1].split('.')) + ".py"
                if importfile not in imported.keys():
                    imported[importfile] = True
                    out += replace_module_imports(importfile, imported, platform) + "\n"
            else:
                out += line
    return out

def main(argv):
    infile = ""
    outfile = ""
    platform = ""

    for i, arg in enumerate(argv):
        if arg == "-i":
            infile = argv[i+1]
        elif arg == "-o":
            outfile = argv[i+1]
        elif arg == "-p":
            platform = argv[i+1]

    if not infile or not outfile:
        print("error: use -i 'file' and -o 'file'")
    if not platform:
        platform = "linux"
    
    imported = {}
    final = replace_module_imports(infile, imported, platform)

    with open(outfile, 'w') as f:
        f.write(final)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
