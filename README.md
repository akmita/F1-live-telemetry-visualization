python 3.13
-----------------
IDEAS / FEATURES
-----------------
compare records of laptimes to current practice session
-> see who might have the edge
-> get insights on track evolution
compare progression of practice sessions for drivers
-> get insight on which one of the
.. two papaya cars might have an edge early in the weekend
find "virtual leader" (some haven't pitted yet)
practice laptimes vs fuel load
let's say two rivals are behind a lead car.
.. If the lead car is slower it's going to sqeeze the rivals closer together
.. potentially predict the outcome
pitstop speed comparison 
"watch" driver gaps, notification when driver gets past a threshhold 
auto mark and track drivers who are managing tires 
.. compare to pace in practice or previous laps, maybe just mark
.. any ones that are off pace, which ones are faster
distance from each driver visualization like a connect drivers to
.. dots on the right in a line representing relative distance
distance from 

--------------
UNIT TEST PLANS
--------------
fill driverThread with telemetry verify telemetry is in order


--------------
REFACTOR TODO
--------------
decouple driverThread-UIeventQueue with mediator pattern - [X]
main should be a class, called UIController - [X]
decouple posMapper from TelemetryController - 
are we violating the dependency inversion principle with 
 TelemetryController depending on driverThreads
 also violating single responsibility
 


--------------------------
freewriting/problems/ideas
--------------------------
try to switch to using threadpool later
position class relies on pos data, but WHICH driver? any one will work?
-- actually we can reuse it
can we reuse Timing class between drivers? it considers the 
race start to be the first telemetry point of an arbitrary driver. 
I'm sure the F1 data has race start time (lights out)
do we do a separate thread for a different driver? makes sense right?
and lap data goign by index is not going to suffice
if we could gather all the drivers telemetry, 
insert all into one array and sort by time with each insert.. binary search? 
well no, they should be within one point of each other
but we can't predict the path based on the next driver though.
so what makes the most sense is to do the "isReady" calculation 
in each threa. we're sending the massive sorted telemetry array to each 
thread.
but how does the live timing actually work? it would help working
with the actual live api to see how that data is structured
##### timing refactor 
so do we do the timing in the main thread?
    - decide timing in main thread
    - telemetry must be in order
    - each driver thread loops through event queue
        - get current and next telemetry that isn't ready
    - if we get the telemetry data together for all drivers through some 
    live api, we can always split that up.
    - create driverThread objects 
    - start threads before game loop starts
##### decoupling UI and drivers
so should the telemetryController house the driverthreads?
we're going to include speed/gas pedal/braking
if we proceed with the refactor, we will be passing the mediator object 
thorugh the constructor, it'll be a little clunky
we could just create the drivers on the main thread, just read
from driver config file? 
do we want to keep drivers and stream coupled? 
the UI for sure needs decoupling, but the former probably doesn't need it
the stream controller class will be sending out pedal/controls data too



