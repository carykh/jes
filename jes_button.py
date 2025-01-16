from typing import Callable

import pygame
from jes_shapes import center_text
import time

class Button:
    def __init__(self, pdim, pnames, callback_func: Callable) -> None:
        self.dim = pdim  # Dim is a list of 4 parameters: x, y, width, height
        self.names = pnames
        self.setting = 0
        self.time_of_last_click = 0
        self._func = callback_func

    def draw_button(self, screen, font) -> None:
        x, y, w, h = self.dim
        name = self.names[self.setting]
        
        slider_surface = pygame.Surface((w,h), pygame.SRCALPHA, 32)
        slider_surface.fill((30,150,230))
        if name == "Turn off ALAP" or name[:4] == "Stop" or name[:4] == "Hide":
            slider_surface.fill((128,255,255))
        center_text(slider_surface, name, w / 2, h / 2, (0, 0, 0), font)
            
        screen.blit(slider_surface,(x,y))
        
    def click(self) -> None:
        self.setting = (self.setting + 1)%len(self.names)
        self.time_of_last_click = time.time()
        self._func(self)