# file only used to load data for UI.py


import fastf1
import fastf1.plotting

import saveFiles

session = fastf1.get_session(2021, 'Spanish Grand Prix', 'R')
session.load()

ver_laps = session.laps.pick_drivers('VER')
alo_laps = session.laps.pick_drivers('ALO')

single_lap = ver_laps.pick_fastest()


ver_pos_data = ver_laps.get_pos_data()
alo_pos_data = alo_laps.get_pos_data()

saveFiles.save_object(single_lap.telemetry, 'single_lap.pkl')
saveFiles.save_object(ver_pos_data, "ver_pos_data.pkl")
saveFiles.save_object(alo_pos_data, "alo_pos_data.pkl")





