from jes_sim import Sim
from jes_ui import UI
import logging
import sys

def setup_logging(level=logging.INFO, log_file='app.log'):
    # Create a formatter that includes timestamp, level, and module
    formatter = logging.Formatter('%(asctime)s - [%(filename)s:%(lineno)d] - [%(name)s:%(funcName)s] - %(levelname)s - %(message)s')
    
    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Optional: Add file handler for persistent logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    return root_logger

c_input = input("How many creatures do you want?\n100: Lightweight\n250: Standard (if you don't type anything, I'll go with this)\n500: Strenuous (this is what my carykh video used)\n")
if c_input == "":
    c_input = "250"

# Simulation
# population size is 250 here, because that runs faster. You can increase it to 500 to replicate what was in my video, but do that at your own risk!
logger = setup_logging()
sim = Sim(_c_count=int(c_input), _stabilization_time=200, _trial_time=600,
_beat_time=20, _beat_fade_time=5, _c_dim=[4,4],
_beats_per_cycle=3, _node_coor_count=4, # x_position, y_position, x_velocity, y_velocity
_y_clips=[-10000000,0], _ground_friction_coef=25,
_gravity_acceleration_coef=0.002, _calming_friction_coef=0.7,
_typical_friction_coef=0.8, _muscle_coef=0.08,
_traits_per_box=3, # desired width, desired height, rigidity
_traits_extra=1, # heartbeat (time)
mutation_size=0.05, big_mutation_size=0.1, mutation_rate=0.05, big_mutation_rate=0.1,
_UNITS_PER_METER=0.05, logger=logger)

# Cosmetic UI variables
ui = UI(_W_W=1920, _W_H=1078, _MOVIE_SINGLE_DIM=(650,650),
_GRAPH_COOR=(850,50,900,500), _SAC_COOR=(850,560,900,300), _GENEALOGY_COOR=(20,105,530,802,42),
_COLUMN_MARGIN=330, _MOSAIC_DIM=[10,24,24,30], #_MOSAIC_DIM=[10,10,17,22],
_MENU_TEXT_UP=180, _CM_MARGIN1=20, _CM_MARGIN2=1)

sim.ui = ui
ui.sim = sim
ui.addButtonsAndSliders()
    
sim.initializeUniverse()
while ui.running:
    sim.checkALAP()
    ui.detectMouseMotion()
    ui.detectEvents()
    ui.detectSliders()
    ui.doMovies()
    ui.drawMenu()
    ui.show()