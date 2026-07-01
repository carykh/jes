import copy
import math
import time

import numpy as np
import pygame

from utils import lerp, species_to_name, speciesToColor


def drawTextRect(surface, transform, coor, color1, color2, text, font):
    tx, ty, s = transform
    x1, y1, x2, y2 = coor
    drawRect(surface, transform, coor, color1)
    centerX = (x1 + x2) / 2
    centerY = (y1 + y2) / 2
    text_x = centerX * s + tx
    text_y = centerY * s + ty
    centerText(surface, text, text_x, text_y, color2, font)


def drawRect(surface, transform, coor, color):
    W = surface.get_width()
    H = surface.get_height()
    if coor is None:
        x1 = y1 = x2 = y2 = None
    else:
        x1, y1, x2, y2 = coor
    tx, ty, s = transform
    ax1 = 0 if x1 is None else tx + x1 * s
    ay1 = 0 if y1 is None else ty + y1 * s
    ax2 = W if x2 is None else tx + x2 * s
    ay2 = H if y2 is None else ty + y2 * s
    if ax1 < W and ax2 > 0 and ay1 < H and ay2 > 0:
        pygame.draw.rect(surface, color, (ax1, ay1, ax2 - ax1, ay2 - ay1))


def drawRingLight(w, h, thickness):
    s = math.sin(time.time() * (2 * math.pi) * 3) * 0.5 + 0.5
    BRIGHT = (255 * s, 255 * s, 0, 200)
    ringlight = pygame.Surface((w, h), pygame.SRCALPHA, 32)
    pygame.draw.rect(ringlight, BRIGHT, (0, 0, w, thickness))
    pygame.draw.rect(ringlight, BRIGHT, (0, h - thickness, w, thickness))
    pygame.draw.rect(ringlight, BRIGHT, (0, 0, thickness, h))
    pygame.draw.rect(ringlight, BRIGHT, (w - thickness, 0, thickness, h))
    return ringlight


def drawX(iconCoor, i, color, screen):
    for L in range(2):
        i1 = i * 0.02
        i2 = i * 0.06 + 3
        points = [[i1, i2], [i2, i1], [i - i1, i - i2], [i - i2, i - i1]]
        for P in points:
            if L == 1:
                P[0] = i - P[0]
            P[0] += iconCoor[0]
            P[1] += iconCoor[1]
        pygame.draw.polygon(screen, color, points)


def centerText(theScreen, stri, x, y, color, font):
    alignText(theScreen, stri, x, y, color, font, 0.5, None)


def rightText(theScreen, stri, x, y, color, font):
    alignText(theScreen, stri, x, y, color, font, 1.0, None)


def expand(coor, amount):
    return [
        coor[0] - amount,
        coor[1] - amount,
        coor[2] + amount * 2,
        coor[3] + amount * 2,
    ]


def alignText(theScreen, stri, x, y, color, font, align, bg_color):
    textSurface = font.render(stri, False, color)
    coor = (x - textSurface.get_width() * align, y - textSurface.get_height() / 2)
    if bg_color is not None:
        coor = (
            coor[0] - 4,
            coor[1],
            textSurface.get_width() + 8,
            textSurface.get_height(),
        )
        if bg_color[1] is not None:
            pygame.draw.rect(theScreen, bg_color[1], expand(coor, 2))
        pygame.draw.rect(theScreen, bg_color[0], coor)
    theScreen.blit(textSurface, coor)


def drawClock(surface, coor, the_ratio, text, font):
    WHITE = (255, 255, 255)
    GRAYISH = (115, 125, 160)
    BLACK = (0, 0, 0)
    x, y, r = coor
    P = 30
    for p in range(P):
        ratio1 = p / P
        ratio2 = (p + 1) / P
        ang1 = (ratio1 - 0.25) * 2 * math.pi
        ang2 = (ratio2 - 0.25) * 2 * math.pi
        points = [
            [x, y],
            [x + r * math.cos(ang1), y + r * math.sin(ang1)],
            [x + r * math.cos(ang2), y + r * math.sin(ang2)],
        ]
        pygame.draw.polygon(surface, GRAYISH, points)

        if the_ratio > ratio2:
            pygame.draw.polygon(surface, WHITE, points)
        elif the_ratio > ratio1:
            points2 = copy.deepcopy(points)
            prog = (the_ratio - ratio1) / (ratio2 - ratio1)
            points2[2][0] = lerp(points[1][0], points[2][0], prog)
            points2[2][1] = lerp(points[1][1], points[2][1], prog)
            pygame.draw.polygon(surface, WHITE, points2)

    centerText(surface, text, x, y, BLACK, font)


def drawArrow(screen, _start, _end, margin, head, color):
    start = np.array(_start)
    end = np.array(_end)
    total_dist = np.linalg.norm(start - end)
    prog = margin / total_dist

    near_start = start + (end - start) * prog
    near_end = start + (end - start) * (1 - prog)

    pygame.draw.line(screen, color, near_start, near_end, width=2)  # main line

    angle = np.arctan2(start[1] - end[1], start[0] - end[0])
    for p in range(2):
        new_angle = angle + (p - 0.5) * 2 * math.pi * 0.25
        flare = [
            near_end[0] + math.cos(new_angle) * head,
            near_end[1] + math.sin(new_angle) * head,
        ]
        pygame.draw.line(screen, color, near_end, flare, width=2)


def drawSpeciesCircle(screen, s, coor, R, sim, species_info, font, shouldDrawArrow, ui):
    color = speciesToColor(s, ui)
    name = species_to_name(s, ui)
    info = species_info[s]
    cx, cy = coor

    pygame.draw.circle(screen, color, coor, R)
    centerText(screen, name, cx, cy - 22, (0, 0, 0), font)

    creature = sim.getCreatureWithID(info.reps[2])
    tiny_icon = pygame.transform.scale(creature.icons[0], (50, 50))
    screen.blit(tiny_icon, (cx - 25, cy - 11))

    if shouldDrawArrow:
        ancestorID = species_info[s].ancestorID
        if ancestorID is None:
            drawArrow(screen, (cx, -R * 2), (cx, cy), R, R / 2, color)
        else:
            drawArrow(screen, species_info[ancestorID].coor, info.coor, R, R / 2, color)
