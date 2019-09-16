from copy import deepcopy
from math import sqrt, cos, sin

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

def mat4_translate( m, x, y, z ):
    m[3][0] += x
    m[3][1] += y
    m[3][2] += z

def mat4_print( m ):
    s = ""
    for i in range(4):
        for j in range(4):
            s += "%.6f, "%m[j][i]
        s += "\n"
    print(s)

def mat4_identity():
    return [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ]

def mat4_rotation_determinant( m ):
    det = 0.0
    for i in range(3):
        det = det + (m[0][i] * (m[1][(i+1)%3] * m[2][(i+2)%3] - m[1][(i+2)%3] * m[2][(i+1)%3]))
    return det

def vec2f_mat4_mul_inverse( m, v ):
    det = mat4_rotation_determinant( m )
    det = 1.0 / det

    # since I'm only using x and y thankfully only need to get cofactor of top left 4.
    # inverse cofactor though, so *1/det
    icf00 =  ((m[1][1]*m[2][2]) - (m[2][1]*m[1][2])) * det
    icf01 = -((m[0][1]*m[2][2]) - (m[2][1]*m[0][2])) * det
    icf10 = -((m[1][0]*m[2][2]) - (m[2][0]*m[1][2])) * det
    icf11 =  ((m[0][0]*m[2][2]) - (m[2][0]*m[0][2])) * det
    
    x = (icf00*v[0] + icf10*v[1]) - (icf00*m[3][0] + icf10*m[3][1])
    y = (icf01*v[0] + icf11*v[1]) - (icf01*m[3][0] + icf11*m[3][1])
    return (x, y)

def vec2f_dist( a, b ):
    return sqrt(pow(a[0] - b[0], 2) + pow(a[1] - b[1], 2))

def vec2f_lerp( a, b, t ):
    return ( a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

def mat4_scale_at_point( m, x, y, s ):
    if s != 1.0:
        m[0][0] *= s
        m[0][1] *= s
        m[0][2] *= s
        m[1][0] *= s
        m[1][1] *= s
        m[1][2] *= s
        m[2][0] *= s
        m[2][1] *= s
        m[2][2] *= s
        m[3][0] -= x
        m[3][1] -= y
        m[3][0] *= s
        m[3][1] *= s
        m[3][0] += x
        m[3][1] += y

def mat4_rotate_z_at_point( m, x, y, a ):
    o = deepcopy(m)

    m[0][0] = o[0][0] *  cos(a) + o[0][1] *  sin(a) + o[0][2]*0
    m[0][1] = o[0][0] * -sin(a) + o[0][1] *  cos(a) + o[0][2]*0
    m[0][2] = o[0][0] *    0    + o[0][1] *    0    + o[0][2]*1
    
    m[1][0] = o[1][0] *  cos(a) + o[1][1] *  sin(a) + o[1][2]*0
    m[1][1] = o[1][0] * -sin(a) + o[1][1] *  cos(a) + o[1][2]*0
    m[1][2] = o[1][0] *    0    + o[1][1] *    0    + o[1][2]*1
    
    m[2][0] = o[2][0] *  cos(a) + o[2][1] *  sin(a) + o[2][2]*0
    m[2][1] = o[2][0] * -sin(a) + o[2][1] *  cos(a) + o[2][2]*0
    m[2][2] = o[2][0] *    0    + o[2][1] *    0    + o[2][2]*1
    
    o[3][0] -= x
    o[3][1] -= y
    m[3][0] = o[3][0] *  cos(a) + o[3][1] *  sin(a) + o[3][2]*0
    m[3][1] = o[3][0] * -sin(a) + o[3][1] *  cos(a) + o[3][2]*0
    m[3][0] += x
    m[3][1] += y

def mat4_remove_scale( m, s ):
    m[0][0] /= s
    m[0][1] /= s
    m[0][2] /= s
    m[1][0] /= s
    m[1][1] /= s
    m[1][2] /= s
    m[2][0] /= s
    m[2][1] /= s
    m[2][2] /= s

def mat4_scale( m, s ):
    m[0][0] *= s
    m[0][1] *= s
    m[0][2] *= s
    m[1][0] *= s
    m[1][1] *= s
    m[1][2] *= s
    m[2][0] *= s
    m[2][1] *= s
    m[2][2] *= s

def mat4_rotation_invert( m ):
    o = deepcopy(m)
    
    det = 1.0 / mat4_rotation_determinant( m )
    
    for i in range(3):
        for j in range(3):
            m[i][j] = ((o[(i+1)%3][(j+1)%3] * o[(i+2)%3][(j+2)%3]) - (o[(i+1)%3][(j+2)%3]*o[(i+2)%3][(j+1)%3])) * det
    
    m[0][1] *= -1.0
    m[1][0] *= -1.0
    m[1][2] *= -1.0
    m[2][1] *= -1.0

def mat4_flip_horizontal_at_point( m, x ):
    s = sqrt(pow(m[0][0], 2) + pow(m[0][1], 2) + pow(m[0][2], 2))
    mat4_remove_scale( m, s )
    mat4_rotation_invert( m )
    m[0][0] *= -1.0
    m[0][1] *= -1.0
    mat4_scale( m, s )

    m[3][0] += (x - m[3][0]) * 2.0
