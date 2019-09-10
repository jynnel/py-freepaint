import numpy

def mat4_ortho(width, height):
    m = numpy.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ], numpy.float32)

    m[0][0] = 2.0 / width
    m[1][1] = 2.0 / height
    m[2][2] = 2.0
    m[3][0] = -1.0
    m[3][1] = -1.0
    m[3][2]  = 1.0

    return m
