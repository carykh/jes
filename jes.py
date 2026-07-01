from jes_sim import Sim
from jes_ui import UI

c_input = input(
    "How many creatures do you want?\n100: Lightweight\n250: Standard (if you don't type anything, I'll go with this)\n500: Strenuous (this is what my carykh video used)\n"
)
if c_input == "":
    c_input = "250"

# Simulation
# population size is 250 here, because that runs faster. You can increase it to 500 to replicate what was in my video, but do that at your own risk!

sim = Sim(
    _c_count=int(c_input),
    _stabilization_time=200,
    _trial_time=300,
    _beat_time=20,
    _beat_fade_time=5,
    _c_dim=[4, 4],
    _beats_per_cycle=3,
    _node_coor_count=4,  # x_position, y_position, x_velocity, y_velocity
    _y_clips=[-10000000, 0],
    _ground_friction_coef=25,
    _gravity_acceleration_coef=0.002,
    _calming_friction_coef=0.7,
    _typical_friction_coef=0.8,
    _muscle_coef=0.08,
    _traits_per_box=3,  # desired width, desired height, rigidity
    _traits_extra=1,  # heartbeat (time)
    _mutation_rate=0.07,
    _big_mutation_rate=0.025,
    _UNITS_PER_METER=0.05,
)

# Cosmetic UI variables
ui = UI(
    _W_W=1700,
    _W_H=900,
    _MOVIE_SINGLE_DIM=(650, 650),
    _GRAPH_COOR=(850, 50, 900, 500),
    _SAC_COOR=(850, 560, 900, 300),
    _GENEALOGY_COOR=(20, 105, 530, 802, 42),
    _COLUMN_MARGIN=330,
    _MOSAIC_DIM=[10, 24, 24, 30],  # _MOSAIC_DIM=[10,10,17,22],
    _MENU_TEXT_UP=180,
    _CM_MARGIN1=20,
    _CM_MARGIN2=1,
)

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
