import numpy as np
from hashlib import sha256
import math
from utils import species_to_name

class SpeciesInfo:
    def __init__(self, _sim, me, ancestor, generation):
        self.sim = _sim
        self.speciesID = me.species
        self.ancestorID = None
        self.generation = generation
        self.level = 0
        if ancestor is not None:
            self.ancestorID = ancestor.species
            self.level = self.sim.species_info[ancestor.species].level+1
            
        self.apex_pop = 0
        self.reps = np.zeros((4), dtype=int) # Representative ancestor, first, apex, and last creatures of this species.
        self.prominent = False
        
        if ancestor is not None:
            self.reps[0] = ancestor.IDNumber
        self.reps[1] = me.IDNumber
        self.coor = None

    def __str__(self):
        return f"{species_to_name(self.speciesID, self.sim.ui)}"
        
    def becomeProminent(self):  # if you are prominent, all your ancestors become prominent.
        self.prominent = True
        self.insertIntoProminentSpeciesList()
        if self.ancestorID is not None: # you have a parent
            ancestor = self.sim.species_info[self.ancestorID]
            if not ancestor.prominent:
                ancestor.becomeProminent()
                
    def insertIntoProminentSpeciesList(self):
        i = self.speciesID
        p = self.sim.prominent_species
        while len(p) <= self.level: # this level doesn't exist yet. Add new levels of the genealogy tree to acommodate you
            p.append([])
        pL = p[self.level]
        insert_index = 0
        for index in range(len(pL)):  # inefficient sorting thing, but there are <50 species so who cares
            other = pL[index]
            ancestorCompare = 0 if self.level == 0 else self.sim.species_info[other].ancestorID-self.ancestorID
            if ancestorCompare == 0: #siblings
                if other < i:
                    insert_index = index+1
            else: #not siblings trick to avoid family trees tangling (all siblings should be adjacent)
                if ancestorCompare < 0:
                    insert_index = index+1
        pL.insert(insert_index,i)

    def getWhen(self, index):
        return math.floor(self.reps[index]//self.sim.c_count)
        
    def getPerformance(self, sim, index):
        gen = math.floor(self.reps[index]//self.sim.c_count)
        c = self.reps[index]%self.sim.c_count
        creature = sim.creatures[gen][c]
        return creature.fitness
        
        