# python 3.13
# compare records of laptimes to current practice session
# -> see who might have the edge
# -> get insights on track evolution
# compare progression of practice sessions for drivers
# -> get insight on which one of the
# .. two papaya cars might have an edge early in the weekend
# find "virtual leader" (some haven't pitted yet)
# practice laptimes vs fuel load
# let's say two rivals are behind a lead car.
# .. If the lead car is slower it's going to sqeeze the rivals closer together
# .. potentially predict the outcome
# pitstop speed comparison (remember mclaren 2025)


--------------
UNIT TEST PLANS
--------------
fill driverThread with telemetry verify telemetry is in order

---------------------
freewriting/problems/ideas
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

so do we do the timing in the main thread?
    - decide timing in main thread
    - telemetry must be in order
    - each driver thread loops through event queue
        - get current and next telemetry that isn't ready
    - if we get the telemetry data together for all drivers through some 
    live api, we can always split that up.
    - create driverThread objects 
    - start threads before game loop starts





