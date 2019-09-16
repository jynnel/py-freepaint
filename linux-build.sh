#!/bin/bash
BUILDDIR="build"
LINUXDIR="bin/py-freepaint-linux"
EXENAME="py-freepaint"

mkdir -p ./$BUILDDIR/$LINUXDIR
rsync -rupE default_settings.json settings.json shaders ./$BUILDDIR/$LINUXDIR
python ./codegen/build-single-source-file.py -i ./main.py -o ./build/main.pyx -p linux

cd ./$BUILDDIR

cython -v main.pyx --embed
gcc -v -Os -I /usr/include/python3.7m -o ./$LINUXDIR/$EXENAME main.c -lpython3.7m -lpthread -lm -lutil -ldl

echo
echo "*** Build completed. ***"
echo "output: $BUILDDIR/$LINUXDIR/$EXENAME"
echo "note, the settings files and shader folders are necessary for the program to run."
