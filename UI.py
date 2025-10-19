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

def getCoordsBetweenPoints(posData, i, timing, latest_telemetry, mapper):
    # keep all references to UI logic
    next_data_point_telemetry = posData.Date[i + 1]
    telemetry_delta = next_data_point_telemetry - latest_telemetry
    virtual_race_DT_now = timing.getRaceDTNow()
    t_delta_from_latest = virtual_race_DT_now - latest_telemetry
    t_ratio_to_next = t_delta_from_latest / telemetry_delta
    # print("t_ratio_to_next: ", t_ratio_to_next)
    X = posData.X[i]
    Y = posData.Y[i]
    # find vector of track movement till next telemetry pos point
    vX = posData.X[i + 1] - X
    vY = posData.Y[i + 1] - Y
    # we only want a fraction of the vector
    X_point = (vX * t_ratio_to_next) + X
    Y_point = (vY * t_ratio_to_next) + Y
    # map and apply vector to current point and draw it
    result_pos = mapper.getCoords(X_point.item(), Y_point.item())
    time.sleep(refreshRate)
    UIEvents.put(result_pos)

def main():
    # SETUP
    ver_pos_data = saveFiles.load_object("ver_pos_data.pkl") # TODO get different drivers telemetry
    mapper = PosMapper(ver_pos_data)
    pygame.init()
    screen = pygame.display.set_mode((screenSize, screenSize))
    pygame.display.set_caption("Live Timing")
    background = pygame.Surface(screen.get_size())
    drawing_layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)  # supports transparency
    timing = Timing(ver_pos_data.Date[0])
    t = None # thread

    running = True

    # TRACK MAP SETUP
    for i in range(ver_pos_data.__len__()):
        pos = mapper.getCoords(ver_pos_data.X[i].item(), ver_pos_data.Y[i].item())
        print(i, ". drawing", pos)
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

        if i < (ver_pos_data.__len__()):
            latest_telemetry = ver_pos_data.Date[i]
            # draw actual xy data point of track from telemetry
            if timing.isReady(latest_telemetry):
                # screen.blit(background, (0, 0))
                # drawing_layer.fill((0, 0, 0, .5))
                # pos = mapper.getCoords(ver_pos_data.X[i].item(), ver_pos_data.Y[i].item())
                # print("drawing", pos)
                # pygame.draw.circle(drawing_layer, (20, 200, 20), pos, 1)
                i = i + 1
            # draw points in between
            else:
                # fill in area between points (if thread available)
                if (t is None or not t.is_alive()):
                    t = threading.Thread(
                        target=getCoordsBetweenPoints,
                        args=(ver_pos_data, i, timing, latest_telemetry, mapper)
                    )
                    t.start()
        screen.blit(drawing_layer, (0, 0))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()