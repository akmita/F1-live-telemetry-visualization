# file only used to load data for UI.py

import seaborn as sns
from matplotlib import pyplot as plt

import fastf1
import fastf1.plotting


session = fastf1.get_session(2021, 'Spanish Grand Prix', 'Q')
session.load()

ver_laps = session.laps.pick_drivers('VER')

ver_lap = ver_laps.pick_fastest()

ver_pos_data = ver_lap.get_pos_data()


