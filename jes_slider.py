from typing import Callable

import pygame

class Slider:
    def __init__(self, pdim, callback_func: Callable, pval: int = 0, pval_min: int = 0, pval_max: int = 0, psnap_to_int: bool = True, pupdate_live: bool = True ) -> None:
        self.dim = pdim  # Dim is a list of 5 parameters: x, y, width, height, draggable_width
        self.val = pval
        self.val_min = pval_min
        self.val_max = pval_max
        self.tval = self.val
        self.snap_to_int = psnap_to_int
        self.update_live = pupdate_live
        self._func = callback_func

    def draw_slider(self, screen):
        x, y, w, h, dw = self.dim
        ratio = (self.tval-self.val_min)/self.get_length()
        slider_surface = pygame.Surface((w,h), pygame.SRCALPHA, 32)
        slider_surface.fill((80,80,80))
        pygame.draw.rect(slider_surface,(230,230,230),(ratio*(w-dw),0,dw,h))
        screen.blit(slider_surface,(x,y))
        
    def get_length(self):
        return max(self.val_max-self.val_min, 1)
        
    def update_val(self):
        if self.tval != self.val:
            self.val = self.tval
            self._func(self.val)
            
    def manual_update(self, val):
        self.tval = val
        self.update_val()
        self._func(self.val)