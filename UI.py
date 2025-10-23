import threading
from datetime import datetime, timedelta
import time
from queue import Queue
from xmlrpc.client import DateTime
from threading import Thread
import pygame
import saveFiles
import queue


screenSize = 500
padding = 25
UIEvents = queue.Queue()
refreshRate = 0.01

# # will send telemetry to driver threads
# class TelemetryController:
#     def __init__(self):
#

class PosData:
    def __init__(self, posData, i):
        self.X = posData.X[i]
        self.Y = posData.Y[i]
        self.Date = posData.Date[i]

class PosMapper:
    def __init__(self, pos_data):
        self.minx = min(pos_data.X)
        self.maxx = max(pos_data.X)
        self.miny = min(pos_data.Y)
        self.maxy = max(pos_data.Y)

        self.UIRange = screenSize - padding * 2

        self.dataRangeX = self.maxx - self.minx
        self.dataRangeY = self.maxy - self.miny
        self.rangeFactorX = self.UIRange / self.dataRangeX
        self.rangeFactorY = self.UIRange / self.dataRangeY

        # normalize
        self.offsetX = -1 * self.minx
        self.offsetY = -1 * self.miny

    def getCoords(self, X,Y):
        vx = (X + self.offsetX) * self.rangeFactorX + padding
        vy = (Y + self.offsetY) * self.rangeFactorY + padding
        return (vx, vy)

class Timing:
    # when starting timing,
    def __init__(self, raceStartDT):
        self.startTime = datetime.now()
        self.dateOffset = self.startTime - raceStartDT

    def isReady(self, curTelemetryDT):
        if self.getRaceDTNow() > curTelemetryDT:
            return True
        else: return False

    # get our current point in time in the race
    def getRaceDTNow(self):
        return datetime.now() - self.dateOffset

# will contain all data for driver, going to be fed telemetry in a similar to real time basis
class DriverThread:
    def __init__(self, timing, mapper):
        print("creating driver thread")
        self.event_queue = queue.Queue() # contains Date,X,Y
        self.mapper = mapper
        self.timing = timing
        self.lock = threading.Semaphore(1)

    def Start(self):
        print("starting DriverThread")
        while True:
        # for k in range(1000):
            # CASE 1: not enough telemetry points
            if self.event_queue.qsize() < 2:
                # print("case 1 hit. qsize:", self.event_queue.qsize())
                continue

            with self.lock:
                eq = list(self.event_queue.queue)
                tel_1 = eq[0]
                tel_2 = eq[1]

            # CASE 2: first telemetry outdated
            if self.timing.isReady(tel_2.Date):
                print("case 2 hit")
                self.event_queue.get_nowait()
                continue

            telemetry_delta = tel_2.Date - tel_1.Date
            virtual_race_DT_now = self.timing.getRaceDTNow()
            t_delta_from_latest = virtual_race_DT_now - tel_1.Date

            # CASE 3: not ready
            if (t_delta_from_latest < timedelta(0)):
                print("case 3 hit")
                continue

            self.event_queue.get_nowait()
            print("sending tel data back to UI. qsize:", self.event_queue.qsize())
            t_ratio_to_next = t_delta_from_latest / telemetry_delta
            # print("t_ratio_to_next: ", t_ratio_to_next)
            X = tel_1.X
            Y = tel_1.Y
            # find vector of track movement till next telemetry pos point
            vX = tel_2.X - X
            vY = tel_2.Y - Y
            # we only want a fraction of the vector
            X_point = (vX * t_ratio_to_next) + X
            Y_point = (vY * t_ratio_to_next) + Y
            # map and apply vector to current point and draw it
            result_pos = self.mapper.getCoords(X_point.item(), Y_point.item())
            time.sleep(refreshRate)
            UIEvents.put(result_pos)


def main():
    # SETUP
    ver_pos_data = saveFiles.load_object("ver_pos_data.pkl")
    alo_pos_data = saveFiles.load_object("alo_pos_data.pkl")
    mapper = PosMapper(ver_pos_data)
    pygame.init()
    screen = pygame.display.set_mode((screenSize, screenSize))
    pygame.display.set_caption("Live Timing")
    background = pygame.Surface(screen.get_size())
    drawing_layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)  # supports transparency
    timing = Timing(ver_pos_data.Date[0])


    thread_ver = DriverThread(timing, mapper)
    t = threading.Thread(
        target=thread_ver.Start,
        args=()
    )
    t.start()
    time.sleep(0.1)
    thread_ver.event_queue.put(PosData(ver_pos_data, 0))
    time.sleep(0.1)
    thread_ver.event_queue.put(PosData(ver_pos_data, 1))
    time.sleep(0.1)
    thread_ver.event_queue.put(PosData(ver_pos_data, 2))
    print("added 3 events in driver thread")

    running = True

    # TRACK MAP SETUP
    for i in range(ver_pos_data.__len__()):
        pos = mapper.getCoords(ver_pos_data.X[i].item(), ver_pos_data.Y[i].item())
        # print(i, ". drawing", pos)
        pygame.draw.circle(background, (50, 50, 50, 0.5), pos, 6)
        i = i + 1
    screen.blit(background, (0, 0))

    # UI/GAME LOOP
    i=0
    while running:
        # built in pygame event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # UI event handling
        try:
            newPos = UIEvents.get_nowait()
            now = datetime.now()
            print("drawing in between data points ", now.second, now.microsecond, newPos)
            screen.blit(background, (0, 0))
            drawing_layer.fill((0, 0, 0, .5))
            # TODO diff color depending on driver
            pygame.draw.circle(drawing_layer, (150, 0, 100), newPos, 1)
        except:
            pass

        # # TODO this might go, do a separate thread that spits telemetry data every quarter second or so
        # if i < (ver_pos_data.__len__()):
        #     latest_telemetry = ver_pos_data.Date[i]
        #     # once next point is ready we increment to next telemetry
        #     if timing.isReady(latest_telemetry):
        #         i = i + 1
        #     # draw points in between
        #     else:
        #         # fill in area between points (if thread available)
        #         if (t is None or not t.is_alive()):
        #             t = threading.Thread(
        #                 target=getCoordsBetweenPoints,
        #                 args=(ver_pos_data, i, timing, latest_telemetry, mapper)
        #             )
        #             t.start()
        screen.blit(drawing_layer, (0, 0))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()