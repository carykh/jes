import pygame
from jes_shapes import center_text
import time

class Button:
    def __init__(self, ui, pdim, pnames, pfunc):
        self.dim = pdim  # Dim is a list of 4 parameters: x, y, width, height
        self.names = pnames
        self.setting = 0
        self.timeOfLastClick = 0
        self.func = pfunc
        ui.button_list.append(self)
        
    def draw_button(self, screen, font):
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
        self.timeOfLastClick = time.time()
        self.func(self)