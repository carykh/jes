import numpy as np

from enums import Color
from utils import apply_muscles
from jes_creature import Creature
from jes_species_info import SpeciesInfo
from jes_dataviz import draw_all_graphs
import time
import random

class Sim:
    def __init__(self, creature_count: int, config: dict) -> None:
        self._creature_count: int = creature_count # creature count
        self.species_count: int = creature_count # species count
        self.stabilization_time: int = config.get('stabilization_time')
        self.trial_time: int = config.get('trial_time')
        self.beat_time: int = config.get('beat_time')
        self.beat_fade_time: int = config.get('beat_fade_time')
        self.c_dim: list[int] = config.get('c_dim')
        self.CW, self.CH =  self.c_dim
        self.beats_per_cycle: int = config.get('beats_per_cycle')
        self.node_coor_count: int = config.get('node_coor_count')
        self.y_clips: list[int] = config.get('y_clips')
        self.ground_friction_coef: int = config.get('ground_friction_coef')
        self.gravity_acceleration_coef: float = config.get('gravity_acceleration_coef')
        self.calming_friction_coef: float = config.get('calming_friction_coef')
        self.typical_friction_coef: float = config.get('typical_friction_coef')
        self.muscle_coef: float = config.get('muscle_coef')
        
        self.traits_per_box: int = config.get('traits_per_box')
        self.traits_extra: int = config.get('traits_extra')
        self.trait_count = self.CW * self.CH * self.beats_per_cycle * self.traits_per_box + self.traits_extra
        
        self.mutation_rate: float = config.get('mutation_rate')
        self.big_mutation_rate: float = config.get('big_mutation_rate')
        
        self.S_VISIBLE: float = 0.05 #what proportion of the population does a species need to appear on the SAC graph?
        self.S_NOTABLE: float = 0.10 #what proportion of the population does a species need to appear in the genealogy?
        self.HUNDRED: int = 100 # change this if you want to change the resolution of the percentile-tracking
        self.units_per_meter: float = config.get('units_per_meter')
        self.creatures = None
        self.rankings = np.zeros((0,self.creature_count), dtype=int)
        self.percentiles = np.zeros((0,self.HUNDRED + 1))
        self.species_pops: list = []
        self.species_info: list = []
        self.prominent_species: list = []
        self.ui = None
        self.last_gen_run_time: int = -1
        
    def initialize_universe(self):
        self.creatures = [[None] * self.creature_count]

        for c in range(self.creature_count):
            self.creatures[0][c] = self.create_new_creature(creature_id=c)
            self.species_info.append(SpeciesInfo(self, self.creatures[0][c], None))
            
        # We want to make sure that all creatures, even in their
        # initial state, are in calm equilibrium. They shouldn't
        # be holding onto potential energy (e.g. compressed springs)
        self.get_calm_states(0, 0, self.creature_count, self.stabilization_time) #Calm the creatures down so no potential energy is stored
        
        for c in range(self.creature_count):
            for i in range(2):
                self.creatures[0][c].icons[i] = self.creatures[0][c].draw_icon(self.ui.icon_dim[i], Color.MOSAIC, self.beat_fade_time)
            
        self.ui.draw_creature_mosaic(0)

    @property
    def creature_count(self):
        return self._creature_count

    @creature_count.setter
    def creature_count(self, value: int):
        self._creature_count = value

    def create_new_creature(self, creature_id) -> Creature:
        dna = np.clip(np.random.normal(0.0, 1.0, self.trait_count),-3,3)
        return Creature(dna, creature_id, -1, self, self.ui)
        
    def get_calm_states(self, gen, start_index, end_index, frame_count) -> None:
        param = self.simulate_import(gen, start_index, end_index, False)
        node_coor, muscles, _ = self.simulate_run(param, frame_count, True)

        for c in range(self.creature_count):
            self.creatures[gen][c].save_calm_state(node_coor[c])
            
    def get_starting_node_coor(self, gen, start_index, end_index, from_calm_state):
        count = end_index - start_index
        n = np.zeros((count,self.CH+1,self.CW+1,self.node_coor_count))

        if not from_calm_state or self.creatures[gen][0].calmState is None:
            # create grid of nodes along perfect gridlines
            coor_grid = np.mgrid[0:self.CW+1,0:self.CH+1]
            coor_grid = np.swapaxes(np.swapaxes(coor_grid,0,1),1,2)
            n[:,:,:,0:2] = coor_grid

        else:
            # load calm state into nodeCoor
            for c in range(start_index, end_index):
                n[c - start_index, :, :, :] = self.creatures[gen][c].calmState
                n[c - start_index, :, :, 1] -= self.CH  # lift the creature above ground level

        return n

    def get_muscle_array(self, gen, start_index, end_index):
        count = end_index - start_index
        m = np.zeros((count, self.CH, self.CW, self.beats_per_cycle, self.traits_per_box + 1)) # add one trait for diagonal length.
        dna_len = self.CH * self.CW * self.beats_per_cycle * self.traits_per_box

        for c in range(start_index, end_index):
            dna = self.creatures[gen][c].dna[0:dna_len].reshape(self.CH,self.CW,self.beats_per_cycle,self.traits_per_box)
            m[c - start_index, :, :, :, :self.traits_per_box] = 1.0 + dna / 3.0

        m[:,:,:,:,3] = np.sqrt(np.square(m[:,:,:,:,0]) + np.square(m[:,:,:,:,1])) # Set diagonal tendons

        return m

    def simulate_import(self, gen, start_index, end_index, from_calm_state):
        node_coor = self.get_starting_node_coor(gen, start_index, end_index, from_calm_state)
        muscles = self.get_muscle_array(gen, start_index, end_index)
        current_frame: int = 0

        return node_coor, muscles, current_frame

    def frame_to_beat(self, f):
        return (f//self.beat_time) % self.beats_per_cycle
        
    def frame_to_beat_fade(self, f):
        prog = f % self.beat_time
        return min(prog / self.beat_fade_time, 1)

    def simulate_run(self, param, frame_count, calming_run):
        node_coor, muscles, start_current_frame = param
        friction = self.calming_friction_coef if calming_run else self.typical_friction_coef
        ceiling_y = self.y_clips[0]
        floor_y = self.y_clips[1]
        
        for f in range(frame_count):
            current_frame = start_current_frame+f
            beat = 0
            if not calming_run:
                beat = self.frame_to_beat(current_frame)
                node_coor[:,:,:,3] += self.gravity_acceleration_coef
                # decrease y-velo (3rd node coor) by G
            apply_muscles(node_coor, muscles[:, :, :, beat, :], self.muscle_coef)
            node_coor[:,:,:,2:4] *= friction
            node_coor[:,:,:,0:2] += node_coor[:,:,:,2:4]
            # all node's x and y coordinates are adjusted by velocity_x and velocity_y
            if not calming_run:    # dealing with collision with the ground.
                nodes_touching_ground = np.ma.masked_where(node_coor[:,:,:,1] >= floor_y, node_coor[:,:,:,1])
                m = nodes_touching_ground.mask.astype(float) # mask that only countains 1's where nodes touch the floor
                pressure = node_coor[:,:,:,1] - floor_y
                ground_friction_multiplier = 0.5 ** (m*pressure*self.ground_friction_coef)
                
                node_coor[:,:,:,1] = np.clip(node_coor[:,:,:,1], ceiling_y, floor_y) # clip nodes below the ground back to ground level
                node_coor[:,:,:,2] *= ground_friction_multiplier # any nodes touching the ground must be slowed down by ground friction.
        
        if calming_run: # If it's a calming run, then take the average location of all nodes to center it at the origin.
            node_coor[:,:,:,0] -= np.mean(node_coor[:,:,:,0], axis=(1,2), keepdims=True)

        return node_coor, muscles, start_current_frame + frame_count
        
    def do_species_info(self, nsp, best_of_each_species) -> None:
        nsp: dict = dict(sorted(nsp.items()))
        running: int = 0
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
            if pop >= self.creature_count*self.S_NOTABLE and not info.prominent:  #prominent threshold
                info.become_prominent()
                
    def check_alap(self) -> None:
        if self.ui.alap_button.setting == 1: # We're already ALAP-ing!
            self.do_generation(self.ui.do_gen_button)
        
    def do_generation(self, button):
        generation_start_time = time.time() #calculates how long each generation takes to run
        
        gen = len(self.creatures) - 1
        creature_state = self.simulate_import(gen, 0, self.creature_count, True)
        node_coor, muscles, _ = self.simulate_run(creature_state, self.trial_time, False)
        final_scores = node_coor[:,:,:,0].mean(axis=(1, 2)) # find each creature's average X-coordinate
        
        # Tallying up all the data
        curr_rankings = np.flip(np.argsort(final_scores), axis=0)
        new_percentiles = np.zeros((self.HUNDRED + 1))
        new_species_pops = {}
        best_of_each_species = {}

        for rank in range(self.creature_count):
            c = curr_rankings[rank]
            self.creatures[gen][c].fitness = final_scores[c]
            self.creatures[gen][c].rank = rank
            
            species = self.creatures[gen][c].species
            if species in new_species_pops:
                new_species_pops[species][0] += 1
            else:
                new_species_pops[species] = [1, None, None]
            if species not in best_of_each_species:
                best_of_each_species[species] = self.creatures[gen][c].id_number

        self.do_species_info(new_species_pops, best_of_each_species)

        for p in range(self.HUNDRED+1):
            rank = min(int(self.creature_count * p / self.HUNDRED), self.creature_count - 1)
            c = curr_rankings[rank]
            new_percentiles[p] = self.creatures[gen][c].fitness
        
        next_creatures = [None] * self.creature_count

        for rank in range(self.creature_count // 2):
            winner = curr_rankings[rank]
            loser = curr_rankings[(self.creature_count - 1) - rank]
            if random.uniform(0,1) < rank/self.creature_count:
                ph = loser
                loser = winner
                winner = ph

            next_creatures[winner] = None
            if random.uniform(0,1) < rank/self.creature_count*2.0:  # A 1st place finisher is guaranteed to make a clone, but as we get closer to the middle the odds get more likely we just get 2 mutants.
                next_creatures[winner] = self.mutate(self.creatures[gen][winner], (gen+1) * self.creature_count + winner)
            else:
                next_creatures[winner] = self.clone(self.creatures[gen][winner], (gen+1) * self.creature_count + winner)

            next_creatures[loser] = self.mutate(self.creatures[gen][winner], (gen+1) * self.creature_count + loser)
            self.creatures[gen][loser].living = False
        
        self.creatures.append(next_creatures)
        self.rankings = np.append(self.rankings, curr_rankings.reshape((1,self.creature_count)), axis=0)
        self.percentiles = np.append(self.percentiles,new_percentiles.reshape((1,self.HUNDRED+1)), axis=0)
        self.species_pops.append(new_species_pops)
        
        draw_all_graphs(self, self.ui)
        
        self.get_calm_states(gen + 1, 0, self.creature_count, self.stabilization_time)

        #Calm the creatures down so no potential energy is stored

        for c in range(self.creature_count):
            for i in range(2):
                self.creatures[gen+1][c].icons[i] = self.creatures[gen+1][c].draw_icon(self.ui.icon_dim[i], Color.MOSAIC, self.beat_fade_time)
  
        self.ui.gen_slider.val_max = gen + 1
        self.ui.gen_slider.manualUpdate(gen)
        self.last_gen_run_time = time.time() - generation_start_time
        
        self.ui.creature_location_highlight = [None, None, None]
        self.ui.detect_mouse_motion()
        
    def get_creature_with_id(self, creature_id):
        return self.creatures[creature_id // self.creature_count][creature_id % self.creature_count]
        
    def clone(self, parent, new_id) -> Creature:
        return Creature(parent.dna, new_id, parent.species, self, self.ui)
        
    def mutate(self, parent, new_id) -> Creature:
        new_dna, new_species, cwc = parent.get_mutated_dna(self)
        new_creature = Creature(new_dna, new_id, new_species, self, self.ui)

        if new_creature.species != parent.species:
            self.species_info.append(SpeciesInfo(self, new_creature,parent))
            new_creature.codon_with_change = cwc

        return new_creature