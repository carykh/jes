from jes_sim import Sim
from jes_ui import UI
from utils import read_config

sim_config_file: str = 'config/sim_config.json'
ui_config_file: str = 'config/ui_config.json'

sim_config: dict = read_config(filename=sim_config_file)
ui_config: dict = read_config(filename=ui_config_file)

c_input = input("How many creatures do you want?\n100: Lightweight\n250: Standard (if you don't type anything, I'll go with this)\n500: Strenuous (this is what my carykh video used)\n")
if c_input == "":
    c_input = "250"

# Simulation
# population size is 250 here, because that runs faster. You can increase it to 500 to replicate what was in my video, but do that at your own risk!



sim: Sim = Sim(creature_count=int(c_input), config=sim_config)

# Cosmetic UI variables

ui: UI = UI(config=ui_config)

# ui = UI(_W_W=1920, _W_H=1080, _MOVIE_SINGLE_DIM=(650,650),
# _GRAPH_COOR=(850,50,900,500), _SAC_COOR=(850,560,900,300), _GENEALOGY_COOR=(20,105,530,802,42),
# _COLUMN_MARGIN=330, _MOSAIC_DIM=[10,24,24,30], #_MOSAIC_DIM=[10,10,17,22],
# _MENU_TEXT_UP=180, _CM_MARGIN1=20, _CM_MARGIN2=1)

sim.ui = ui
ui.sim = sim
ui.add_buttons_and_sliders()
    
sim.initialize_universe()

while ui.running:
    sim.check_alap()
    ui.detect_mouse_motion()
    ui.detect_events()
    ui.detect_sliders()
    ui.do_movies()
    ui.drawMenu()
    ui.show()