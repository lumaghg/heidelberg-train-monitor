#!/usr/bin/env python
# coding: utf-8

# In[335]:


import datetime
from dotenv import load_dotenv
from os import getenv
import pandas as pd
import ratelimit

load_dotenv()

STOPTIMES_PATH = 'stoptimes.csv'
PLANNED_STOPTIMES_PATH = 'stoptimes_planned.csv'
STATIONS_PATH = './static/stations.csv'


# In[336]:


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

def datetimeToDBDateAndHourTuple(dt: datetime.datetime):
    date = dt.strftime("%y%m%d")
    hour = dt.strftime("%H")
    return (date, hour)
    
       
print(dateToDBDate(datetime.date(2025, 8, 10)))
print(datetimeToDBDatetime(datetime.datetime(2025, 8, 10, 12, 22)))
print(DBDateToDate("250810"))
print(DBDatetimeToDatetime("2508101222"))
print(datetimeToDBDateAndHourTuple(datetime.datetime(2025, 8, 10, 12, 22)))


# In[337]:


# load stations that need to be requested
df_stations = pd.read_csv(STATIONS_PATH, dtype=str).dropna(how='all')
print(df_stations)


# In[338]:


# helper functions

def extract_tripid_from_stopid(stop_id: str):
                
    has_dash = True if stop_id.startswith("-") else False

    trip_id = None

    if has_dash:
        # if stop id has dash, the first split result will be empty
        trip_id = stop_id.split("-")[1]
        trip_id = f"-{trip_id}"
    else:
        trip_id = stop_id.split("-")[0]
    return trip_id


# Fall 1: id ist bekannt
#     Fall 1.1: id/uic Kombination ist bekannt: update / canceled => wenn cs = c dann auf None, sonst auf ct setzen
#     Fall 1.2: id/uic Kombination ist nicht bekannt: neuer stop, category und number klauen, neu anlegen mit time, evtl. erstmal ignorieren bis solche Daten da sind
#     Schluss
# Fall 2: id ist nicht bekannt => neuer Trip. Trip hat planned data und trip label, neuen stop anlegen.
# 

# In[339]:


# request and process changes
import requests
import xmltodict
import time
import os.path as path

# load envs
db_timetables_base_url = getenv("db_timetables_base_url")
db_client_id = getenv("db_client_id")
db_client_secret = getenv("db_client_secret")

# for querying and matching planned stop times
df_stoptimes_planned = pd.read_csv(PLANNED_STOPTIMES_PATH, dtype=str).dropna(how='all')
df_stoptimes = df_stoptimes_planned.copy()

for index, station_row in df_stations.iterrows():
    try:
        # for mutating and saving updated data
        station_uic = station_row['station_uic']
        station_name = station_row['station_name']
            
        # respect rate limiting
        ratelimit.wait_for_slot()    
            
        print(f"fetching fchg for {station_name}")
        
        # prepare request headers
        auth_headers = {
            'DB-Client-Id': db_client_id,
            'DB-Api-Key': db_client_secret
        }
        
        # {hour:02} means print hour, fill (0) up to 2 (2) digits
        url = f"{db_timetables_base_url}/fchg/{station_uic}"
            
            
        response = requests.get(url=url, headers=auth_headers)
        if response.status_code != 200:
            print(f"skipping station {station_uic}, {response.status_code}")
            continue
            
            
        # process response
        timetable_fchg_dict = xmltodict.parse(response.content)
        
        # process response
        timetable_fchg_dict = xmltodict.parse(response.content)
        if timetable_fchg_dict['timetable'] is None:
            print(f'empty timetable: skipping station {station_uic}')
            continue
        
        timetable_fchg_stops = timetable_fchg_dict['timetable']['s']
        
        # if there is only one trip in the requested hour, the xml parser parses the timetable stop entry into a dict rather than a list
        if not isinstance(timetable_fchg_stops, list):
            timetable_fchg_stops = [timetable_fchg_stops]
        
        for timetable_fchg_stop in timetable_fchg_stops:
            try:
                # try to find id in stop_times
                stop_id = timetable_fchg_stop['@id']
                trip_id = extract_tripid_from_stopid(stop_id)
                
                planned_stop_times_with_id = df_stoptimes[df_stoptimes['trip_id'] == trip_id]
                
                
                
                # Fall 1
                if len(planned_stop_times_with_id) > 0:

                    planned_stop_times_with_id_and_station = df_stoptimes[(df_stoptimes['trip_id'] == trip_id) & (df_stoptimes['station_uic'] == station_uic)]
                    
                    # Fall 1.1: id an diesem Bahnhof bekannt -> update
                    if len(planned_stop_times_with_id_and_station) > 0:
                        updated_stop_time = planned_stop_times_with_id_and_station.iloc[0].copy()
                        stop_time_index_to_update = planned_stop_times_with_id_and_station.index[0]
                        
                        # update arrival if changed
                        if 'ar' in timetable_fchg_stop:
                            arrival = timetable_fchg_stop['ar']
                            
                            # cancel if stop was canceled
                            if '@cs' in arrival:
                                if arrival['@cs'] == 'c':
                                    updated_stop_time['arrival_actual_dbdatetime'] = None
                                
                            # update if stop was not canceled
                            elif '@ct' in arrival:
                                updated_stop_time['arrival_actual_dbdatetime'] = arrival['@ct']
                        
                        # save changed updated stop time
                        df_stoptimes.loc[stop_time_index_to_update] = updated_stop_time      
                        
                        # update departure if changed
                        if 'dp' in timetable_fchg_stop:
                            departure = timetable_fchg_stop['dp']
                            
                            # cancel if stop was canceled
                            if '@cs' in departure:
                                if departure['@cs'] == 'c':
                                    updated_stop_time['departure_actual_dbdatetime'] = None
                                
                            # update if stop was not canceled
                            elif '@ct' in departure:
                                updated_stop_time['departure_actual_dbdatetime'] = departure['@ct']
                                
                        # save changed updated stop time
                        df_stoptimes.loc[stop_time_index_to_update] = updated_stop_time
                  
                        
                    
                    # Fall 1.2 - id an diesem Bahnhof unbekannt -> Zusatzhalt
                    else:
                        # TODO or ignore
                        pass
                
                # Fall 2
                else:
                    # id unbekannt -> Regionalverkehrstrip oder Ersatzfahrt, wenn trip label mit category in Fernverkehr vorhanden, dann stop anlegen.
                    # TODO or ignore
                    pass
                
            
            except Exception as e:
                print("error during processing timetable stop")
                print(e)

    except Exception as e:
        print(f"error during fetching or postprocessing station {station_name}")
        print(e)
    
# POSTPROCESS BEFORE SAVING

# remove duplicates
# duplicates can occur when a train arrives before and departs after the full hour, because in this case the train will be included in both slices

df_stoptimes = df_stoptimes.drop_duplicates(subset=['trip_id', 'station_uic','departure_planned_dbdatetime','departure_actual_dbdatetime'])

# remove stoptimes without an arrival or a departure (can happen when a stop is cancelled)
df_stoptimes = df_stoptimes.dropna(subset=['arrival_actual_dbdatetime','departure_actual_dbdatetime'], how='all')

    
# add departure / arrival where necessary. Every stop needs a departure and arrival for animation to work 
# set arrival to departure where arrival is na
departure_actual_isna_mask =  df_stoptimes['departure_actual_dbdatetime'].isna()
df_stoptimes.loc[departure_actual_isna_mask, 'departure_actual_dbdatetime'] = df_stoptimes[departure_actual_isna_mask]['arrival_actual_dbdatetime']

departure_planned_isna_mask =  df_stoptimes['departure_planned_dbdatetime'].isna()
df_stoptimes.loc[departure_planned_isna_mask, 'departure_planned_dbdatetime'] = df_stoptimes[departure_planned_isna_mask]['arrival_planned_dbdatetime']


arrival_actual_isna_mask =  df_stoptimes['arrival_actual_dbdatetime'].isna()
df_stoptimes.loc[arrival_actual_isna_mask, 'arrival_actual_dbdatetime'] = df_stoptimes[arrival_actual_isna_mask]['departure_actual_dbdatetime']

arrival_planned_isna_mask =  df_stoptimes['arrival_planned_dbdatetime'].isna()
df_stoptimes.loc[arrival_planned_isna_mask, 'arrival_planned_dbdatetime'] = df_stoptimes[arrival_planned_isna_mask]['departure_planned_dbdatetime']

# sort
df_stoptimes = df_stoptimes.sort_values(by=['trip_id','departure_actual_dbdatetime'])

# convert arrival and departure to datetimes
df_stoptimes['arrival_planned'] = df_stoptimes['arrival_planned_dbdatetime'].map(DBDatetimeToDatetime)
df_stoptimes['departure_planned'] = df_stoptimes['departure_planned_dbdatetime'].map(DBDatetimeToDatetime)
df_stoptimes['arrival_actual'] = df_stoptimes['arrival_actual_dbdatetime'].map(DBDatetimeToDatetime)
df_stoptimes['departure_actual'] = df_stoptimes['departure_actual_dbdatetime'].map(DBDatetimeToDatetime)  

# compute arrival and departure delay in minutes (min: 0)
def compute_arrival_delay(row):
    delta:datetime.timedelta = row['arrival_actual'] - row['arrival_planned']
    delay = max(int(delta.total_seconds() / 60),0)
    return delay

def compute_departure_delay(row):
    delta:datetime.timedelta = row['departure_actual'] - row['departure_planned']
    delay = max(int(delta.total_seconds() / 60),0)
    return delay

df_stoptimes['arrival_delay'] = df_stoptimes.apply(compute_arrival_delay, axis=1)  
df_stoptimes['departure_delay'] = df_stoptimes.apply(compute_departure_delay, axis=1)  

# rename actual columns for easier and less confusing processing later on
df_stoptimes['arrival'] = df_stoptimes.loc[:,'arrival_actual']
df_stoptimes['departure'] = df_stoptimes.loc[:,'departure_actual']
        
# remove now uneeded old arrival and departure columns 
df_stoptimes=df_stoptimes.drop(labels=['arrival_planned_dbdatetime','departure_planned_dbdatetime','arrival_actual_dbdatetime', 'departure_actual_dbdatetime','arrival_planned', 'departure_planned', 'arrival_actual', 'departure_actual'], axis=1)


# save
df_stoptimes.to_csv(STOPTIMES_PATH, index=False)

    


# In[ ]:




