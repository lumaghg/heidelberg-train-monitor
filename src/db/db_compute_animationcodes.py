#!/usr/bin/env python
# coding: utf-8

# # Compute animationcodes of DB Trips
# 
# - load timetable from disk
# - optionally apply realtime updates
# - compute arrival and departure direction
# - compute statuscodes
# 
# runs every 30 seconds
# (in cron, register one job to run every minute and the other as well, but with 30s sleep at first)
# 
# ## convenience functions

# In[ ]:


# settings
TICK_LENGTH_SECONDS = 15
SECONDARY_COLOR_DIM_FACTOR = 0.4


# In[2]:


# chatgpt generiert lol
import datetime
def dateToDBDate(date: datetime.date) -> str:
    """
    Wandelt ein datetime.date Objekt in einen DB-Date-String "YYMMDD" um.
    """
    return date.strftime("%y%m%d")


def datetimeToDBDatetime(dt: datetime.datetime) -> str:
    """
    Wandelt ein datetime.datetime Objekt in einen DB-Datetime-String "YYMMDDHHMM" um.
    """
    return dt.strftime("%y%m%d%H%M")


def DBDatetimeToDatetime(dbDate: str) -> datetime.datetime:
    """
    Wandelt einen DB-Datetime-String "YYMMDDHHMM" in ein datetime.datetime Objekt um.
    """
    return datetime.datetime.strptime(dbDate, "%y%m%d%H%M")


def DBDateToDate(dbDate: str) -> datetime.date:
    """
    Wandelt einen DB-Date-String "YYMMDD" in ein datetime.date Objekt um.
    """
    return datetime.datetime.strptime(dbDate, "%y%m%d").date()
    
       
print(dateToDBDate(datetime.date(2025, 8, 10)))
print(datetimeToDBDatetime(datetime.datetime(2025, 8, 10, 12, 22)))
print(DBDateToDate("250810"))
print(DBDatetimeToDatetime("2508101222"))


# ## load timetable from disk

# In[3]:


import pandas as pd

df_timetable = pd.read_csv('db_timetable.csv', dtype=str)


print(df_timetable.head(5))


# # OPTIONAL IMPROVEMENT: APPLY REALTIME UPDATES HERE

# ## add artificial departure / arrival times
# if a trip starts/ends in Heidelberg Hbf, the arrival / departure properties are missing. To allow correct animation and not make the train spawn somewhere on the tracks, it is assumed that trains stand 1 minute in the station before departuring / after arriving. Therefore, one minute of standing time is artificially added to rows that don't have an arrival / departure.

# In[4]:


import datetime

def fillEmptyArrivals(timetable_row):
    if pd.isna(timetable_row['arrival_dbdatetime']):
        departure_datetime = DBDatetimeToDatetime(timetable_row['departure_dbdatetime'])
        artificial_arrival_datetime = departure_datetime - datetime.timedelta(minutes=1)
        timetable_row['arrival_dbdatetime'] = datetimeToDBDatetime(artificial_arrival_datetime)
    return timetable_row

def fillEmptyDepartures(timetable_row):
    if pd.isna(timetable_row['departure_dbdatetime']):
        arrival_datetime = DBDatetimeToDatetime(timetable_row['arrival_dbdatetime'])
        artificial_departure_datetime = arrival_datetime + datetime.timedelta(minutes=1)
        timetable_row['departure_dbdatetime'] = datetimeToDBDatetime(artificial_departure_datetime)
    return timetable_row
        
df_timetable = df_timetable.apply(func=fillEmptyArrivals, axis=1)
df_timetable = df_timetable.apply(func=fillEmptyDepartures, axis=1)

print(df_timetable.head(5))
        
        


# ## compute arrival / departure direction
# next, we want to compute the direction, from which a train is coming / to which a train is departuring. In the current model there are 4 possible directions that will be identified as north, south, west and east depending on which stations the respective planned path contains. There a multiple marker stations that are searched for in the path to determine the direction.
# 

# In[5]:


north_marker_stations = ['Neu-Edingen/Friedrichsfeld', 'Weinheim(Bergstr)Hbf', 'Bensheim', 'Darmstadt Hbf'] # RB68, FV nach Darmstadt
east_marker_stations = ['Heidelberg-Altstadt', 'Neckargemünd', 'Eberbach', 'Meckesheim'] # S1, S2, S5, S51, RE10a, RE10b
south_marker_stations = ['Wiesloch-Walldorf', 'Bruchsal', 'Karlsruhe Hbf', 'Vaihingen(Enz)','Stuttgart Hbf', 'Esslingen(Neckar)', 'Ulm Hbf'] # S3, S4, RE71, RE73, FV nach Karlsruhe, Stuttgart, Ulm 
west_marker_stations = ['Mannheim Hbf', 'Ludwigshafen(Rhein) Mitte','Ludwigshafen(Rh)Hbf'] # S1, S2, S3, S4, RE10a, RE10b, FV über Mannheim nach Wiesbaden / Mainz / Frankfurt 




def compute_path_direction(path: str):
    # check if path contains any of the marker stations
    if pd.isna(path):
        return "DEPOT"
    if any(station in path for station in north_marker_stations):
        return "north"
    if any(station in path for station in east_marker_stations):
        return "east"
    if any(station in path for station in west_marker_stations):
        return "west"
    if any(station in path for station in south_marker_stations):
        return "south"
 
   
df_timetable['arrival_direction'] = df_timetable['arrival_path'].map(compute_path_direction)
#df_timetable = df_timetable.drop('arrival_path', axis=1)

df_timetable['departure_direction'] = df_timetable['departure_path'].map(compute_path_direction)
#df_timetable = df_timetable.drop('departure_path', axis=1)



# ## compute animation class
# trips are classified into two animation classes, depending on which station stops have to be animated and which train length is animated.  
# Class SNV (S-Bahn und Nahverkehr): S, RB - stop at Hbf, Kirchheim/Rohrbach, Weststadt/Südstadt, Pfaffengrund/Wieblingen, Neu-Edingen/Friedrichsfeld  
# Class RFV (Regional- und Fernverkehr): everything else (RE, FLX, IC, ICE, NJ, RJ, RJX, TGV) - only stop at Hbf   
# 
# The class will be included in the statuscode
# each class gets their own statuscode_led_mapping, so that the statuscode can be computed in ticks after / before HD Hbf, and depending on the class the statuscodes mean different positions to account for stops.
# The different displayed train lengths will be realized by different statuscode_led_mappings, which contain all LEDs to light for a statuscode.
# 
# SNV -> 2+1
# RFV -> 4+1
# 

# In[6]:


def compute_animation_class(category):
    if category in ['S', 'RB']:
        return 'SNV'
    else:
        return 'RFV'
    
df_timetable['animation_class'] = df_timetable['category'].map(compute_animation_class)


# ## compute animation color
# each category receives a (not unique) color, which is used to display the respective trip.
# The color will later be included into the animationcode in two ways, the original color and a dimmed color for the trail

# In[ ]:


def compute_animation_color(category):
    if category in ['S']:
        # Color of the S-Bahn Logo
        return "019704"
    
    # maybe change RE to bwegt yellow color
    if category in ['RE', 'RB']:
        # Color of DB Regional Trains (Verkehrsrot)
        return "FD1621"
    
    if category in ['FLX']:
        # Color of Flixtrains
        return "00FF55"
    
    if category in ['NJ']:
        # Color of Nightjets, maybe needs to be lightened to be visible
        return "3D3DB3"
    
    if category in ['IC', 'ICE']:
        # White, like IC and ICE are painted <3
        return "FFFFFF"
    
    if category in ['RJ', 'RJX', 'TGV']:
        # Bright pink to signalize something special
        return "FC2DD2"
    
    # yellow for unknown train categories
    return 'F8FC00'

df_timetable['animation_color'] = df_timetable['category'].map(compute_animation_color)


    
    


# ## compute animationcodes
# 
# the computation of statuscodes works differently than the rnv computation. As rnv uses gtfs data, the status inside the animationcode shows the absolute position of the train on the network. Therefore only trains that are actually currently on the network can have a status / animationcode. For the DB data however, the position is noted relative to the arrival / departure time at Heidelberg Hbf by the difference of ticks between the current time and the arrival / departure time. Therefore every train can have a status / animationcode. Trains that are too far away from arriving or departing e.g. a train that will arrive in 30 minutes (=60 ticks) and can therefore not be displayed yet will simple by ignored by the display-animationcodes script, as the statuscode will not have a corresponding mapping entry in the LED and will just be skipped. Likewise trains arriving from the depot will be ignored until they are in the station, as there simply won't be statuscode mapping entries for that
# 
# There are two types of statuscodes:
# 
# Train is in Heidelberg Hbf: Statuscode consists of HDHBF_{facing_direction} with the direction being either northwest, southeast or none, depending on where the train is departing to. 
# Train is not in heidelberg hbf: in this case, The statuscode consist of the direction the train is looking from Heidelberg Hbf (north, east, south, west), the ticks (tick length 30s, diff_seconds / 30, rounded up, so 1 is the lowest possible value) it is away from Heidelberg Hbf and whether the train is inbound or outbound (inbound/outbound). 
# 
# lastly, the animationclass, statuscode and animation colors have to be put together into one string

# In[8]:


import math

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

def add_statuscode(timetable_row):
    
    arrival_datetime = DBDatetimeToDatetime(timetable_row['arrival_dbdatetime'])
    departure_datetime = DBDatetimeToDatetime(timetable_row['departure_dbdatetime'])
    now_datetime = datetime.datetime.now()
    
    statuscode = ''
    
    # arrival has happened, departure hasn't happened -> standing in Heidelberg Hbf
    if(arrival_datetime < now_datetime < departure_datetime):
        departure_direction = timetable_row['departure_direction']
        
        facing_to = None
        if departure_direction in ['north', 'west']:
            facing_to = 'northwest'
        elif departure_direction in ['south', 'east']:
            facing_to = 'southeast'
        # if the train is ending, it has no departure direction, therefore we need to check arrival direction and invert
        elif arrival_direction in ['north', 'west']:
            facing_to = 'southeast'
        elif arrival_direction in ['south', 'east']:
            facing_to = 'northwest'
            
        statuscode = f'HDHBF_{facing_to}'

    # arrival hasn't happened -> inbound
    elif(now_datetime < arrival_datetime):
        arrival_direction = timetable_row['arrival_direction']
        
        timedelta_to_arrival = arrival_datetime - now_datetime
        seconds_to_arrival = timedelta_to_arrival.total_seconds()
        ticks_to_arrival = math.ceil(seconds_to_arrival / TICK_LENGTH_SECONDS)
        
        # ignore everything that doesn't arrive for another 30 minutes and just return row unchanged
        if seconds_to_arrival > 30 * 60:
            return timetable_row
        
        statuscode = f"{arrival_direction}_{ticks_to_arrival}_inbound"
        
    # departure has happened -> outbound
    elif(departure_datetime < now_datetime):
        departure_direction = timetable_row['departure_direction']
        
        timedelta_since_departure = now_datetime - departure_datetime
        seconds_since_departure = timedelta_since_departure.total_seconds()
        ticks_since_departure = math.ceil(seconds_since_departure / TICK_LENGTH_SECONDS)
        
         # ignore everything that departed more than 30 minutes ago and just return row unchanged
        if seconds_since_departure > 30 * 60:
            return timetable_row
        
        statuscode = f"{departure_direction}_{ticks_since_departure}_outbound"
    
    
    animation_class = timetable_row['animation_class']
    primary_animation_color = timetable_row['animation_color']
    secondary_animation_color = dim_hex_color(primary_animation_color, SECONDARY_COLOR_DIM_FACTOR)
    
    animationcode = f"DB_{animation_class}:{statuscode}:{primary_animation_color}_{secondary_animation_color}"
    
    timetable_row['animationcode'] = animationcode
    return timetable_row

df_timetable = df_timetable.apply(add_statuscode, axis=1)


# ## save to disk

# In[9]:


df_animationcodes = df_timetable['animationcode'].dropna()

df_animationcodes.to_csv('db_animationcodes.csv', index=False)


# ## control dataframe

# In[10]:


#df_control = df_timetable

#df_control['trip_name'] = df_control.apply(lambda row: f"{row['category']} {row['line']}", axis=1)
#df_control['arrival'] = df_control['arrival_dbdatetime'].map(lambda arrival_dbdatetime: arrival_dbdatetime[6:])
#df_control['departure'] = df_control['departure_dbdatetime'].map(lambda departure_dbdatetime: departure_dbdatetime[6:])

#df_control = df_control.drop(columns=["animation_class"])

#df_control[['trip_name', 'arrival', 'departure', 'animationcode']].to_csv("control.csv")

