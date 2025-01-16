import numpy as np

from enums import Color
from utils import get_unit, dist_to_text, species_to_name, species_to_color
from jes_shapes import right_text, align_text, draw_species_circle
import math
import pygame
import bisect


# BLACK = (0,0,0)
# GRAY25 = (70,70,70)
# GRAY50 = (128,128,128)
# WHITE = (255,255,255)
# RED = (255,0,0)
# GREEN = (0,255,0)

def draw_all_graphs(sim, ui):
    draw_line_graph(sim.percentiles, ui.graph, [70, 0, 30, 30], sim.units_per_meter, ui.small_font)
    draw_sac(sim.species_pops, ui.sac, [70, 0], ui)
    draw_gene_graph(sim.species_info, sim.prominent_species, ui.gene_graph, sim, ui, ui.tiny_font)

def draw_line_graph(data, graph, margins, u, font) -> None:

    graph.fill(Color.BLACK)
    w = graph.get_width()-margins[0]-margins[1]
    h = graph.get_height()-margins[2]-margins[3]
    left = margins[0]
    right = graph.get_width()-margins[1]
    bottom = graph.get_height()-margins[3]
    
    min_val = np.amin(data)
    max_val = np.amax(data)
    unit = get_unit((max_val - min_val) / u) * u
    tick = math.floor(min_val/unit)*unit-unit
    while tick <= max_val+unit:
        ay = bottom-h*(tick-min_val)/(max_val-min_val)
        pygame.draw.line(graph, Color.GRAY25, (left, ay), (right, ay), width=1)
        right_text(graph, dist_to_text(tick, False, u), left - 7, ay, Color.GRAY50, font)
        tick += unit
        
    
    to_show = [0,1,2,3,4,5,6,7,8,9,10,20,30,40,50,60,70,80,90,91,92,93,94,95,96,97,98,99,100]
    data_len = len(data)
    for g in range(data_len):
        for p in to_show:
            prev_val = 0 if g == 0 else data[g-1][p]
            next_val = data[g][p]
            
            x1 = left+(g/data_len)*w
            x2 = left+((g+1)/data_len)*w
            y1 = bottom-h*(prev_val-min_val)/(max_val-min_val)
            y2 = bottom-h*(next_val-min_val)/(max_val-min_val)
            
            important: bool = (p%10 == 0)
            thickness = 2 if important else 1
            color = Color.WHITE if important else Color.GRAY50
            if p == 50:
                color = Color.RED
                thickness = 3

            pygame.draw.line(graph, color, (x1, y1), (x2, y2), width=thickness)
            
def draw_sac(data, sac, margins, ui) -> None:
    sac.fill((0,0,0))
    for g in range(len(data)):
        scan_down_trapezoids(data, g, sac, margins, ui)
        
def scan_down_trapezoids(data, g, sac, margins, ui) -> None:
    w = sac.get_width()-margins[0]-margins[1]
    h = sac.get_height()
    len_data = len(data)
    left = margins[0]

    x1 = left+(g/len_data)*w
    x2 = left+((g+1)/len_data)*w
    keys = sorted(list(data[g].keys()))
    c_count = data[g][keys[-1]][2] # ending index of the last entry
    fac = h/c_count

    if g == 0:
        for sp in data[g].keys():
            pop = data[g][sp]
            points = [[x1,h/2],[x1,h/2],[x2,h-pop[1]*fac],[x2,h-pop[2]*fac]]
            pygame.draw.polygon(sac, species_to_color(sp, ui), points)
    else:
        trapezoid_helper(sac, data, g, g - 1, 0, c_count, x1, x2, fac, 0, ui)
   
def get_range_even_if_none(dicty, key):
    keys = sorted(list(dicty.keys()))
    if key in keys:
        return dicty[key]
    else:
        n = bisect.bisect(keys, key + 0.5)
        if n >= len(keys):
            val = dicty[keys[n-1]][2]
        else:
            val = dicty[keys[n]][1]
        return [0, val, val]

def trapezoid_helper(sac, data, g1, g2, i_start, i_end, x1, x2, fac, level, ui) -> None:
    pop2 = [0, 0, 0]
    h = sac.get_height()
    for sp in data[g1].keys():
        pop1 = data[g1][sp]
        if level == 0 and pop1[1] != pop2[2]: #there was a gap
            trapezoid_helper(sac, data, g2, g1, pop2[2], pop1[1], x2, x1, fac, 1, ui)

        pop2 = get_range_even_if_none(data[g2], sp)
        points = [[x1, h - pop2[1] * fac], [x1, h - pop2[2] * fac], [x2, h - pop1[2] * fac], [x2, h - pop1[1] * fac]]
        pygame.draw.polygon(sac, species_to_color(sp, ui), points)
        
def draw_gene_graph(species_info, ps, gg, sim, ui, font) -> None:  # ps = prominent_species
    r = ui.genealogy_coor[4]
    h = gg.get_height()-r*2
    w = gg.get_width()-r*2
    gg.fill((0,0,0))
    if len(sim.creatures) == 0:
        return
        
    for level in range(len(ps)):
        for i in range(len(ps[level])):
            s = ps[level][i]
            x = (i+0.5)/(len(ps[level])) * w + r
            y = level / (len(ps)-0.8) * h + r
            species_info[s].coor = (x,y)
            
    for level in range(len(ps)):
        for i in range(len(ps[level])):
            s = ps[level][i]
            draw_species_circle(gg, s, species_info[s].coor, r, sim, species_info, font, True, ui)
        
def display_all_graphs(screen, sim, ui) -> None:
    blit_graphsand_marks(screen, sim, ui)
    blit_g_gand_marks(screen, sim, ui)
    
    if sim.last_gen_run_time >= 0:
        right_text(screen, f"Last gen runtime: {sim.last_gen_run_time:.3f}s", 1200, 28, Color.WHITE, ui.small_font)
        
def blit_graphsand_marks(screen, sim, ui):
    screen.blit(ui.graph, ui.graph_coor[0:2])
    screen.blit(ui.sac, ui.sac_coor[0:2])

    a = int(ui.gen_slider.val)
    b = int(ui.gen_slider.val_max)
    a2 = min(a,b-1)
    if b == 0:
        return
    
    if a < b:
        frac = (a+1)/b
        line_x = ui.sac_coor[0] + 70 + (ui.graph.get_width() - 70) * frac
        line_ys = [[50,550],[560,860]]
        for lineY in line_ys:
            pygame.draw.line(screen, Color.GREEN, (line_x, lineY[0]), (line_x, lineY[1]), width=2)
    
    frac = (a2+1)/b
    line_x = ui.sac_coor[0] + 70 + (ui.graph.get_width() - 70) * frac
    median = sim.percentiles[a2][50]
    right_text(screen, f"Median: {dist_to_text(median, True, sim.units_per_meter)}", 1800, 28, Color.WHITE, ui.small_font)
    
    top_species = get_top_species(sim, a2)
    for sp in sim.species_pops[a2].keys():
        pop = sim.species_pops[a2][sp]
        if pop[0] >= sim.creature_count*sim.S_VISIBLE:
            species_i = (pop[1]+pop[2])/2
            species_y = 560+300*(1 - species_i / sim.creature_count)
            name = species_to_name(sp, ui)
            color = species_to_color(sp, ui)
            outline = Color.WHITE if sp == top_species else None
            align_text(screen, f"{name}: {pop[0]}", line_x + 10, species_y, color, ui.small_font, 0.0, [Color.BLACK, outline])
        

def blit_g_gand_marks(screen, sim, ui):
    screen.blit(ui.gene_graph, ui.genealogy_coor[0:2])
    r = 42
    a = int(ui.gen_slider.val)
    b = int(ui.gen_slider.val_max)
    a2 = min(a,b-1)
    if b == 0:
        return
    top_species = get_top_species(sim, a2)
    
    
    for sp in sim.species_pops[a2].keys():
        info = sim.species_info[sp]
        if not info.prominent:
            continue
        # pop = sim.species_pops[a2][sp][0]
        circle_count = 2 if sp == top_species else 1
        cx = info.coor[0] + ui.genealogy_coor[0]
        cy = info.coor[1] + ui.genealogy_coor[1]
        for c in range(circle_count):
            pygame.draw.circle(screen, Color.WHITE, (cx,cy), r+3+6*c, 3)
    
    if ui.species_storage is not None:
        sp = ui.species_storage
        if sp in sim.species_pops[a2]:
            circle_count = 2 if sp == top_species else 1
            for c in range(circle_count):
                pygame.draw.circle(screen, Color.WHITE, ui.storage_coor, r+3+6*c, 3)
            

def get_top_species(sim, g):
    data = sim.species_pops[g] 
    return max(data, key=data.get)