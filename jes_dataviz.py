import bisect
import math

import numpy as np
import pygame

from jes_shapes import alignText, drawSpeciesCircle, rightText
from utils import dist_to_text, getUnit, species_to_name, speciesToColor


def drawAllGraphs(sim, ui):
    drawLineGraph(
        sim.percentiles, ui.graph, [70, 0, 30, 30], sim.UNITS_PER_METER, ui.smallFont
    )
    drawSAC(sim.species_pops, ui.sac, [70, 0], ui)
    drawGeneGraph(
        sim.species_info, sim.prominent_species, ui.gene_graph, sim, ui, ui.tinyFont
    )


def drawLineGraph(data, graph, margins, u, font):
    BLACK = (0, 0, 0)
    GRAY25 = (70, 70, 70)
    GRAY50 = (128, 128, 128)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)

    graph.fill(BLACK)
    W = graph.get_width() - margins[0] - margins[1]
    H = graph.get_height() - margins[2] - margins[3]
    LEFT = margins[0]
    RIGHT = graph.get_width() - margins[1]
    BOTTOM = graph.get_height() - margins[3]

    minVal = np.amin(data)
    maxVal = np.amax(data)
    unit = getUnit((maxVal - minVal) / u) * u
    tick = math.floor(minVal / unit) * unit - unit
    while tick <= maxVal + unit:
        ay = BOTTOM - H * (tick - minVal) / (maxVal - minVal)
        pygame.draw.line(graph, GRAY25, (LEFT, ay), (RIGHT, ay), width=1)
        rightText(graph, dist_to_text(tick, False, u), LEFT - 7, ay, GRAY50, font)
        tick += unit

    toShow = [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        20,
        30,
        40,
        50,
        60,
        70,
        80,
        90,
        91,
        92,
        93,
        94,
        95,
        96,
        97,
        98,
        99,
        100,
    ]
    LEN = len(data)
    for g in range(LEN):
        for p in toShow:
            prevVal = 0 if g == 0 else data[g - 1][p]
            nextVal = data[g][p]

            x1 = LEFT + (g / LEN) * W
            x2 = LEFT + ((g + 1) / LEN) * W
            y1 = BOTTOM - H * (prevVal - minVal) / (maxVal - minVal)
            y2 = BOTTOM - H * (nextVal - minVal) / (maxVal - minVal)

            IMPORTANT = p % 10 == 0
            thickness = 2 if IMPORTANT else 1
            color = WHITE if IMPORTANT else GRAY50
            if p == 50:
                color = RED
                thickness = 3
            pygame.draw.line(graph, color, (x1, y1), (x2, y2), width=thickness)


def drawSAC(data, sac, margins, ui):
    sac.fill((0, 0, 0))
    for g in range(len(data)):
        scanDownTrapezoids(data, g, sac, margins, ui)


def scanDownTrapezoids(data, g, sac, margins, ui):
    W = sac.get_width() - margins[0] - margins[1]
    H = sac.get_height()
    LEN = len(data)
    LEFT = margins[0]
    sac.get_width() - margins[1]
    x1 = LEFT + (g / LEN) * W
    x2 = LEFT + ((g + 1) / LEN) * W
    keys = sorted(list(data[g].keys()))
    c_count = data[g][keys[-1]][2]  # ending index of the last entry
    FAC = H / c_count

    if g == 0:
        for sp in data[g].keys():
            pop = data[g][sp]
            points = [
                [x1, H / 2],
                [x1, H / 2],
                [x2, H - pop[1] * FAC],
                [x2, H - pop[2] * FAC],
            ]
            pygame.draw.polygon(sac, speciesToColor(sp, ui), points)
    else:
        trapezoidHelper(sac, data, g, g - 1, 0, c_count, x1, x2, FAC, 0, ui)


def getRangeEvenIfNone(dicty, key):
    keys = sorted(list(dicty.keys()))
    if key in keys:
        return dicty[key]
    else:
        n = bisect.bisect(keys, key + 0.5)
        if n >= len(keys):
            val = dicty[keys[n - 1]][2]
        else:
            val = dicty[keys[n]][1]
        return [0, val, val]


def trapezoidHelper(sac, data, g1, g2, i_start, i_end, x1, x2, FAC, level, ui):
    pop2 = [0, 0, 0]
    H = sac.get_height()
    for sp in data[g1].keys():
        pop1 = data[g1][sp]
        if level == 0 and pop1[1] != pop2[2]:  # there was a gap
            trapezoidHelper(sac, data, g2, g1, pop2[2], pop1[1], x2, x1, FAC, 1, ui)
        pop2 = getRangeEvenIfNone(data[g2], sp)
        points = [
            [x1, H - pop2[1] * FAC],
            [x1, H - pop2[2] * FAC],
            [x2, H - pop1[2] * FAC],
            [x2, H - pop1[1] * FAC],
        ]
        pygame.draw.polygon(sac, speciesToColor(sp, ui), points)


def drawGeneGraph(species_info, ps, gg, sim, ui, font):  # ps = prominent_species
    R = ui.GENEALOGY_COOR[4]
    H = gg.get_height() - R * 2
    W = gg.get_width() - R * 2
    gg.fill((0, 0, 0))
    if len(sim.creatures) == 0:
        return

    for level in range(len(ps)):
        for i in range(len(ps[level])):
            s = ps[level][i]
            x = (i + 0.5) / (len(ps[level])) * W + R
            y = (level) / (len(ps) - 0.8) * H + R
            species_info[s].coor = (x, y)

    for level in range(len(ps)):
        for i in range(len(ps[level])):
            s = ps[level][i]
            drawSpeciesCircle(
                gg, s, species_info[s].coor, R, sim, species_info, font, True, ui
            )


def displayAllGraphs(screen, sim, ui):
    WHITE = (255, 255, 255)
    blitGraphsandMarks(screen, sim, ui)
    blitGGandMarks(screen, sim, ui)

    if sim.last_gen_run_time >= 0:
        rightText(
            screen,
            f"Last gen runtime: {sim.last_gen_run_time:.3f}s",
            1200,
            28,
            WHITE,
            ui.smallFont,
        )


def blitGraphsandMarks(screen, sim, ui):
    screen.blit(ui.graph, ui.GRAPH_COOR[0:2])
    screen.blit(ui.sac, ui.SAC_COOR[0:2])
    GREEN = (0, 255, 0)
    WHITE = (255, 255, 255)
    a = int(ui.genSlider.val)
    b = int(ui.genSlider.val_max)
    a2 = min(a, b - 1)
    if b == 0:
        return

    if a < b:
        frac = (a + 1) / b
        lineX = ui.SAC_COOR[0] + 70 + (ui.graph.get_width() - 70) * frac
        lineYs = [[50, 550], [560, 860]]
        for lineY in lineYs:
            pygame.draw.line(
                screen, GREEN, (lineX, lineY[0]), (lineX, lineY[1]), width=2
            )

    frac = (a2 + 1) / b
    lineX = ui.SAC_COOR[0] + 70 + (ui.graph.get_width() - 70) * frac
    median = sim.percentiles[a2][50]
    rightText(
        screen,
        f"Median: {dist_to_text(median, True, sim.UNITS_PER_METER)}",
        1800,
        28,
        WHITE,
        ui.smallFont,
    )

    top_species = getTopSpecies(sim, a2)
    for sp in sim.species_pops[a2].keys():
        pop = sim.species_pops[a2][sp]
        if pop[0] >= sim.c_count * sim.S_VISIBLE:
            speciesI = (pop[1] + pop[2]) / 2
            speciesY = 560 + 300 * (1 - speciesI / sim.c_count)
            name = species_to_name(sp, ui)
            color = speciesToColor(sp, ui)
            OUTLINE = ui.WHITE if sp == top_species else None
            alignText(
                screen,
                f"{name}: {pop[0]}",
                lineX + 10,
                speciesY,
                color,
                ui.smallFont,
                0.0,
                [ui.BLACK, OUTLINE],
            )


def blitGGandMarks(screen, sim, ui):
    screen.blit(ui.gene_graph, ui.GENEALOGY_COOR[0:2])
    R = 42
    a = int(ui.genSlider.val)
    b = int(ui.genSlider.val_max)
    a2 = min(a, b - 1)
    if b == 0:
        return
    top_species = getTopSpecies(sim, a2)

    for sp in sim.species_pops[a2].keys():
        info = sim.species_info[sp]
        if not info.prominent:
            continue
        sim.species_pops[a2][sp][0]
        circle_count = 2 if sp == top_species else 1
        cx = info.coor[0] + ui.GENEALOGY_COOR[0]
        cy = info.coor[1] + ui.GENEALOGY_COOR[1]
        for c in range(circle_count):
            pygame.draw.circle(screen, ui.WHITE, (cx, cy), R + 3 + 6 * c, 3)

    if ui.species_storage is not None:
        sp = ui.species_storage
        if sp in sim.species_pops[a2]:
            circle_count = 2 if sp == top_species else 1
            for c in range(circle_count):
                pygame.draw.circle(screen, ui.WHITE, ui.storage_coor, R + 3 + 6 * c, 3)


def getTopSpecies(sim, g):
    data = sim.species_pops[g]
    return max(data, key=data.get)
