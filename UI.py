import threading
from datetime import datetime, timedelta
import time
from queue import Queue
from xmlrpc.client import DateTime
from threading import Thread
import pygame
import saveFiles
import queue
from logger import log_info, log_debug
from enum import Enum



screenSize = 500
padding = 25
UIEvents = queue.Queue()
refreshRate = 0.05
streamRate = 0.15

class Mediator:
    def __init__(self):
        self.Queue = queue.Queue()

    def publish(self, event):
        self.event_queue.put(event)

    def get_event(self):
        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return None

class ScreenLayer(Enum):
    TRACK_MAP = 1
    DRIVERS = 2

# will send telemetry to driver threads
class TelemetryController:
    def __init__(self, mediator):
        self.ver_pos_data = saveFiles.load_object("ver_pos_data.pkl")
        self.alo_pos_data = saveFiles.load_object("alo_pos_data.pkl")
        self.single_lap = saveFiles.load_object("single_lap.pkl")
        self.mapper = PosMapper(self.ver_pos_data)
        self.timing = Timing(self.ver_pos_data.Date[0])
        self.mediator = mediator
        self.driver_thread = DriverThread(self.timing, self.mapper, self.mediator)
        self.thread = threading.Thread(
            target=self.Run,
            args=()
        )

    def InitTrackMap(self):
        for i in range(self.single_lap.__len__()):
            pos = self.mapper.getCoords(self.single_lap.X[i].item(), self.single_lap.Y[i].item())
            # log_info(i, ". drawing", pos)
            UIEvents.put(UIDrawCommand(pos, (50, 50, 50, 0.5), 6, ScreenLayer.TRACK_MAP))
            i = i + 1

    def StartTelemetryStream(self):
        self.thread.start()

    def StartDriverThreads(self):
         self.driver_thread.StartThread()

    def Run(self):
        log_info("starting telemetry stream thread")
        for i in range(self.ver_pos_data.__len__()):
            time.sleep(streamRate)
            self.driver_thread.event_queue.put(PosData(self.ver_pos_data, i))


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

class UIDrawCommand:
    def __init__(self, posData, color, width, screenLayer):
        self.posData = posData
        self.color = color
        self.width = width
        self.screenLayer = screenLayer

# will contain all data for driver, going to be fed telemetry in a similar to real time basis
class DriverThread:
    def __init__(self, timing, mapper, mediator):
        log_info("creating driver thread")
        self.event_queue = queue.Queue()
        self.mapper = mapper
        self.timing = timing
        self.lock = threading.Semaphore(1)
        self.mediator = mediator
        self.t = threading.Thread(
            target=self.Run,
            args=()
        )

    def StartThread(self):
        self.t.start()

    def Run(self):
        log_info("starting DriverThread")
        while True:
            # CASE 1: not enough telemetry points
            if self.event_queue.qsize() < 2:
                # log_info("case 1 hit. qsize:", self.event_queue.qsize())
                continue

            # peek queue with semaphore
            with self.lock:
                eq = list(self.event_queue.queue)
                tel_1 = eq[0]
                tel_2 = eq[1]

            # CASE 2: first telemetry outdated
            if self.timing.isReady(tel_2.Date):
                log_info("case 2 hit")
                self.event_queue.get_nowait()
                continue

            telemetry_delta = tel_2.Date - tel_1.Date
            # log_info("\ntel_1.Date:", tel_1.Date)
            # log_info("tel_2.Date:", tel_2.Date)
            virtual_race_DT_now = self.timing.getRaceDTNow()
            # log_info("virtual_race_DT_now", virtual_race_DT_now)
            t_delta_from_latest = virtual_race_DT_now - tel_1.Date
            # log_info("t_delta_from_latest", t_delta_from_latest)

            # CASE 3: not ready
            if (t_delta_from_latest < timedelta(0)):
                # log_info("case 3 hit")
                continue

            log_info("sending tel data back to UI. qsize:", self.event_queue.qsize())
            t_ratio_to_next = t_delta_from_latest / telemetry_delta
            # log_info("t_ratio_to_next: ", t_ratio_to_next)
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
            UIEvents.put(UIDrawCommand(result_pos, (150, 0, 100), 3, ScreenLayer.DRIVERS))


def main():
    # SETUP UI
    pygame.init()
    screen = pygame.display.set_mode((screenSize, screenSize))
    pygame.display.set_caption("Live Timing")
    background = pygame.Surface(screen.get_size())
    drawing_layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)  # supports transparency
    # SETUP
    pos_mediator = Mediator()
    controller = TelemetryController(pos_mediator)
    controller.StartDriverThreads()
    controller.InitTrackMap()
    controller.StartTelemetryStream()


    running = True

    screen.blit(background, (0, 0))
    log_info("starting game loop")
    # UI/GAME LOOP
    i=0
    while running:
        screen.blit(background, (0, 0))
        # built in pygame event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # UI event handling
        try:
            command: UIDrawCommand = UIEvents.get_nowait()
            now = datetime.now()
            screen.blit(background, (0, 0))
            drawing_layer.fill((0, 0, 0, .5))
            log_info("processing command")
            if command.screenLayer == ScreenLayer.DRIVERS:
                log_info("drawing in between data points ", command.posData)
                pygame.draw.circle(drawing_layer, command.color, command.posData, command.width)
            elif command.screenLayer == ScreenLayer.TRACK_MAP:
                log_info("drawing track map data point ", command.posData)
                pygame.draw.circle(background, command.color, command.posData, command.width)
            else:
                log_info("invalid screen requested in command", command.posData, command.color, command.screenLayer)
        except:
            pass

        screen.blit(drawing_layer, (0, 0))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()