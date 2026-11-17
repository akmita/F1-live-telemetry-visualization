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
refreshRate = 0.05
streamRate = 0.15


class Mediator:
    def __init__(self):
        self.Queue = queue.Queue()

    def publish(self, event):
        self.Queue.put(event)

    def get_event(self):
        try:
            return self.Queue.get_nowait()
        except queue.Empty:
            return None

class ScreenLayer(Enum):
    TRACK_MAP = "TRACK_MAP"
    class drivers(Enum):
        VER = "VER"
        ALO = "ALO"

class Driver:
    def __init__(self, driver_name, driver_thread, driver_data):
        self.driver_name = driver_name
        self.driver_thread : DriverThread = driver_thread
        self.driver_data = driver_data
        self.index = 0

    def StartThread(self):
        self.driver_thread.StartThread()

    def SendTelemetry(self):
        if self.index < self.driver_data.__len__() - 1:
            log_info("SendTelemetry to driver: " + self.driver_name, ". index: ", str(self.index), ". Qsize", self.driver_thread.event_queue.qsize())
            self.driver_thread.event_queue.put(PosData(self.driver_data, self.index))
            self.index += 1
        else:
            log_info("telemetry done for: ", self.driver_name)

class Drivers:
    def __init__(self, mapper, mediator):
        self.drivers : dict [str,Driver] = {}
        self.mapper = mapper
        self.mediator = mediator

    def LoadDriversData(self):
        pos_data = saveFiles.load_object("ver_pos_data.pkl")
        self.timing = Timing(pos_data.Date[0])
        # TODO fix this is terrible
        self.drivers["VER"] = Driver("VER", DriverThread(self.timing, self.mapper, self.mediator, ScreenLayer.drivers.VER), pos_data)
        self.drivers["ALO"] = Driver("ALO", DriverThread(self.timing, self.mapper, self.mediator, ScreenLayer.drivers.ALO), saveFiles.load_object("alo_pos_data.pkl"))

    def StartDriverThreads(self):
        self.drivers['VER'].StartThread()
        self.drivers['ALO'].StartThread()

    def SendTelemetryToAll(self):
        self.drivers['VER'].SendTelemetry()
        self.drivers['ALO'].SendTelemetry()


# will send telemetry to driver threads
class TelemetryController:
    def __init__(self, mediator):
        self.single_lap = saveFiles.load_object("single_lap.pkl")
        # initialize mapper and timing with first driver's data
        self.mapper = PosMapper(self.single_lap)
        self.mediator = mediator
        # telemetry streamer thread
        self.thread = threading.Thread(
            target=self.Run,
            args=()
        )
        self.drivers_container = Drivers(self.mapper, self.mediator)
        self.drivers_container.LoadDriversData()

    def InitTrackMap(self):
        for x, y in zip(self.single_lap.X, self.single_lap.Y):
            pos = self.mapper.getCoords(x, y)
            self.mediator.publish(UIDrawCommand(pos, (50, 50, 50, 0.5), 6, ScreenLayer.TRACK_MAP))

    def StartTelemetryStream(self):
        self.thread.start()

    def StartDriverThreads(self):
       self.drivers_container.StartDriverThreads()

    def Run(self):
        while True:
            self.drivers_container.SendTelemetryToAll()
            time.sleep(streamRate)

# gets element at x,y,timestamp of posData from fastf1 api object
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
        # log_info("virtualDT: ", self.getRaceDTNow(), " telDT:", curTelemetryDT)
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
    def __init__(self, timing, mapper, mediator, driver_name):
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
        self.driver_name = driver_name

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
            self.mediator.publish(UIDrawCommand(result_pos, (150, 0, 100), 3, self.driver_name))

# runs on main thread, controls UI
class UIController:
    def __init__(self, mediator):
        # SETUP UI
        pygame.init()
        self.screen = pygame.display.set_mode((screenSize, screenSize))
        pygame.display.set_caption("Live Timing")
        # UI layers
        self.background = pygame.Surface(self.screen.get_size())
        self.layer_1 = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)  # supports transparency
        self.layer_2 = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)  # supports transparency
        self.running = False
        self.mediator = mediator

    def Start(self):
        self.running = True
        self.Run()

    def Run(self):
        log_info("starting game loop")
        self.screen.blit(self.background, (0, 0))
        i = 0
        while self.running:
            self.screen.blit(self.background, (0, 0))
            # built in pygame event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # UI event handling
            command : UIDrawCommand = self.mediator.get_event()
            if command is None:
                continue

            self.screen.blit(self.background, (0, 0))

            if command.screenLayer == ScreenLayer.drivers.VER:
                self.layer_1.fill((0, 0, 0, .5))
                log_info("drawing in between data points ", command.posData)
                pygame.draw.circle(self.layer_1, command.color, command.posData, command.width)
            elif command.screenLayer == ScreenLayer.drivers.ALO:
                self.layer_2.fill((0, 0, 0, .5))
                log_info("drawing in between data points ", command.posData)
                pygame.draw.circle(self.layer_2, command.color, command.posData, command.width)
            elif command.screenLayer == ScreenLayer.TRACK_MAP:
                log_info("drawing track map data point ", command.posData)
                pygame.draw.circle(self.background, command.color, command.posData, command.width)
            else:
                log_info("invalid screen requested in command", command.posData, command.color, command.screenLayer)

            self.screen.blit(self.layer_1, (0, 0))
            self.screen.blit(self.layer_2, (0, 0))
            pygame.display.flip()

        log_info("ending game loop")
        pygame.quit()



# -----------
# ENTRY POINT
# -----------
def main():
    # SETUP
    pos_mediator = Mediator()
    controller = TelemetryController(pos_mediator)
    controller.StartDriverThreads()
    controller.InitTrackMap()
    controller.StartTelemetryStream()
    UI = UIController(pos_mediator)
    # UI will block and take over the main thread from here
    UI.Start()

if __name__ == "__main__":
    main()
