import numpy

def mat4_ortho(width, height):
    m = numpy.array(mat4_identity(), numpy.float32)

    m[0][0] = 2.0 / width
    m[1][1] = 2.0 / height
    m[2][2] = 2.0
    m[3][0] = -1.0
    m[3][1] = -1.0
    m[3][2]  = 1.0

    return m

def mat4_mul( m1, m2 ):
    m = numpy.array(mat4_identity(), numpy.float32)
    for i in range(4):
        for j in range(4):
            m[i][j] = 0
            for k in range(4):
                m[i][j] += m1[i][k] * m2[k][j]
    return m

def mat4_identity():
    return [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ]
