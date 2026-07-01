import time

import pygame

from jes_shapes import centerText


class Button:
    def __init__(self, ui, pdim, pnames, pfunc):
        self.dim = pdim  # Dim is a list of 4 parameters: x, y, width, height
        self.names = pnames
        self.setting = 0
        self.timeOfLastClick = 0
        self.func = pfunc
        ui.buttonList.append(self)

    def drawButton(self, screen, font):
        x, y, w, h = self.dim
        name = self.names[self.setting]

        sliderSurface = pygame.Surface((w, h), pygame.SRCALPHA, 32)
        sliderSurface.fill((30, 150, 230))
        if name == "Turn off ALAP" or name[:4] == "Stop" or name[:4] == "Hide":
            sliderSurface.fill((128, 255, 255))
        centerText(sliderSurface, name, w / 2, h / 2, (0, 0, 0), font)

        screen.blit(sliderSurface, (x, y))

    def click(self):
        self.setting = (self.setting + 1) % len(self.names)
        self.timeOfLastClick = time.time()
        self.func(self)
