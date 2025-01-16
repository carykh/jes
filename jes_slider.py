import pygame

class Slider:
    def __init__(self,ui,pdim,pval,pval_min,pval_max,psnap_to_int,pupdate_live,pupdate_function):
        self.dim = pdim  # Dim is a list of 5 parameters: x, y, width, height, draggable_width
        self.val = pval
        self.val_min = pval_min
        self.val_max = pval_max
        self.tval = self.val
        self.snap_to_int = psnap_to_int
        self.update_live = pupdate_live
        self.update_function = pupdate_function
        ui.slider_list.append(self)
        
    def drawSlider(self, screen):
        x, y, w, h, dw = self.dim
        ratio = (self.tval-self.val_min)/self.getLength()
        sliderSurface = pygame.Surface((w,h), pygame.SRCALPHA, 32)
        sliderSurface.fill((80,80,80)) 
        pygame.draw.rect(sliderSurface,(230,230,230),(ratio*(w-dw),0,dw,h))
        screen.blit(sliderSurface,(x,y))
        
    def getLength(self):
        return max(self.val_max-self.val_min, 1)
        
    def updateVal(self):
        if self.tval != self.val:
            self.val = self.tval
            self.update_function(self.val)
            
    def manualUpdate(self, val):
        self.tval = val
        self.updateVal()
        self.update_function(self.val)