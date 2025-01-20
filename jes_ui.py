from typing import Optional

import pygame
from pygame import Surface
from pygame.font import Font

from enums import Color
from jes_creature import Creature
from jes_species_info import SpeciesInfo
from utils import species_to_color, species_to_name, dist_to_text, bound, get_dist, array_int_multiply
from jes_dataviz import display_all_graphs, draw_all_graphs
from jes_shapes import  draw_ring_light, draw_x, center_text, align_text, draw_species_circle
from jes_slider import Slider
from jes_button import Button
import time
import numpy as np

import random

class UI:
    def __init__(self, config: dict):
        self.title: str = config.get('title')
        pygame.display.set_caption(self.title)
        pygame.font.init()
        self.big_font: Font = pygame.font.Font('./visuals/Arial.ttf', 60)
        self.small_font: Font = pygame.font.Font('./visuals/Arial.ttf', 30)
        self.tiny_font: Font = pygame.font.Font('./visuals/Arial.ttf', 21)
        self.background_pic = pygame.image.load("visuals/background.png")

        self.window_width: int = config.get('window_width')
        self.window_height: int = config.get('window_height')
        self.movie_single_dim: list[int] = config.get('movie_single_dim')
        self.info_w: int = config.get('movie_single_dim')[0]
        
        self.graph_coor: list[int] = config.get('graph_coor')
        self.graph = pygame.Surface(self.graph_coor[2:4], pygame.SRCALPHA, 32)
        self.sac_coor: list[int] = config.get('sac_coor')
        self.sac = pygame.Surface(self.sac_coor[2:4], pygame.SRCALPHA, 32)
        self.genealogy_coor: list = config.get('genealogy_coor')
        self.gene_graph: Surface = pygame.Surface(self.genealogy_coor[2:4], pygame.SRCALPHA, 32)
        
        self.column_margin: int = config.get('column_margin')
        self.mosaic_dim: list[int] = config.get('mosaic_dim')
        self.menu_text_up: int = config.get('menu_text_up')
        
        self.cm_margin_1: int = config.get('cm_margin_1')
        self.cm_margin_2: int = config.get('cm_margin_2')

        self.mosaic_screen_width: int = self.window_width - self.cm_margin_1 * 2
        self.mosaic_screen_width_creatures: int = self.mosaic_screen_width - self.info_w - self.column_margin  # mosaic screen width (just creatures)
        self.mosaic_screen_height = self.window_height - self.menu_text_up - self.cm_margin_1 * 2
        
        s1: int = int(self.mosaic_screen_width_creatures / self.mosaic_dim[0] - self.cm_margin_2 * 2)
        s2: int = int(self.mosaic_screen_width_creatures / self.mosaic_dim[1] - self.cm_margin_2 * 2)
        self.icon_dim = ((s1, s1), (s2, s2), (s2, s2))
        
        self.mosaic_visible: bool = False
        self.creature_location_highlight: list = [None, None, None]  # Creature Location Highlight. First: is it in the mosaic (0), or top-3? (1). Second: Index of highlighted creature? Third: rank of creature?
        self.creature_highlight: list = []
        self.slider_drag = None
        
        self.visual_sim_memory: list = []
        self.movie_screens: list = []
        self.sim = None
        
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        self.mosaic_screen: Surface = pygame.Surface((self.mosaic_screen_width_creatures, self.mosaic_screen_height), pygame.SRCALPHA, 32)
        self.info_bar_screen: Surface = pygame.Surface((self.info_w, self.mosaic_screen_height), pygame.SRCALPHA, 32)
        self.preview_locations: list[list[int]] = [[570, 105, 250, 250], [570, 365, 250, 250], [570, 625, 250, 250]]
        self.salt: str = str(random.uniform(0,1))
        self.sc_colors: dict = {} # special-case colors: species colored by the user, not RNG
        
        # variables for the "Watch sample" button
        self.sample_frames: int = 0
        self.sample_i: int = 0

        self.fps= config.get('fps')

        pygame.time.Clock().tick(self.fps)

        self.sample_freeze_time: int = 90
        self.show_xs: bool = True
        self.species_storage = None
        self.storage_coor = (660, 52)
        self.running: bool = True

        self.slider_list: list[Slider] = []
        self.button_list: list[Button] = []

        self.gen_slider: Slider = Optional[Slider]
        self.show_creatures_button: Button = Optional[Button]
        self.sort_button: Button = Optional[Button]
        self.style_button: Button = Optional[Button]
        self.sample_button: Button = Optional[Button]
        self.do_gen_button: Button = Optional[Button]
        self.alap_button: Button = Optional[Button]


    def add_buttons_and_sliders(self):
        self.gen_slider: Slider = Slider(pdim=(40, self.window_height - 100, self.window_width - 80, 60, 140), callback_func=self.update_gen_slider)

        self.slider_list.append(self.gen_slider)

        button_coor = []
        for i in range(6):
            button_coor.append((self.window_width - 1340 + 220 * i, self.window_height - self.menu_text_up, 200, 60))

        self.show_creatures_button = Button(button_coor[0], ["Show creatures", "Hide creatures"], self.toggle_creatures)
        self.button_list.append(self.show_creatures_button)

        self.sort_button = Button(button_coor[1], ["Sort by ID", "Sort by fitness", "Sort by weakness"], self.toggle_sort)
        self.button_list.append(self.sort_button)

        self.style_button = Button(button_coor[2], ["Big Icons", "Small Icons", "Species Tiles"], self.toggle_style)
        self.button_list.append(self.style_button)

        self.sample_button = Button(button_coor[3], ["Watch sample", "Stop sample"], self.start_sample)
        self.button_list.append(self.sample_button)

        self.do_gen_button = Button(button_coor[4], ["Do a generation"], self.sim.do_generation)
        self.button_list.append(self.do_gen_button)

        self.alap_button = Button(button_coor[5], ["Turn on ALAP", "Turn off ALAP"], self.do_nothing)
        self.button_list.append(self.alap_button)

        
    def reverse(self, i):
        return self.sim.creature_count-1-i
        
    def detect_mouse_motion(self):
        if self.sample_button.setting == 1:
            return
        gen = self.gen_slider.val
        mouse_x, mouse_y = pygame.mouse.get_pos()
        new_clh = [None,None,None]
        if self.mosaic_visible:
            rel_mouse_x = mouse_x-self.cm_margin_1
            rel_mouse_y = mouse_y-self.cm_margin_1
            if 0 <= rel_mouse_x < self.mosaic_screen_width_creatures and 0 <= rel_mouse_y < self.mosaic_screen_height:
                dim = self.mosaic_dim[self.style_button.setting]
                spacing = self.mosaic_screen_width_creatures / dim
                ix = min(int(rel_mouse_x/spacing),dim)
                iy = int(rel_mouse_y/spacing)
                i = iy*dim+ix
                if 0 <= i < self.sim.creature_count:
                    sort = self.sort_button.setting
                    if sort == 0 or gen >= len(self.sim.rankings):
                        new_clh = [0,i,i]
                    elif sort == 1:
                        new_clh = [0,self.sim.rankings[gen][i],i]
                    elif sort == 2:
                        new_clh = [0,self.sim.rankings[gen][self.reverse(i)],i]
                        
        elif 0 <= gen < len(self.sim.rankings):
            # rolling mouse over the Best+Median+Worst previews
            for r in range(len(self.preview_locations)):
                pl = self.preview_locations[r]
                if pl[0] <= mouse_x < pl[0]+pl[2] and pl[1] <= mouse_y < pl[1] + pl[3]:
                    index = self.sim.rankings[gen][self.r_to_rank(r)]
                    new_clh = [1,index,r]
            
            # rolling mouse over species circles
            r_x = mouse_x-self.genealogy_coor[0]
            r_y = mouse_y-self.genealogy_coor[1]
            if 0 <= r_x < self.genealogy_coor[2] and 0 <= r_y < self.genealogy_coor[3]:
                answer = self.get_roll_over(r_x, r_y)
                if answer is not None:
                    new_clh = [2, answer]
                    
            # rolling over storage
            if self.species_storage is not None and get_dist(mouse_x, mouse_y, self.storage_coor[0], self.storage_coor[1]) <= self.genealogy_coor[4]:
                new_clh = [2, self.species_storage]
                       
        if new_clh[1] != self.creature_location_highlight[1]:
            self.creature_location_highlight = new_clh
            if self.creature_location_highlight[1] is None:
                self.clear_movies()
            elif self.creature_location_highlight[0] == 2: # a species was highlighted
                info = self.sim.species_info[self.creature_location_highlight[1]]
                l = len(info.reps)
                self.visual_sim_memory = []
                self.creature_highlight = []
                self.movie_screens = []
                for i in range(l):
                    some_id = info.reps[i]
                    gen = some_id // self.sim.creature_count
                    c = some_id % self.sim.creature_count

                    self.creature_highlight.append(self.sim.creatures[gen][c])
                    self.visual_sim_memory.append(self.sim.simulate_import(gen, c, c + 1, True))
                    self.movie_screens.append(None)

                self.draw_info_bar_species(self.creature_location_highlight[1])
            else: # a creature was highlighted!
                self.creature_highlight = [self.sim.creatures[gen][self.creature_location_highlight[1]]]
                self.visual_sim_memory = [self.sim.simulate_import(gen, self.creature_location_highlight[1], self.creature_location_highlight[1] + 1, True)]
                self.movie_screens = [None] * 1
                self.draw_info_bar_creature(self.sim.creatures[gen][self.creature_location_highlight[1]])
        
    def clear_movies(self) -> None:
        self.visual_sim_memory = []
        self.creature_highlight = []
        self.movie_screens = []
        self.creature_location_highlight = [None, None, None]
                
    def get_roll_over(self, mouse_x, mouse_y):
        answer = None
        ps = self.sim.prominent_species
        for level in range(len(ps)):
            for i in range(len(ps[level])):
                s = ps[level][i]
                s_x, s_y = self.sim.species_info[s].coor
                if get_dist(mouse_x, mouse_y, s_x, s_y) <= self.genealogy_coor[4]:
                    answer = s
        return answer
        
    def draw_creature_mosaic(self, gen) -> None:
        self.mosaic_screen.fill(Color.MOSAIC)

        for c in range(self.sim.creature_count):
            i = c
            if self.sim.creatures[gen][c].rank is not None:
                if self.sort_button.setting == 1:
                    i = self.sim.creatures[gen][c].rank
                elif self.sort_button.setting == 2:
                    i = self.reverse(self.sim.creatures[gen][c].rank)
            dim = self.mosaic_dim[self.style_button.setting]
            x = i % dim
            y = i//dim
            creature = self.sim.creatures[gen][c]
            spacing = self.mosaic_screen_width_creatures / dim
            creature.icon_coor = (x * spacing + self.cm_margin_2, y * spacing + self.cm_margin_2, spacing, spacing)
            if creature.icon_coor[1] < self.mosaic_screen.get_height():
                s = self.style_button.setting
                if s <= 1:
                    self.mosaic_screen.blit(creature.icons[s], creature.icon_coor)
                elif s == 2:
                    extra = 1
                    pygame.draw.rect(self.mosaic_screen, species_to_color(creature.species, self), (creature.icon_coor[0], creature.icon_coor[1], spacing + extra, spacing + extra))
                if not creature.living and self.show_xs:
                    color = (255,0,0) if s <= 1 else (0,0,0)
                    draw_x(creature.icon_coor, self.icon_dim[s][0], color, self.mosaic_screen)

    def draw_info_bar_creature(self, creature: Creature) -> None:
        x_center = int(self.info_w * 0.5)
        self.info_bar_screen.fill(Color.MOSAIC)

        stri: list[str] = [f"Creature #{creature.id_number}", f"Species: {species_to_name(creature.species, self)}", "Untested"]
        if creature.fitness is not None:
            fate = "Living" if creature.living else "Killed"
            stri = [f"Creature #{creature.id_number}", f"Species: {species_to_name(creature.species, self)}", f"Fitness: {dist_to_text(creature.fitness, True, self.sim.units_per_meter)}", f"Rank: {creature.rank + 1} - {fate}"]
            
        for i in range(len(stri)):
            color = Color.WHITE
            if stri[i][0:7] == "Species":
                color = species_to_color(creature.species, self)

            center_text(self.info_bar_screen, stri[i], x_center, self.movie_single_dim[1] + 40 + 42 * i, color, self.small_font)
    
    def draw_movie_grid(self, screen, coor, mask, titles, colors, font) -> None:
        lms = len(self.movie_screens)
        per_row = 1 if lms == 1 else lms//2
        for i in range(lms):
            if mask is not None and not mask[i]:
                continue
            ms = self.movie_screens[i]
            w = ms.get_width()
            h = ms.get_height()
            x = coor[0]+(i%per_row) * w
            y = coor[1]+(i//per_row) * h
            screen.blit(ms,(x,y))
            if titles is not None:
                center_text(screen, titles[i], x + w / 2, y + h - 30, colors[i], font)
    
    def draw_movie_quad(self, species) -> None:
        l = 4
        info: SpeciesInfo = self.sim.species_info[species]
        a_name = species_to_name(info.ancestor_id, self)
        s_name = species_to_name(species, self)
        titles = ["Ancestor","First","Apex","Last"]
        mask = [True] * l

        for i in range(l):
            if (info.ancestor_id is None and i == 0) or (i >= 2 and info.get_when(i) == info.get_when(i - 1)):
                mask[i] = False
                continue

            stri = a_name if i == 0 else s_name
            performance = info.get_performance(self.sim, i)
            titles[i] = f"G{info.get_when(i)}: {titles[i]} {stri} ({dist_to_text(performance, True, self.sim.units_per_meter)})"

        coor = (self.cm_margin_1 + self.mosaic_screen_width_creatures, 0)
        self.draw_movie_grid(self.screen, coor, mask, titles, [Color.GRAYISH] * l, self.tiny_font)
        
        
    def draw_info_bar_species(self, species) -> None:
        self.info_bar_screen.fill(Color.MOSAIC)
        info = self.sim.species_info[species]
        a_name = species_to_name(info.ancestor_id, self)
        s_name = species_to_name(species, self)
        now = min(self.gen_slider.val, len(self.sim.species_pops) - 1)
        now_pop = 0
        extinct_string = " (Extinct)"
        if species in self.sim.species_pops[now]:
            now_pop = self.sim.species_pops[now][species][0]
            extinct_string = ""
        strings = [f"Species {s_name}",f"Ancestor {a_name}",f"Lifespan: G{info.get_when(1)} - G{info.get_when(3)}{extinct_string}", f"Population:   {info.apex_pop} at apex (G{info.get_when(2)})   |   {now_pop} now (G{now})"]
        colors = [Color.WHITE]*len(strings)
        colors[0] = species_to_color(species, self)
        if info.ancestor_id is None:
            strings[1] = "Primordial species"
        else:
            colors[1] = species_to_color(info.ancestor_id, self)
        for i in range(len(strings)):
            x_center = int(self.info_w * (0.5 if i == 3 else 0.3))
            center_text(self.info_bar_screen, strings[i], x_center, self.movie_single_dim[1] + 40 + 42 * i, colors[i], self.small_font)
        
        self.draw_lightboard(self.info_bar_screen, species, now, (self.info_w * 0.6, self.movie_single_dim[1] + 10, self.info_w * 0.37, self.mosaic_screen_height - self.movie_single_dim[1] - 20))
        
    def draw_lightboard(self, screen, species, gen, coor) -> None:
        dim = self.mosaic_dim[-1]
        r = coor[2]/dim
        for c in range(self.sim.creature_count):
            x = coor[0] + r * (c % dim)
            y = coor[1] + r * (c // dim)
            col = (0,0,0)
            creature = self.sim.creatures[gen][self.sim.rankings[gen][c]]
            if creature.species == species:
                col = species_to_color(species, self)
            pygame.draw.rect(screen,col,(x,y,r,r))
        
    def draw_menu_text(self) -> None:
        y = self.window_height - self.menu_text_up
        title_surface = self.big_font.render(self.title, False, Color.GRAYISH)
        self.screen.blit(title_surface,(40,20))
        a = str(int(self.gen_slider.val))
        b = str(int(self.gen_slider.val_max))
        gen_surface = self.big_font.render("Generation " + a + " / " + b, False, (255, 255, 255))
        self.screen.blit(gen_surface,(40,y))
        if self.species_storage is not None:
            s = self.species_storage
            r = self.genealogy_coor[4]
            draw_species_circle(self.screen, s, self.storage_coor, r, self.sim, self.sim.species_info, self.tiny_font, False, self)
        
    def r_to_rank(self,r):
        return 0 if r == 0 else (self.sim.creature_count - 1 if r == 2 else self.sim.creature_count // 2)
        
    def draw_previews(self) -> None:
        gen = self.gen_slider.val
        if 0 <= gen < len(self.sim.rankings):
            names = ["Best","Median","Worst"]
            for r in range(3):
                r_i = self.r_to_rank(r)
                index = self.sim.rankings[gen][r_i]
                creature = self.sim.creatures[gen][index]
                dim = (self.preview_locations[r][2], self.preview_locations[r][3])
                preview = creature.draw_icon(dim, Color.MOSAIC, self.sim.beat_fade_time)
                center_text(preview, f"{names[r]} creature", dim[0] / 2, dim[1] - 20, Color.WHITE, self.small_font)
                align_text(preview, dist_to_text(creature.fitness, True, self.sim.units_per_meter), 10, 20, Color.WHITE, self.small_font, 0.0, None)
                self.screen.blit(preview, (self.preview_locations[r][0], self.preview_locations[r][1]))

    def do_movies(self) -> None:
        l = len(self.visual_sim_memory)
        mscale = [1, 1, 0.5, 0.70]  # movie screen scale
        if self.sample_button.setting == 1:
            self.sample_frames += 1
            if self.sample_frames >= self.sim.trial_time+self.sample_freeze_time:
                self.start_sample_helper()

        for i in range(l):
            if self.visual_sim_memory[i][2] < self.sim.trial_time:
                self.visual_sim_memory[i] = self.sim.simulate_run(self.visual_sim_memory[i], 1, False)

            try:
                dim = array_int_multiply(self.movie_single_dim, mscale[self.creature_location_highlight[0]])


                self.movie_screens[i] = pygame.Surface(dim, pygame.SRCALPHA, 32)

                node_arr, _, current_frame = self.visual_sim_memory[i]
                s = dim[0]/(self.sim.CW+2)*0.5 # visual transform scale

                average_x = np.mean(node_arr[:,:,:,0])
                transform = [dim[0]/2 - average_x*s,dim[1]*0.8,s]
                self.creature_highlight[i].draw_creature(self.movie_screens[i], node_arr[0], current_frame, transform, True, (i == 0))

            except TypeError as _:
                pass
                
    def get_highlighted_species(self):
        gen = self.gen_slider.val
        if self.creature_location_highlight[0] == 2:
            return self.creature_location_highlight[1]
        elif self.creature_location_highlight[0] == 0 or self.creature_location_highlight[0] == 1:
            return self.sim.creatures[gen][self.creature_location_highlight[1]].species

        return None

    def detect_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == 27: # pressing escape
                    self.running = False
                new_gen = None
                if event.key == pygame.K_LEFT:
                    new_gen = max(0, self.gen_slider.val - 1)
                if event.key == pygame.K_RIGHT:
                    new_gen = min(self.gen_slider.val_max, self.gen_slider.val + 1)
                if new_gen is not None:
                    self.gen_slider.manual_update(new_gen)
                    self.clear_movies()
                    self.detect_mouse_motion()
                if event.key == 120: # pressing X will hide the Xs showing killed creatures
                    self.show_xs = (not self.show_xs)
                    self.draw_creature_mosaic(self.gen_slider.val)
                elif event.key == 115: # pressing S will store the species of the creature you're rolling over into "storage".
                    self.species_storage = self.get_highlighted_species()
                elif event.key == 99: # pressing C will change the highlighted species's color.
                    c = self.get_highlighted_species()
                    if c is not None:
                        self.sc_colors[c] = str(random.uniform(0,1))
                        draw_all_graphs(self.sim, self)
                        self.clear_movies()
                        self.detect_mouse_motion()

                elif event.key == 13: # pressing Enter
                    self.sim.do_generation(None)

                elif event.key == 113: # pressing 'Q'
                    self.show_creatures_button.time_of_last_click = time.time()
                    self.show_creatures_button.setting = 1 - self.show_creatures_button.setting
                    self.toggle_creatures(self.show_creatures_button)
                
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                for slider in self.slider_list:
                    s_x, s_y, s_w, s_h, s_dw = slider.dim
                    if s_x <= mouse_x < s_x+s_w and s_y <= mouse_y < s_y + s_h:
                        self.slider_drag = slider
                        break
                for button in self.button_list:
                    s_x, s_y, s_w, s_h = button.dim
                    if s_x <= mouse_x < s_x+s_w and s_y <= mouse_y < s_y + s_h:
                        button.click()

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.slider_drag is not None:
                    self.slider_drag.update_val()
                    self.slider_drag = None

    def draw_menu(self) -> None:
        self.screen.blit(self.background_pic, (0, 0))
        self.draw_menu_text()
        self.draw_previews()

        display_all_graphs(self.screen, self.sim, self)

        self.draw_sliders_and_buttons()
        self.display_creature_mosaic(self.screen)
        self.display_movies(self.screen)

    def display_creature_mosaic(self, screen):
        time_since_last_press = time.time()-self.show_creatures_button.time_of_last_click
        pan_time = 0.2
        frac = bound(time_since_last_press/pan_time)

        if self.mosaic_visible:
            panel_y = self.cm_margin_1 - self.mosaic_screen.get_height() * (1 - frac)
            screen.blit(self.mosaic_screen, (self.cm_margin_1, panel_y))
        if not self.mosaic_visible and frac < 1:
            self.screen.blit(self.mosaic_screen, (self.cm_margin_1, self.cm_margin_1 - self.mosaic_screen.get_height() * frac))
    
    def display_movies(self, screen) -> None:
        if self.creature_location_highlight[0] is None:
            return

        if self.creature_location_highlight[0] == 3:
            lms = len(self.movie_screens)
            species_names = [None] * lms
            species_colors = [None] * lms
            for i in range(lms):
                sp = self.creature_highlight[i].species
                species_names[i] = species_to_name(sp, self)
                species_colors[i] = species_to_color(sp, self)

            self.draw_movie_grid(screen, (0, 0), [True] * lms, species_names, species_colors, self.small_font)
            return

        gen = self.gen_slider.val
        coor = (self.cm_margin_1 + self.mosaic_screen_width_creatures, 0)
        self.screen.blit(self.info_bar_screen, coor)
        if self.creature_location_highlight[0] == 2:
            self.draw_movie_quad(self.creature_location_highlight[1])
            return
        self.screen.blit(self.movie_screens[0], coor)
        if self.creature_location_highlight[0] == 1:
            dim = self.preview_locations[self.creature_location_highlight[2]]
            self.screen.blit(draw_ring_light(dim[2], dim[3], 6), (dim[0], dim[1]))
        else:
            coor = self.sim.creatures[gen][self.creature_location_highlight[1]].icon_coor
            x = coor[0]+self.cm_margin_1
            y = coor[1]+self.cm_margin_1
            self.screen.blit(draw_ring_light(coor[2], coor[3], 6), (x, y))


    def detect_sliders(self):
        if self.slider_drag is not None:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            s_x, s_y, s_w, s_h, s_dw = self.slider_drag.dim
            ratio = bound(((mouse_x-s_dw*0.5)-s_x)/(s_w-s_dw))
            
            s_range = self.slider_drag.val_max - self.slider_drag.val_min
            self.slider_drag.tval = ratio * s_range + self.slider_drag.val_min
            if self.slider_drag.snap_to_int:
                self.slider_drag.tval = round(self.slider_drag.tval)
            if self.slider_drag.update_live:
                self.slider_drag.update_val()
       
    def draw_sliders_and_buttons(self):
        for slider in self.slider_list:
            slider.draw_slider(self.screen)

        for button in self.button_list:
            button.draw_button(self.screen, self.small_font)
       
    # Button and slider functions
    def update_gen_slider(self, gen):
        self.draw_creature_mosaic(gen)
        
    def toggle_creatures(self, button):
        self.mosaic_visible = (button.setting == 1)
        
    def toggle_sort(self, button):
        self.draw_creature_mosaic(self.gen_slider.val)
        
    def toggle_style(self, button):
        self.draw_creature_mosaic(self.gen_slider.val)
    
    def do_nothing(self, button):
        pass
        
    def start_sample(self, button):
        if button.setting == 1:
            self.sample_i = 0
            self.start_sample_helper()
        
    def start_sample_helper(self):
        l = 8
        self.creature_highlight = []
        self.visual_sim_memory = []
        self.movie_screens = []
        self.creature_location_highlight = [3, 0]
        self.sample_frames = 0
        for i in range(l):
            gen = self.gen_slider.val
            c = (self.sample_i+i)%self.sim.creature_count
            self.creature_highlight.append(self.sim.creatures[gen][c])
            self.visual_sim_memory.append(self.sim.simulate_import(gen, c, c + 1, True))
            self.movie_screens.append(None)

        self.sample_i += l

    @staticmethod
    def show():
        pygame.display.flip()
