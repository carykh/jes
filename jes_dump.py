"""def getSpecies(self):
        BOXES = CW*CH*BEATS_PER_CYCLE
        TOTAL = TRAITS_PER_BOX*BOXES
        dna_reshaped = np.zeros((TRAITS_PER_BOX,BOXES))
        for t in range(TRAITS_PER_BOX):
            for u in range(BOXES):
                dna_reshaped[t][u] = self.dna[u*TRAITS_PER_BOX+t]
        dna_up_down = np.zeros((TOTAL))
        for t in range(TRAITS_PER_BOX):
            for u in range(BOXES):
                val = 1 if dna_reshaped[t][u] >= np.mean(dna_reshaped[t]) else 0
                dna_up_down[t*BOXES+u] = val
        
        pre_stri = DUDtoPRESTRI(dna_up_down[128:144], 16)  #I'm only taking rigidity on Frame 1 into account now.
        self.dudly = pre_stri
        _hex = sha256(pre_stri.encode('utf-8')).hexdigest()
        return int(_hex, 16)%SPECIES_COUNT"""
        
        
        
        
        """if data[g,s] >= 1 or (g >= 1 and data[g-1,s] >= 1):
                y1a = H/2
                y1b = H/2
                y2a = np.sum(data[g,0:s])*FAC
                y2b = np.sum(data[g,0:s+1])*FAC
                if g >= 1:
                    y1a = np.sum(data[g-1,0:s])*FAC
                    y1b = np.sum(data[g-1,0:s+1])*FAC
                
                pygame.draw.polygon(sac,speciesToColor(s),points)"""
                
                
                
"""
for s in range(CREATURE_COUNT):
            d = species_pops[a2,s]
            if d >= CREATURE_COUNT*0.05:
                speciesI = runningTotal+d*0.5
                speciesY = 560+300*speciesI/CREATURE_COUNT
                name = species_to_name(s)
                color = speciesToColor(s)
                alignText(screen, f"{name}: {int(d)}", 860+880*frac, speciesY, color, smallFont, 0.0, True)
            runningTotal += d
            """
            
            
            
            
            """CREATURE_COUNT = 250
SPECIES_COUNT = CREATURE_COUNT
STABILIZATION_TIME = 200
TRIAL_TIME = 300
BEAT_TIME = 20
BEAT_FADE_TIME = 5
CW = 4
CH = 4
CREATURE_DIM = [CW,CH]
BEATS_PER_CYCLE = 3
NODE_COOR_COUNT = 4 

CEILING_Y = -10000000
FLOOR_Y = 0
GROUND_FRICTION_COEF = 25 # the higher the number, the more ground friction is applied.

GRAVITY_ACCELERATION_COEF = 0.002
CALMING_FRICTION_COEF = 0.7
TYPICAL_FRICTION_COEF = 0.8
MUSCLE_COEF = 0.08

TRAITS_PER_BOX = 3 
TRAITS_EXTRA = 1 # heartbeat (time)
TOTAL_TRAIT_COUNT = CW*CH*BEATS_PER_CYCLE*TRAITS_PER_BOX+TRAITS_EXTRA"""



"""
W_W = 1920
W_H = 1078

MOVIE_SINGLE_DIM = (650,650)
GRAPH_DIM = (1000,500)
graph = pygame.Surface(GRAPH_DIM, pygame.SRCALPHA, 32)
SAC_DIM = (1000,300)
sac = pygame.Surface(SAC_DIM, pygame.SRCALPHA, 32)


CREATURES_PER_ROW = 14
CREATURES_PER_COLUMN = 8
MENU_TEXT_UP = 180"""


def DUDtoPRESTRI(DUD, TOTAL):
    stri = ""
    PER = 1
    for i in range(math.ceil(TOTAL/PER)):
        _sum = 0
        for j in range(PER):
            _sum *= 2
            if i*PER+j < len(DUD) and DUD[i*PER+j] == 1:
                _sum += 1
        stri += chr(_sum+41)
    return stri
    
    
    
BG_COLOR = (0,0,0)
    RED = (255,0,0)
    GREEN = (0,255,0)
    GRAYISH = (108,118,155)
    BLACK = (0,0,0)
    WHITE = (255,255,255)
    GRAY25 = (70,70,70)
    GRAY50 = (128,128,128)
    MOSAIC_BG_COLOR = (80,80,80)
    BRIGHT = (255,255,0,200)
    SIGN_COLOR = (150,100,50)
    
    
    def doSpeciesInfo(self,nsp,best_of_each_species):
        p1 = 0 # 'p' stands for 'pointer'
        while p1 < self.creature_count:
            s = data[p1]
            p2 = bisect.bisect(data, s+0.5)
            pop = p2-p1
            
            sp = self.species_info[s]
            sp.latest_pop = pop
            if pop > sp.apex_pop: # This species reached its highest population
                sp.apex_pop = pop
                sp.reps[2] = best_of_each_species[s] # apex representative
            if pop > self.creature_count*0.10 and not sp.prominent:  #prominent threshold
                sp.become_prominent()
                
            sp.reps[3] = best_of_each_species[s] # most-recent representative
            p1 = p2
            
            
  
        p1 = 0 # 'p' stands for 'pointer'
        while p1 < c_count:
            s = data[g,p1]
            p2 = bisect.bisect(data[g], s+0.5)
            points = [[x1,H/2],[x1,H/2],[x2,H-p2*FAC],[x2,H-p1*FAC]]
            pygame.draw.polygon(sac,speciesToColor(s),points)
            p1 = p2
            
            
            
            
            
    data = sim.species_pops[g]
    p1 = p2 = 0
    record = 0
    recordHolder = -1
    while p1 < sim.creature_count:
        s = data[p1]
        p2 = bisect.bisect(data, s+0.5)
        pop = p2-p1
        if pop > record:
            record = pop
            recordHolder = s
        p1 = p2
    return recordHolder
    
    
    
p1 = p2 = q1 = q2 = i_start
    H = sac.get_height()
    while q1 < i_end:
        s = data[g1,q1]
        q2 = bisect.bisect(data[g1], s+0.5)
        p1 = bisect.bisect(data[g2], s-0.5)
        if p1 != p2 and level == 0: #there was a gap. (A species that existed in the previous gen, but not in this one)
            trapezoidHelper(sac, data, g2, g1, p2, p1, x2, x1, FAC, 1)
        p2 = bisect.bisect(data[g2], s+0.5)
        points = [[x1,H-p1*FAC],[x1,H-p2*FAC],[x2,H-q2*FAC],[x2,H-q1*FAC]]
        pygame.draw.polygon(sac,speciesToColor(s),points)
        q1 = q2
        
        
        
p1 = p2 = 0
    while p1 < sim.creature_count:
        s = sim.species_pops[a2,p1]
        p2 = bisect.bisect(sim.species_pops[a2], s+0.5)
        pop = p2-p1
        if pop >= sim.creature_count*sim.S_VISIBLE:
            speciesI = (p1+p2)/2
            speciesY = 560+300*(1 - speciesI / sim.creature_count)
            name = species_to_name(s)
            color = speciesToColor(s)
            OUTLINE = ui.WHITE if s == top_species else None
            alignText(screen, f"{name}: {int(pop)}", lineX + 10, speciesY, color, ui.small_font, 0.0, [ui.BLACK, OUTLINE])
        p1 = p2
        
        
"""top_species = getTopSpecies(sim, a2)
    pop = data[a2][top_species]
    speciesI = (pop[1]+pop[2])/2
    speciesY = 560+300*(1-speciesI/sim.c_count)
    name = species_to_name(s)
        color = speciesToColor(s)
        OUTLINE = ui.WHITE if s == top_species else None
        alignText(screen, f"{name}: {int(pop)}", lineX+10, speciesY, color, ui.smallFont, 0.0, [ui.BLACK,OUTLINE])
    
    p1 = p2 = 0
    while p1 < sim.c_count:
        s = sim.species_pops[a2,p1]
        p2 = bisect.bisect(sim.species_pops[a2], s+0.5)
        pop = p2-p1
        if pop >= sim.c_count*sim.S_VISIBLE:
            speciesI = (p1+p2)/2
            speciesY = 560+300*(1-speciesI/sim.c_count)
            name = species_to_name(s)
            color = speciesToColor(s)
            OUTLINE = ui.WHITE if s == top_species else None
            alignText(screen, f"{name}: {int(pop)}", lineX+10, speciesY, color, ui.smallFont, 0.0, [ui.BLACK,OUTLINE])
        p1 = p2"""
        
        
        
        p1 = p2 = 0
    
    while p1 < sim.creature_count:
        s = sim.species_pops[a2,p1]
        p2 = bisect.bisect(sim.species_pops[a2], s+0.5)
        info = sim.species_info[s]
        if info.prominent:
            pop = p2-p1
            circle_count = 1
            if s == top_species:
                circle_count += 1
            for c in range(circle_count):
                cx = info.coor[0]+ui.genealogy_coor[0]
                cy = info.coor[1]+ui.genealogy_coor[1]
                pygame.draw.circle(screen, ui.WHITE, (cx,cy), R+3+6*c, 3)
        p1 = p2
        
        
        
        """for i in range(L):
            if info.ancestorID is None and i == 0:
                continue
            if :  # Two movies are showing the same thing, which we don't need to do
                continue
            ms = self.movieScreens[i]
            MSCALE = int(math.sqrt(L))
            W = ms.get_width()
            H = ms.get_height()
            x = (i%MSCALE)*W
            y = (i//MSCALE)*H
            self.infoBarScreen.blit(ms,(x,y))
            centerText(self.infoBarScreen, titles[i], x+W/2, y+H-30, self.GRAYISH, self.tinyFont)"""