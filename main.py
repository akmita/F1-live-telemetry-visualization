import seaborn as sns
from matplotlib import pyplot as plt

import fastf1
import fastf1.plotting


session = fastf1.get_session(2021, 'Spanish Grand Prix', 'Q')
session.load()

ver_lap = session.laps.pick_drivers('VER').pick_fastest()

ver_pos_data = ver_lap.get_pos_data()


# compare records of laptimes to current practice session
# -> see who might have the edge
# -> get insights on track evolution
# compare progression of practice sessions for drivers
# -> get insight on which one of the
# .. two papaya cars might have an edge early in the weekend
# find "virtual leader" (some haven't pitted yet)
# practice laptimes vs fuel load