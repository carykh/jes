import pygame
from utils import arrayLerp, dist_to_text, speciesToColor, listLerp, lerp
from jes_shapes import drawRect, drawTextRect, centerText, drawClock
import numpy as np
import math
from jes_species_info import SpeciesInfo
# from jes_sim import Sim
import random
import logging

class Creature:
    def __init__(self,d,pIDNumber,parent_species,_sim,_ui, max_offspring=4, logger=None, mutate_rate=0.05):
        self.logger = logger or logging.getLogger(__name__)
        self.dna = d
        self.calmState = None
        self.icons = [None]*2
        self.iconCoor = None
        self.IDNumber = pIDNumber
        self.fitness = None
        self.rank = None
        self.living = True
        self.species = self.getSpecies(parent_species)
        self.sim = _sim
        self.ui = _ui
        self.codonWithChange = None
        self.max_offspring = max_offspring
        self.generation_offspring = 0

    def __str__(self):
        return f"ID: {self.IDNumber:<5} S: {str(self.sim.species_info[self.species]):<10}  OG: {self.generation_offspring:<4}"
    
    def getSpecies(self, parent_species):
        if parent_species == -1:
            return self.IDNumber
        else:
            return parent_species
    
    def drawCell(self,surface,nodeState,frame,transform,x,y):
        tx,ty,s = transform
        color = self.traitsToColor(self.dna,x,y,frame)
        points = [None]*4
        for p in range(4):
            px = x
            if p == 1 or p == 2:
                px += 1
            py = y+p//2
            points[p] = [tx+nodeState[px,py,0]*s,ty+nodeState[px,py,1]*s]
        pygame.draw.polygon(surface,color,points)
        
    def drawEnvironment(self,surface,nodeState,frame,transform):
        BLACK = (0,0,0)
        WHITE = (255,255,255)
        SIGN_COLOR = (150,100,50)
        #sky
        drawRect(surface,transform,None,BLACK)
        
        #signs
        font = self.ui.bigFont if transform[2] >= 50 else self.ui.smallFont
        for meters in range(0,3000,100):
            u = meters*self.sim.UNITS_PER_METER
            drawRect(surface,transform,[u-0.2,-6,u+0.2,0],SIGN_COLOR)
            drawTextRect(surface,transform,[u-1.5,-6.8,u+1.5,-5.4],SIGN_COLOR,WHITE,f"{meters}cm",font)
        
        #ground
        drawRect(surface,transform,[None,0,None,None],WHITE)

    def drawCreature(self, surface, nodeState, frame, transform, drawLabels, shouldDrawClock):
        if drawLabels:
            self.drawEnvironment(surface,nodeState,frame,transform)
            
        cellSurface = pygame.Surface(surface.get_size(), pygame.SRCALPHA, 32)
        for x in range(self.sim.CW):
            for y in range(self.sim.CH):
                self.drawCell(cellSurface,nodeState,frame,transform,x,y)
        surface.blit(cellSurface,(0,0))
   
        if drawLabels:
            tx,ty,s = transform
            avg_x = np.mean(nodeState[:,:,0],axis=(0,1))
            lx = tx+avg_x*s
            ly = 20
            lw = 100
            lh = 36
            ar = 15
            pygame.draw.rect(surface, (255,0,0),(lx-lw/2,ly,lw,lh))
            pygame.draw.polygon(surface,(255,0,0),((lx,ly+lh+ar),(lx-ar,ly+lh),(lx+ar,ly+lh)))
            centerText(surface, f"{dist_to_text(avg_x,True,self.sim.UNITS_PER_METER)}", lx, ly+18, self.ui.WHITE, self.ui.smallFont)
            
            ratio = 1-frame/self.sim.trial_time
        if shouldDrawClock:
            drawClock(surface,[40,40,32],ratio,str(math.ceil(ratio*self.sim.trial_time/self.ui.FPS)),self.ui.smallFont)

        
    def drawIcon(self, ICON_DIM, BG_COLOR, BEAT_FADE_TIME):
        icon = pygame.Surface(ICON_DIM, pygame.SRCALPHA, 32)
        icon.fill(BG_COLOR)
        transform = [ICON_DIM[0]/2,ICON_DIM[0]/(self.sim.CW+2),ICON_DIM[0]/(self.sim.CH+2.85)]
        self.drawCreature(icon,self.calmState,BEAT_FADE_TIME,transform,False,False)
        R = ICON_DIM[0]*0.09
        R2 = ICON_DIM[0]*0.12
        pygame.draw.circle(icon,speciesToColor(self.species, self.ui),(ICON_DIM[0]-R2,R2),R)
        return icon
        
    def saveCalmState(self, arr):
        self.calmState = arr

    def check_if_new_species(self, other_dna):
        sp_info = self.sim.species_info[self.species]
        species_rep_dna = self.sim.getCreatureWithID(sp_info.reps[1]).dna

        new_creature_similarity = self.calculate_raw_dna_similarity(species_rep_dna, other_dna)
        if new_creature_similarity < self.sim.species_threshold:
            self.logger.info(f"Creating new species, as offspring similarity is below threshold: {new_creature_similarity}")
            return True
        return False

        
    def getMutatedDNA(self, sim):
        mutation = np.clip(np.random.normal(-1.0, 1.0, self.dna.shape[0]),-99,99)
        mutation_mask = np.random.random(self.dna.shape) < sim.mutation_rate
        result = self.dna + sim.mutation_size * mutation * mutation_mask
        newSpecies = self.species
        
        big_mut_loc = 0

        if self.check_if_new_species(result):
            newSpecies = sim.species_count
            sim.species_count += 1
            # biggest_dna_change = mutation.argmax()
            return result, newSpecies, big_mut_loc

        if random.uniform(0,1) < self.sim.big_mutation_rate: # do a big mutation

            cell_x = random.randint(0,self.sim.CW-1)
            cell_y = random.randint(0,self.sim.CH-1)
            cell_beat = random.randint(0,self.sim.beats_per_cycle-1)
            
            big_mut_loc = (cell_x*self.sim.CH*self.sim.beats_per_cycle+cell_y*self.sim.beats_per_cycle+cell_beat)*self.sim.traits_per_box
            for i in range(self.sim.traits_per_box):
                delta = 0
                while abs(delta) < 0.5:
                    delta = np.random.normal(-1.0, 1.0, 1)
                result[big_mut_loc+i] += delta
                
                #Cells that endure a big mutation are also required to be at least somewhat rigid, because if a cell goes from super-short to super-tall but has low rigidity the whole time, then it doesn't really matter.
                if i == 2 and result[big_mut_loc+i] < 0.5:
                    result[big_mut_loc+i] = 0.5
            
        if self.check_if_new_species(result):
            newSpecies = sim.species_count
            sim.species_count += 1

        return result, newSpecies, big_mut_loc
    def calculate_dna_similarity(self, other_creature):
        """
        Calculate the genetic similarity between this creature and another creature.
        Returns a value between 0 and 1, where 1 means identical DNA.
        """
        # Calculate Euclidean distance between DNA arrays, normalized
        distance = np.sqrt(np.sum(np.square(self.dna - other_creature.dna)))
        # Convert to similarity (closer to 1 means more similar)
        max_possible_distance = np.sqrt(len(self.dna) * 36)  # Maximum possible distance assuming all values differ by 6 (-3 to 3)
        similarity = 1 - (distance / max_possible_distance)
        return similarity
    
    def calculate_raw_dna_similarity(self, dna_a, dna_b):
        distance = np.sqrt(np.sum(np.square(dna_a - dna_b)))
        # Convert to similarity (closer to 1 means more similar)
        max_possible_distance = np.sqrt(len(dna_a) * 36)  # Maximum possible distance assuming all values differ by 6 (-3 to 3)
        similarity = 1 - (distance / max_possible_distance)
        return similarity

        
    def traitsToColor(self, dna, x, y, frame):
        beat = self.sim.frameToBeat(frame)
        beat_prev = (beat+self.sim.beats_per_cycle-1)%self.sim.beats_per_cycle
        prog = self.sim.frameToBeatFade(frame)
        
        locationIndex = x*self.sim.CH+y
        DNAIndex = (locationIndex*self.sim.beats_per_cycle+beat)*self.sim.traits_per_box
        DNAIndex_prev = (locationIndex*self.sim.beats_per_cycle+beat_prev)*self.sim.traits_per_box
        traits = dna[DNAIndex:DNAIndex+self.sim.traits_per_box]
        traits_prev = dna[DNAIndex_prev:DNAIndex_prev+self.sim.traits_per_box]
        traits = arrayLerp(traits_prev,traits,prog)

        red = min(max(int(128+traits[0]*128),0),255)
        green = min(max(int(128+traits[1]*128),0),255)
        alpha = min(max(int(155+traits[2]*100),64),255) #alpha can't go below 25%
        color_result = (red,green,255,alpha)
        
        if self.codonWithChange is not None:
            nextGreen = 0
            if self.codonWithChange >= DNAIndex and self.codonWithChange < DNAIndex+self.sim.traits_per_box:
                nextGreen = 1
            prevGreen = 0
            if self.codonWithChange >= DNAIndex_prev and self.codonWithChange < DNAIndex_prev+self.sim.traits_per_box:
                prevGreen = 1
            green_ness = lerp(prevGreen,nextGreen,prog)
            color_result = listLerp(color_result,(0,255,0,255),green_ness)
        
        return color_result