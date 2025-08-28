#!/usr/bin/env python
# coding: utf-8

# # Extract active vehicles
# 1. Convenience functions for date processing
# 2. fetch trip_updates
# 3. Process trip_updates
# 4. Enrich stop_times with real-time trip_updates
# 5. add realtime start and end times to trips
# 6. Get trips that are currently active
# 7. Get status of the active trips
# 8. Transform status to LED matrix
# 
# runs every minute

# In[1]:


import pandas as pd
from os import path, getcwd

gtfs_filtered_path = path.join(getcwd(), 'gtfs_filtered')
calendar_path = path.join(gtfs_filtered_path, 'calendar.txt')
routes_path = path.join(gtfs_filtered_path, 'routes.txt')
trips_path = path.join(gtfs_filtered_path, 'trips.txt')
stops_path = path.join(gtfs_filtered_path, 'stops.txt')
stop_times_path = path.join(gtfs_filtered_path, 'stop_times.txt')

calendar:pd.DataFrame = pd.read_csv(calendar_path)
routes:pd.DataFrame = pd.read_csv(routes_path)
trips:pd.DataFrame = pd.read_csv(trips_path)
stops:pd.DataFrame = pd.read_csv(stops_path)
stop_times:pd.DataFrame = pd.read_csv(stop_times_path)


relevant_lines = ['22', '26', '5', '23', '21', '24']
relevant_trip_prefixes = [line + "-" for line in relevant_lines]


# ## Convenience functions for gtfs date formats

# In[2]:


import datetime

def parseGtfsTimestringAsTimeObject(timestring:str):
    # mod 24, because gtfs defines days as service days that can be longer than 24 hours, so 24:15 is a valid gtfs time
    hour = int(timestring[0:2]) % 24
    minute = int(timestring[3:5])
    second = int(timestring[6:8])
    return datetime.time(hour, minute, second)

def parseGtfsDatestringAsDateObject(datestring:str):
    datestring = str(datestring)
    year = int(datestring[0:4])
    month = int(datestring[4:6])
    day = int(datestring[6:8])
    return datetime.date(year, month, day)

def addSecondsToTimeObject(time:datetime.time, seconds) -> datetime.time:
    datetime_object = datetime.datetime(100,1,1,time.hour, time.minute, time.second)
    delta = datetime.timedelta(seconds=seconds)
    return (datetime_object + delta).time()


def getGtfsWeekdayFromDate(date: datetime.date):
    weekday_number = date.weekday()
    if weekday_number == 0:
        return "monday"
    elif weekday_number == 1:
        return "tuesday"
    elif weekday_number == 2:
        return "wednesday"
    elif weekday_number == 3:
        return "thursday"
    elif weekday_number == 4:
        return "friday"
    elif weekday_number == 5:
        return "saturday"
    else:
        return "sunday"


# ## Filter trips that are running at the current time +- 10 minutes

# In[3]:


current_datetime = datetime.datetime.now()

# !! if stop time updates are reintroduced, the buffer might be better set to + 30 minutes in case of delays

# train is potentially running if
# 1. the current time is before the scheduled start - 10 minutes (to allow for potential depot animations)
# 2. the current time is before the scheduled end + 10 minutes (to allow for potential depot animation etc.)
def isPotentiallyRunningAtCurrentTime(start_gtfs_timestring, end_gtfs_timestring, current_datetime):
    starttime = parseGtfsTimestringAsTimeObject(start_gtfs_timestring)
    endtime = parseGtfsTimestringAsTimeObject(end_gtfs_timestring)

    # make a datetime with the current date, because the selected trips are scheduled for today
    # if we use time instead of datetime, no trips after 00:00 - delay_buffer can be shown
    startdatetime = datetime.datetime.combine(datetime.date.today(), starttime)
    enddatetime = datetime.datetime.combine(datetime.date.today(), endtime)

    startdatetime_with_buffer = startdatetime - datetime.timedelta(minutes=10)
    enddatetime_with_buffer = enddatetime + datetime.timedelta(minutes=10)

    return startdatetime_with_buffer <= current_datetime <= enddatetime_with_buffer
    

# select only trips that are running right now
trips = trips.loc[trips.apply(lambda row: isPotentiallyRunningAtCurrentTime(row['start_time'], row['end_time'], current_datetime), axis=1)]
stop_times = stop_times.loc[stop_times['trip_id'].map(lambda trip_id: trip_id in trips.loc[:,'trip_id'].values)]

print(trips.head(5))
print(stop_times.head(5))


# # OPTIONAL IMPROVEMENT: INSERT APPLYING STOPTIMEUPDATES HERE

# ## currently active trips

# First, we need to get all the trip_ids for currently active trips. Trips are active, if the current time is between the start and end time of the trip and if one of the services, the trip belongs to, runs on the current day.
# Let's start by looking at the start and end times of the trips.

# In[4]:


print(datetime.datetime.now())

def isTripRowActiveAtCurrentTime(trip_row):
    start_time = parseGtfsTimestringAsTimeObject(trip_row['start_time'])
    current_time = datetime.datetime.now().time() 
    end_time = parseGtfsTimestringAsTimeObject(trip_row['end_time'])
    return start_time <= current_time <= end_time
    

# select trips where current time is between start and end time
trips = trips[trips.apply(isTripRowActiveAtCurrentTime, axis=1)]
print("found", trips.shape[0], "trips that run at the current time")
print(trips.head(5))


# Secondly, we will check whether the services run on the current day by looking up the services from the `service_id` column in the calendar dataframe.
# As soon as we find a `service_id` that runs on the current day, we can stop the search and return true, otherwise we return false.

# In[5]:


def isTripRowActiveOnCurrentDay(trip_row):
    current_date = datetime.date.today()
    current_weekday_gtfs = getGtfsWeekdayFromDate(datetime.date.today())
    
    calendar:pd.DataFrame = pd.read_csv(calendar_path)

    # select row from calendar for this service
    calendar = calendar[calendar['service_id'] == trip_row['service_id']]

    # check every calendar entry
    for index, schedule in calendar.iterrows():
        # check if current date is between start_date and end_date (inclusive)
        start_date = parseGtfsDatestringAsDateObject(schedule['start_date'])
        end_date = parseGtfsDatestringAsDateObject(schedule['end_date'])

        duration_check = start_date <= current_date <= end_date

        # check if current weekday is an active day in the schedule
        weekday_check = schedule[current_weekday_gtfs] == 1

        if duration_check and weekday_check:
            return True
                
    return False
    
trips = trips[trips.apply(isTripRowActiveOnCurrentDay, axis=1)]
print(trips.head(5))


# ## Compute animationcodes
# Now that we have identified all the trips that are currently running, we want to know where the trams are on our network. For later animation, we want to save the information, between which two station a tram is. We also want to know the primary color (RNV_route_color) as well as the secondary color used for the trail (dimmed primary color). 
# 
# To later distinguish between RNV and DB trains, the animationcode has the following pattern
# 
# RNV:{previous_stop_id}_{next_stop_id}:{primary_color}_{secondary_color}
# 
# 

# First, let's define some functions:

# In[6]:


import pandas as pd

# create status Dataframe for every active trip, then merge the Dataframes
# status, current_stop_id, previous_stop_id


current_time = datetime.datetime.now().time()

# take stop times and iterator to check previous stop
# check if the stop_time at position i of stop_times is currently being traveled to or already reached (i.e. train is between the signal of departure stop A and departure stop B)
def isTravelingToOrStoppingAtStoptime(stop_times, i):
    # loc because i is the pandas index of the row 
    this_stop_time = stop_times.loc[i]

    # if there is no previous stop_time, this is the initial station which cannot be traveled to 
    try:
        # i-1 is okay here, because the df is sorted 
        previous_stop_time = stop_times.loc[i-1]
    except KeyError:
        return False
    has_not_departed_this_stop_time = current_time < parseGtfsTimestringAsTimeObject(this_stop_time['departure_time'])
    has_departed_previous_stop_time = current_time >= parseGtfsTimestringAsTimeObject(previous_stop_time['departure_time'])
    return has_not_departed_this_stop_time and has_departed_previous_stop_time

def getPreviousStopId(stop_times, current_stop_time):
    trip_id = current_stop_time['trip_id']
    
    current_stop_sequence = current_stop_time['stop_sequence']
        
    previous_stop_sequence = current_stop_sequence - 1
    
    previous_stop_times = stop_times.loc[(stop_times['trip_id'] == trip_id) & (stop_times['stop_sequence'] == previous_stop_sequence)].reset_index(drop=True)
    
    if len(previous_stop_times) == 0:
         # if previous stop does not exist, train is coming from depot
        return 'DEPOT'

    previous_stop_time = previous_stop_times.iloc[0]

    return previous_stop_time['stop_id']


def getStopName(stops, stop_id):
    if stop_id == 'DEPOT':
        return 'DEPOT'
   # should be 1 or 0
    applicable_stops = stops.loc[stops['stop_id'] == stop_id]
    if len(applicable_stops) == 0:
        # stop not found
        return 'ERROR'
    else:
        applicable_stop = applicable_stops.iloc[0]
        return f"{applicable_stop['stop_name']} (Steig {applicable_stop['platform_code']})"
    
    
def dim_hex_color(hex_color, factor):
    # HEX -> RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Dimmen und sicherstellen, dass der Wert im Bereich [0, 255] bleibt
    r = int(max(0, min(255, r * factor)))
    g = int(max(0, min(255, g * factor)))
    b = int(max(0, min(255, b * factor)))

    # RGB -> HEX
    return "{:02X}{:02X}{:02X}".format(r, g, b)


def get_route_color(route_id:str):
    if route_id.startswith("5"):
        return "01FF5A"
    if route_id.startswith("21"):
        return 'FF0011'  
    if route_id.startswith("22"):
        return 'FFCC00'  
    if route_id.startswith("23"):
        return "FF9900"   
    if route_id.startswith("24"):
        return 'FF3BD5'   
    if route_id.startswith("26"):
        return "FE7F7F"   
    return 'FFFFFF'
    
    

status_df = pd.DataFrame()

for i, active_trip in trips.iterrows():
    trip_id = active_trip['trip_id']

    stop_times_for_this_trip = stop_times.loc[stop_times['trip_id'] == trip_id]

    # find stops that the vehicle is currently traveling to (should be 0 or 1)
    # vehicle is traveling to a stop if it has not arrived a stop but already departed the previous stop
    stop_times_traveling_to = [stop_time for i ,stop_time in stop_times_for_this_trip.iterrows() if isTravelingToOrStoppingAtStoptime(stop_times_for_this_trip, i)]

    #print(trip_id, len(stop_times_stopped_at), len(stop_times_traveling_to))

    status = ''
    previous_stop_id = ''
    next_stop_id = ''
    previous_stop_name=''
    animationcode = ''

        
    if len(stop_times_traveling_to) > 0:
        status = 'IN_TRANSIT_TO'
        next_stop_time = stop_times_traveling_to[0]

        previous_stop_id = getPreviousStopId(stop_times, next_stop_time)
        next_stop_id = next_stop_time['stop_id']
        
        previous_stop_name = getStopName(stops, previous_stop_id)
        next_stop_name = getStopName(stops, next_stop_id)
        
        
        route_id = active_trip['route_id']
        route_color = get_route_color(route_id)
        primary_color = dim_hex_color(route_color, 1.0)
        secondary_color = dim_hex_color(primary_color, 0.4)
        
        # for the animationcode the last two digits are cut off as they only specify the platform, which is irrelevant for animation.
        
        animationcode = f"RNV:{str(previous_stop_id)[:-2]}_{str(next_stop_id)[:-2]}:{primary_color}_{secondary_color}" 
    else: 
        status = 'ERROR'

        
    
    status_df_row = pd.DataFrame({'trip_id': trip_id,'status': [status], 
                  'previous_stop_id': [previous_stop_id], 
                  'next_stop_id': [next_stop_id],
                  'previous_stop_name': [previous_stop_name], 'animationcode':animationcode})

    
    status_df = pd.concat([status_df, status_df_row], ignore_index=True)

print(status_df)


# In[7]:


# save to disk

status_df['animationcode'].to_csv('rnv_animationcodes.csv', index=False)


# In[ ]:




