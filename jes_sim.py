import numpy as np
from utils import getDistanceArray, applyMuscles
from jes_creature import Creature
from jes_species_info import SpeciesInfo
from jes_dataviz import drawAllGraphs
import time
import random
import logging

class Sim:
    def __init__(self, _c_count, _stabilization_time, _trial_time, _beat_time,
    _beat_fade_time, _c_dim, _beats_per_cycle, _node_coor_count,
    _y_clips, _ground_friction_coef, _gravity_acceleration_coef,
    _calming_friction_coef, _typical_friction_coef, _muscle_coef,
    _traits_per_box, _traits_extra, mutation_size, big_mutation_size, _UNITS_PER_METER, logger=None, mutation_rate=0.05, big_mutation_rate=0.1, species_threshold=0.95, sexual_reproduction_chance=0.75):
        self.logger = logger or logging.getLogger(__name__)

        self.c_count = _c_count #creature count
        self.species_count = _c_count #species count
        self.stabilization_time = _stabilization_time
        self.trial_time = _trial_time
        self.beat_time = _beat_time
        self.beat_fade_time = _beat_fade_time
        self.c_dim = _c_dim
        self.CW, self.CH = self.c_dim
        self.beats_per_cycle = _beats_per_cycle
        self.node_coor_count = _node_coor_count 
        self.y_clips = _y_clips
        self.ground_friction_coef = _ground_friction_coef
        self.gravity_acceleration_coef = _gravity_acceleration_coef
        self.calming_friction_coef = _calming_friction_coef
        self.typical_friction_coef = _typical_friction_coef
        self.muscle_coef = _muscle_coef
        
        self.traits_per_box = _traits_per_box
        self.traits_extra = _traits_extra
        self.trait_count = self.CW*self.CH*self.beats_per_cycle*self.traits_per_box+self.traits_extra
        
        self.mutation_size = mutation_size
        self.big_mutation_size = big_mutation_size

        self.mutation_rate = mutation_rate
        self.big_mutation_rate = big_mutation_rate

        self.species_threshold = species_threshold

        self.sexual_reproduction_chance = sexual_reproduction_chance
        self.average_reproductions_per_creature = 1.1
        
        self.S_VISIBLE = 0.05 #what proportion of the population does a species need to appear on the SAC graph?
        self.S_NOTABLE = 0.10 #what proportion of the population does a species need to appear in the genealogy?
        self.HUNDRED = 100 # change this if you want to change the resolution of the percentile-tracking
        self.UNITS_PER_METER = _UNITS_PER_METER
        self.creatures = None
        self.rankings = np.zeros((0,self.c_count), dtype=int)
        self.percentiles = np.zeros((0,self.HUNDRED+1))
        self.species_pops = []
        self.species_info = []
        self.prominent_species = []
        self.ui = None
        self.last_gen_run_time = -1
        self.creature_generations = {}
        
    def initializeUniverse(self):
        self.creatures = [[None]*self.c_count]
        for c in range(self.c_count):
            self.creatures[0][c] = self.createNewCreature(c)
            self.species_info.append(SpeciesInfo(self,self.creatures[0][c], None, generation=0))
            
        # We want to make sure that all creatures, even in their
        # initial state, are in calm equilibrium. They shouldn't
        # be holding onto potential energy (e.g. compressed springs)
        self.getCalmStates(0,0,self.c_count,self.stabilization_time,True) #Calm the creatures down so no potential energy is stored
        
        for c in range(self.c_count):
            for i in range(2):
                self.creatures[0][c].icons[i] = self.creatures[0][c].drawIcon(self.ui.ICON_DIM[i], self.ui.MOSAIC_COLOR, self.beat_fade_time)
            
        self.ui.drawCreatureMosaic(0)

        
    def createNewCreature(self, idNumber):
        dna = np.clip(np.random.normal(0.0, 1.0, self.trait_count),-3,3)
        self.creature_generations[idNumber] = 0
        return Creature(dna, idNumber, -1, self, self.ui)
        
    def getCalmStates(self, gen, startIndex, endIndex, frameCount, calmingRun):
        param = self.simulateImport(gen, startIndex, endIndex, False)
        nodeCoor, muscles, _ = self.simulateRun(param, frameCount, True)
        for c in range(self.c_count):
            self.creatures[gen][c].saveCalmState(nodeCoor[c])
            
    def getStartingNodeCoor(self, gen, startIndex, endIndex, fromCalmState):
        COUNT = endIndex-startIndex
        n = np.zeros((COUNT,self.CH+1,self.CW+1,self.node_coor_count))
        if not fromCalmState or self.creatures[gen][0].calmState is None:
            # create grid of nodes along perfect gridlines
            coorGrid = np.mgrid[0:self.CW+1,0:self.CH+1]
            coorGrid = np.swapaxes(np.swapaxes(coorGrid,0,1),1,2)
            n[:,:,:,0:2] = coorGrid
        else:
            # load calm state into nodeCoor
            for c in range(startIndex,endIndex):
                n[c-startIndex,:,:,:] = self.creatures[gen][c].calmState
                n[c-startIndex,:,:,1] -= self.CH  # lift the creature above ground level
        return n

    def getMuscleArray(self, gen, startIndex, endIndex):
        COUNT = endIndex-startIndex
        m = np.zeros((COUNT,self.CH,self.CW,self.beats_per_cycle,self.traits_per_box+1)) # add one trait for diagonal length.
        DNA_LEN = self.CH*self.CW*self.beats_per_cycle*self.traits_per_box
        for c in range(startIndex,endIndex):
            dna = self.creatures[gen][c].dna[0:DNA_LEN].reshape(self.CH,self.CW,self.beats_per_cycle,self.traits_per_box)
            m[c-startIndex,:,:,:,:self.traits_per_box] = 1.0+(dna)/3.0
        m[:,:,:,:,3] = np.sqrt(np.square(m[:,:,:,:,0])+np.square(m[:,:,:,:,1])) # Set diagonal tendons
        return m

    def simulateImport(self, gen, startIndex, endIndex, fromCalmState):
        nodeCoor = self.getStartingNodeCoor(gen,startIndex,endIndex,fromCalmState)
        muscles = self.getMuscleArray(gen,startIndex,endIndex)
        currentFrame = 0
        return nodeCoor, muscles, currentFrame

    def frameToBeat(self, f):
        return (f//self.beat_time)%self.beats_per_cycle
        
    def frameToBeatFade(self, f):
        prog = f%self.beat_time
        return min(prog/self.beat_fade_time,1)

    def simulateRun(self, param, frameCount, calmingRun):
        nodeCoor, muscles, startCurrentFrame = param
        friction = self.calming_friction_coef if calmingRun else self.typical_friction_coef
        CEILING_Y = self.y_clips[0]
        FLOOR_Y = self.y_clips[1]
        
        for f in range(frameCount):
            currentFrame = startCurrentFrame+f
            beat = 0
            
            if not calmingRun:
                beat = self.frameToBeat(currentFrame)
                nodeCoor[:,:,:,3] += self.gravity_acceleration_coef
                # decrease y-velo (3rd node coor) by G
            applyMuscles(nodeCoor,muscles[:,:,:,beat,:],self.muscle_coef)
            nodeCoor[:,:,:,2:4] *= friction
            nodeCoor[:,:,:,0:2] += nodeCoor[:,:,:,2:4]    # all node's x and y coordinates are adjusted by velocity_x and velocity_y
            
            if not calmingRun:    # dealing with collision with the ground.
                nodesTouchingGround = np.ma.masked_where(nodeCoor[:,:,:,1] >= FLOOR_Y, nodeCoor[:,:,:,1])
                m = nodesTouchingGround.mask.astype(float) # mask that only countains 1's where nodes touch the floor
                pressure = nodeCoor[:,:,:,1]-FLOOR_Y
                groundFrictionMultiplier = 0.5**(m*pressure*self.ground_friction_coef)
                
                nodeCoor[:,:,:,1] = np.clip(nodeCoor[:,:,:,1], CEILING_Y, FLOOR_Y) # clip nodes below the ground back to ground level
                nodeCoor[:,:,:,2] *= groundFrictionMultiplier # any nodes touching the ground must be slowed down by ground friction.
        
        if calmingRun: # If it's a calming run, then take the average location of all nodes to center it at the origin.
            nodeCoor[:,:,:,0] -= np.mean(nodeCoor[:,:,:,0], axis=(1,2), keepdims=True)
        return nodeCoor, muscles, startCurrentFrame+frameCount  
    
    # Add this method to Sim class
    def sample_biased_id(max_id):
        """
        Sample an ID from 0 to max_id where 0 has the highest probability
        and max_id has the lowest.
        
        Args:
            max_id (int): The maximum ID value (inclusive)
        
        Returns:
            int: A sampled ID with bias toward lower values
        """
        # Generate random value with exponential distribution (more bias toward 0)
        x = np.random.exponential(scale=max_id/10)
        
        # Clip the value to our range and convert to integer
        selected_id = int(np.clip(x, 0, max_id))
    
        return selected_id
    
    def sample_weighted_creature_index(self, rankings, exclude_indices=None, weights = None):
        """
        Sample a creature index with probability weighted by its ranking.
        Higher ranked creatures (lower rank number) have higher probability of being selected.
        
        Parameters:
        - rankings: The array of creature indices sorted by fitness (highest first)
        - exclude_indices: Indices to exclude from selection (e.g., to avoid self-mating)
        
        Returns:
        - The selected creature index
        """
        if exclude_indices is None:
            exclude_indices = []
        
        # Create weights inversely proportional to rank
        if weights is None:
            weights = np.array([max(0.03, 1.0 - (r / len(rankings))) for r in range(len(rankings))])
        
        # Zero out excluded indices
        for idx in exclude_indices:
            if 0 <= idx < len(weights):
                weights[idx] = 0
        
        # Normalize weights
        if np.sum(weights) > 0:
            weights = weights / np.sum(weights)
        else:
            # If all weights are zero, use uniform distribution among non-excluded indices
            weights = np.ones(len(rankings))
            for idx in exclude_indices:
                if 0 <= idx < len(weights):
                    weights[idx] = 0
            weights = weights / np.sum(weights)
        
        # Sample from the distribution
        selected_rank = np.random.choice(len(rankings), p=weights)
        return rankings[selected_rank]
    
    def are_creatures_compatible(self, creature1: Creature, creature2: Creature):
        """
        Determine if two creatures are compatible for sexual reproduction.
        They should be genetically similar but not identical, and preferably of the same species.
        """
        if creature1.species != creature2.species:
            return False
        
        # if creature1.max_offspring <= creature1.generation_offspring or creature2.max_offspring <= creature2.generation_offspring:
        #     return False
        
        similarity = creature1.calculate_dna_similarity(creature2)
        
        # Creatures must be somewhat similar
        if similarity < 0.85:
            return False
        
        # Creatures of the same species are always compatible if they meet similarity criteria

            
        # Different species might still be compatible if they're genetically similar enough
        # This allows for occasional cross-species breeding
        # if similarity > 0.85:
        #     return True
            
        return True
    
    def sexual_reproduce(self, parent1: Creature, parent2: Creature, child_id):
        """
        Perform sexual reproduction between two creatures, creating a child with mixed DNA.
        """
        self.logger.info(f"Performing sexual reproduction. P1: {parent1} P2: {parent2}")
        # Get DNA from both parents
        dna1 = parent1.dna
        dna2 = parent2.dna
        
        # Create child DNA through recombination
        # We'll use a simple crossover method with some random variation
        child_dna = np.zeros_like(dna1)
        choice_array = np.random.random(dna1.shape)
        # Create masks for each inheritance type
        parent1_mask = (choice_array < 0.4)
        parent2_mask = (choice_array >= 0.4) & (choice_array < 0.8)
        blend_mask = (choice_array >= 0.8)
        
        child_dna[parent1_mask] = dna1[parent1_mask]
        child_dna[parent2_mask] = dna2[parent2_mask]
        child_dna[blend_mask] = (dna1[blend_mask] + dna2[blend_mask]) / 2.0

        mutate_mask = np.random.random(dna1.shape) < self.mutation_rate
            
        # Add small random mutations
        mutation = np.clip(np.random.normal(-1.0, 1.0, child_dna.shape[0]), -99, 99)
        child_dna += self.mutation_size * 0.5 * mutation * mutate_mask  # Half the normal mutation size
        
        # Determine child's species
        # Usually, child inherits species from the more fit parent
        # But occasionally, a new species emerges
        # if random.random() < 0.05: # DOES NOTHING
        #     # new_species = self.species_count
        #     # self.species_count += 1
        #     # # Create new creature with new species
        #     # self.logger.info(f"Creating new species. Reason: Why not. ID: {new_species}")
        #     # child = Creature(child_dna, child_id, new_species, self, self.ui)
        #     # # Create new species info record
        #     # more_fit_parent = parent1 if parent1.fitness > parent2.fitness else parent2
        #     # self.species_info.append(SpeciesInfo(self, child, more_fit_parent))
        #     parent_species = parent1.species if parent1.fitness > parent2.fitness else parent2.species
        #     child = Creature(child_dna, child_id, parent_species, self, self.ui)
        # else:
        #     # Inherit species from more fit parent
        species = parent1.species if parent1.fitness > parent2.fitness else parent2.species

        generation = len(self.creatures) - 1
        self.creature_generations[child_id] = generation
        parent1.generation_offspring += 1
        parent2.generation_offspring += 1
        if parent1.check_if_new_species(child_dna):
            species = self.species_count
            self.species_count += 1
            child = Creature(child_dna, child_id, species, self, self.ui)
            self.species_info.append(SpeciesInfo(self, child, parent1, generation=generation))
        else:
            child = Creature(child_dna, child_id, species, self, self.ui)

        return child
        
    def doSpeciesInfo(self,nsp,best_of_each_species):
        nsp = dict(sorted(nsp.items()))
        running = 0
        for sp in nsp.keys():
            pop = nsp[sp][0]
            nsp[sp][1] = running
            nsp[sp][2] = running+pop
            running += pop
            
            info = self.species_info[sp]
            info.reps[3] = best_of_each_species[sp] # most-recent representative
            if pop > info.apex_pop: # This species reached its highest population
                info.apex_pop = pop
                info.reps[2] = best_of_each_species[sp] # apex representative
            if pop >= self.c_count*self.S_NOTABLE and not info.prominent:  #prominent threshold
                info.becomeProminent()
                
    def checkALAP(self):
        if self.ui.ALAPButton.setting == 1: # We're already ALAP-ing!
            self.doGeneration(self.ui.doGenButton)


    def sample_weighted_by_species(self, creature_matrix, species_id, max_reproductions=2, excluded_indices=None, sample_size=10):
        """
        Sample indices weighted by fitness from creatures of a specific species.
        
        Args:
            creature_matrix: NumPy array with shape (n, 3) where:
                - column 0 is species ID
                - column 1 is fitness
                - column 2 is reproduction count
            species_id: The species ID to sample from
            max_reproductions: Maximum number of times a creature can reproduce
            excluded_indices: Optional list/array of indices to exclude from sampling
            
        Returns:
            Index of the sampled creature, or None if no valid creatures found
        """
        # Filter by species and reproduction count
        valid_mask = (creature_matrix[:, 0] == species_id) & (creature_matrix[:, 2] < max_reproductions)
        
        # Also filter out excluded indices if provided
        if excluded_indices is not None:
            # Create a mask of indices to exclude (True for positions to exclude)
            exclude_mask = np.zeros(len(creature_matrix), dtype=bool)
            exclude_mask[excluded_indices] = True
            # Update valid_mask to exclude these indices
            valid_mask = valid_mask & ~exclude_mask
        
        valid_indices = np.where(valid_mask)[0]
        
        # Return None if no valid creatures
        if len(valid_indices) == 0:
            return None
        
        # Determine actual sample size (can't sample more than available)
        actual_sample_size = min(sample_size, len(valid_indices))
        
        # Get fitness values for valid creatures
        fitness_values = creature_matrix[valid_indices, 1]
        
        # Apply softmax-like normalization to exaggerate differences
        temperature = 1.0
        weights = np.exp(fitness_values / temperature)
        
        # Normalize to get probabilities
        probabilities = weights / np.sum(weights)
        
        # Sample based on probabilities
        sampled_indices = np.random.choice(valid_indices, size=actual_sample_size, p=probabilities, replace=False)
        
        return sampled_indices

    def doGeneration(self, button):
        generation_start_time = time.time() #calculates how long each generation takes to run
        
        gen = len(self.creatures)-1
        creatureState = self.simulateImport(gen, 0, self.c_count, True)
        nodeCoor, muscles, _ = self.simulateRun(creatureState, self.trial_time, False)
        finalScores = nodeCoor[:,:,:,0].mean(axis=(1, 2)) # find each creature's average X-coordinate
        
        # Tallying up all the data
        currRankings = np.flip(np.argsort(finalScores), axis=0)
        newPercentiles = np.zeros((self.HUNDRED+1))
        newSpeciesPops = {}
        best_of_each_species = {}
        
        # Set fitness and rank for each creature
        for rank in range(self.c_count):
            c = currRankings[rank]
            self.creatures[gen][c].fitness = finalScores[c]
            self.creatures[gen][c].rank = rank
            
            species = self.creatures[gen][c].species
            if species in newSpeciesPops:
                newSpeciesPops[species][0] += 1
            else:
                newSpeciesPops[species] = [1, None, None]
            if species not in best_of_each_species:
                best_of_each_species[species] = self.creatures[gen][c].IDNumber
        
        self.doSpeciesInfo(newSpeciesPops, best_of_each_species)

        # Calculate percentiles
        for p in range(self.HUNDRED+1):
            rank = min(int(self.c_count*p/self.HUNDRED), self.c_count-1)
            c = currRankings[rank]
            newPercentiles[p] = self.creatures[gen][c].fitness
        
        # Prepare for reproduction
        currCreatures = self.creatures[-1]
        nextCreatures = [None] * self.c_count
        

        for c in range(self.c_count):
            self.creatures[gen][c].living = False
        
        weights = np.array([max(0.03, 1.0 - (r / len(currCreatures))) for r in range(len(currCreatures))])
        # Fill the new generation with offspring
        creature_species_matrix = np.zeros((self.c_count, 3), dtype=int)
        for c in range(self.c_count):
            creature = self.creatures[gen][c]
            creature_species_matrix[c, 0] = creature.species
            creature_species_matrix[c, 1] = creature.fitness
            creature_species_matrix[c, 2] = 0 # Times reproduced already

        for new_idx in range(self.c_count):
            # Choose a parent with weighted probability based on rank
            parent_creature_idx = self.sample_weighted_creature_index(currRankings, weights=weights)
            # make sure we don't reproduce too much
            while creature_species_matrix[parent_creature_idx, 2] + 1 >= self.average_reproductions_per_creature:
                if creature_species_matrix[parent_creature_idx, 2] - 1 < self.average_reproductions_per_creature:
                    if random.random() < 0.2:
                        break
                parent_creature_idx = self.sample_weighted_creature_index(currRankings, weights=weights)
                    
            parent_creature = self.creatures[gen][parent_creature_idx]
            reproduced = False
            # Choose reproduction method
            if random.random() < self.sexual_reproduction_chance:  # Try sexual reproduction
                # Find compatible mates
                # Sample potential mates with preference for higher fitness
                potential_mates_sample = self.sample_weighted_by_species(
                        creature_matrix=creature_species_matrix,
                        species_id=creature_species_matrix[parent_creature_idx][0],
                        max_reproductions=int(self.average_reproductions_per_creature*10),
                        excluded_indices=parent_creature_idx,
                        sample_size=1
                )
                # if potential_mates_sample is None:
                #     potential_mates_sample = []
                # No need to check compatibility, species must be compatible between itself
                # for mate_idx in potential_mates_sample:
                #     mate_creature = self.creatures[gen][mate_idx]
                #     self.logger.info(f"Checking creature compatibility: {parent_creature} | {mate_creature}")
                #     self.logger.info(f"Checking creature compatibility: {parent_creature.fitness} | {mate_creature.fitness}")

                #     if self.are_creatures_compatible(parent_creature, mate_creature):
                #         potential_mates.append(mate_idx)
                        # if len(potential_mates) >= 1:
                        #     break
                
                if potential_mates_sample is not None:
                    # Choose one of the compatible mates randomly
                    mate_idx = random.choice(potential_mates_sample)
                    mate_creature = self.creatures[gen][mate_idx]
                    
                    # Create offspring through sexual reproduction
                    nextCreatures[new_idx] = self.sexual_reproduce(
                        parent_creature, 
                        mate_creature,
                        (gen+1) * self.c_count + new_idx
                    )
                    
                    # Increment reproduction counters
                    creature_species_matrix[parent_creature_idx, 2] += 1
                    # We're the ones giving birth, mate just added genetic material
                    # creature_species_matrix[mate_idx, 2] += 1
                    reproduced = True
                    mate_creature.living = True
                    parent_creature.living = True
                    continue
            
            # If sexual reproduction wasn't chosen or failed, do asexual reproduction
            # 30% chance for cloning, 70% for mutation unless less than 4 individuals alive, then favor cloning
            if not reproduced:
                species_individuals_num = (creature_species_matrix[:, 0] == parent_creature.species).sum()
                if (random.random() * min(species_individuals_num, 4) / 4.0)  < 0.3:
                    nextCreatures[new_idx] = self.clone(
                        parent_creature, 
                        (gen+1) * self.c_count + new_idx
                    )
                    parent_creature
                else:
                    nextCreatures[new_idx] = self.mutate(
                        parent_creature, 
                        (gen+1) * self.c_count + new_idx
                )
            
                # Increment reproduction counter
                creature_species_matrix[parent_creature_idx, 2] += 1
                parent_creature.living = True
        
        # Add the new generation to the simulation
        self.creatures.append(nextCreatures)
        self.rankings = np.append(self.rankings, currRankings.reshape((1, self.c_count)), axis=0)
        self.percentiles = np.append(self.percentiles, newPercentiles.reshape((1, self.HUNDRED+1)), axis=0)
        self.species_pops.append(newSpeciesPops)
        graph_start = time.time()
        drawAllGraphs(self, self.ui)
        graph_end = time.time()
        
        # Calm the creatures down so no potential energy is stored
        self.getCalmStates(gen+1, 0, self.c_count, self.stabilization_time, True)
        for c in range(self.c_count):
            for i in range(2):
                self.creatures[gen+1][c].icons[i] = self.creatures[gen+1][c].drawIcon(
                    self.ui.ICON_DIM[i], 
                    self.ui.MOSAIC_COLOR, 
                    self.beat_fade_time
                )
        
        # Update UI
        self.ui.genSlider.val_max = gen+1
        self.ui.genSlider.manualUpdate(gen)
        self.last_gen_run_time = time.time() - generation_start_time
        
        self.ui.detectMouseMotion()
        self.checkALAP()
        self.logger.info(f"Graph draw time: {graph_end - graph_start}s")
 
    def getCreatureWithID(self, ID):
        return self.creatures[ID//self.c_count][ID%self.c_count]
        
    def clone(self, parent, newID):
        generation = len(self.creatures) - 1
        self.creature_generations[newID] = generation
        return Creature(parent.dna, newID, parent.species, self, self.ui)
        
    def mutate(self, parent, newID):
        newDNA, newSpecies, cwc = parent.getMutatedDNA(self)
        newCreature = Creature(newDNA, newID, newSpecies, self, self.ui)
        generation = len(self.creatures) - 1
        self.creature_generations[newID] = generation
        if newCreature.species != parent.species:
            self.species_info.append(SpeciesInfo(self, newCreature, parent, generation=generation))
            newCreature.codonWithChange = cwc
        return newCreature