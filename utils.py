import json
from hashlib import sha256
import numpy as np
import math

def array_lerp(arr_a, arr_b, x):
    return arr_a+(arr_b - arr_a)*x
    
def list_lerp(list_a, list_b, x):
    list_result = [None]*len(list_a)
    for i in range(len(list_a)):
        list_result[i] = list_a[i] + (list_b[i] - list_a[i]) * x
    return list_result
    
def get_unit(r):
    _list = [0.000001,0.000002,0.000005,0.00001,0.00002,0.00005,0.0001,0.0002,0.0005,0.001,0.002,0.005,0.01,0.02,0.05,0.1,0.2,0.5,1,2,5,10,20,50,100,200,500,1000,2000,5000,10000,20000,50000,100000,200000,500000,1000000]
    choice = 0
    while _list[choice] < r * 0.2:
        choice += 1
    return _list[choice]
    
def hue_to_rgb(hue):
    h = (hue*6)%1.0
    r = (0,0,0)
    if hue < 1/6:
        r = (1,h,0)
    elif hue < 2/6:
        r = (1-h,1,0)
    elif hue < 3/6:
        r = (0,1,h)
    elif hue < 4/6:
        r = (h*0.4,1-h*0.6,1)
    elif hue < 5/6:
        r = (0.4+0.6*h,0.4,1)
    else:
        r = (1,0.4-0.4*h,1-h)
    return 255*r[0], 200*r[1], 255*r[2]
    
def species_to_name(s, ui):
    salted = str(s)+ui.salt
    _hex = sha256(salted.encode('utf-8')).hexdigest()
    result = int(_hex, 16)
    length_choices = [5,6,6,7,7]
    length_choice = result%5
    result = result//5
    
    letters = ["bcdfghjklmnprstvwxz","aeiouy"]
    name_len = length_choices[length_choice]
    name = ""
    for n in range(name_len):
        letter_type = n%len(letters)
        option_count = len(letters[letter_type])
        choice = result%option_count
        letter = letters[letter_type][choice]
        if n >= 2 and letter == "g" and name[n-2].lower() == "n":
            letter = "m"
        if n == 0:
            letter = letter.upper()
        name += letter
        result = result//option_count

    return name
    
def brighten(color, b):
    if b >= 1:
        fac = b-1
        return lerp(color[0],255,fac),lerp(color[1],255,fac),lerp(color[2],255,fac)
    else:
        return color[0]*b, color[1]*b, color[2]*b
    
def species_to_color(s, ui):
    salted = str(s)+ui.salt
    if s in ui.sc_colors:
        salted = ui.sc_colors[s]+ui.salt
    _hex = sha256(salted.encode('utf-8')).hexdigest()
    hue = (int(_hex, 16)%10000)/10000
    brightness = (math.floor(int(_hex, 16)//10000)%100)/100
    color = hue_to_rgb(hue)
    new_color = brighten(color, 0.85+0.6*brightness)

    return new_color
    
def bound(x):
    return min(max(x,0),1)
    
def lerp(a,b,x):
    return a+(b-a)*x
    
def dist_to_text(dist, sigfigs, u):
    if sigfigs:
        return f"{dist/u:.2f}cm"
    else:
        return str(int(dist/u))+"cm"
        
def get_distance_array(a, b):
    x_dist = a[:,:,:,0]-b[:,:,:,0]
    y_dist = a[:,:,:,1]-b[:,:,:,1]
    return np.sqrt(np.square(x_dist)+np.square(y_dist))
    
def apply_muscles(n, m, muscle_coef) -> None :
    x_neighbor_dists = get_distance_array(n[:, :-1, :], n[:, 1:, :])
    y_neighbor_dists = get_distance_array(n[:, :, :-1], n[:, :, 1:])
    pos_diag_neighbor_dists = get_distance_array(n[:, :-1, :-1], n[:, 1:, 1:])
    neg_diag_neighbor_dists = get_distance_array(n[:, :-1, 1:], n[:, 1:, :-1])
    
    m_as = [None] * 6
    segments = [[0,0,1,0],[0,1,1,1],[0,0,0,1],[1,0,1,1],[0,0,1,1],[0,1,1,0]]

    
    m_as[0] = get_muscle_attraction(x_neighbor_dists[:, :, :-1], m[:, :, :, 0], muscle_coef)
    m_as[1] = get_muscle_attraction(x_neighbor_dists[:, :, 1:], m[:, :, :, 0], muscle_coef)
    m_as[2] = get_muscle_attraction(y_neighbor_dists[:, :-1, :], m[:, :, :, 1], muscle_coef)
    m_as[3] = get_muscle_attraction(y_neighbor_dists[:, 1:, :], m[:, :, :, 1], muscle_coef)
    m_as[4] = get_muscle_attraction(pos_diag_neighbor_dists, m[:, :, :, 3], muscle_coef)
    m_as[5] = get_muscle_attraction(neg_diag_neighbor_dists, m[:, :, :, 3], muscle_coef)
    
    # The array n is a 100 x 5 x 5 x 4 dimensional array,
    # and it encodes the position and velocity data for all 100 creatures on a frame.
    
    # Dimension 1: 100 creatures (creature ID)
    # Dimension 2: 5 nodes across the x-dimensional
    # Dimension 3: 5 nodes across the y-dimensional
    # Dimension 4: Which coordinate to do you want (x, y, vx, vy)
    _, cw, ch, __ = n.shape
    cw -= 1
    ch -= 1
    
    for dire in range(6):
        s = segments[dire]
        sli1 = n[:,s[0]:s[0]+cw,s[1]:s[1]+cw]
        sli2 = n[:,s[2]:s[2]+ch,s[3]:s[3]+ch]
        
        delta_x = sli1[:,:,:,0]-sli2[:,:,:,0]
        delta_y = sli1[:,:,:,1]-sli2[:,:,:,1]
        
        delta_magnitude = np.sqrt(np.square(delta_x)+np.square(delta_y))
        delta_nx = delta_x/delta_magnitude
        delta_ny = delta_y/delta_magnitude
        
        n[:,s[0]:s[0]+cw,s[1]:s[1]+cw,2] += delta_nx*m_as[dire]
        n[:,s[0]:s[0]+cw,s[1]:s[1]+cw,3] += delta_ny*m_as[dire]
        n[:,s[2]:s[2]+ch,s[3]:s[3]+ch,2] -= delta_nx*m_as[dire]
        n[:,s[2]:s[2]+ch,s[3]:s[3]+ch,3] -= delta_ny*m_as[dire]
        
def get_muscle_attraction(dists, m, muscle_coef):
    return (m-dists) * muscle_coef
    
def get_dist(x1, y1, x2, y2):
    return np.linalg.norm(np.array([x2-x1,y2-y1]))
    
def array_int_multiply(arr, factor):

    result = [None] * len(arr)

    for i in range(len(arr)):
        result[i] = int(arr[i] * factor)

    return result

def read_config(filename: str) -> dict:
    with open(filename, 'r') as f:
        result: dict = json.load(f)

        return result