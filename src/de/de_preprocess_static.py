#!/usr/bin/env python
# coding: utf-8

# # Preprocess static data from DB Timetables API
# 
# - script runs hourly
# - to be able to know about every train that is currently on the way, we need data for current_time +- time of the longest trip between stations without stopping, which is 4h (FFM-Berlin Sprinter). Data should last for 1 hour before updating. Therefore we need to request current hour, the 4 hours before that and the 4 hours after that = 9 hours. 
# Steps:
# - delete data from timetable that is for an hour before current hour - 4. 
# - request the timetable from every relevant station, and parse the xmls into a timetable while filtering for Fernverkehr (category in [ICE, IC, EC, NJ ...]). Note which date/hour was used to make the request. 
# - artificially add departure and arrival dates where missing
# - sort by I. tripid 2. departure time / stop order

# ### helper functions for handling db dates

# In[19]:


import datetime
from dotenv import load_dotenv
from os import getenv
import pandas as pd
import ratelimit

load_dotenv()

PLANNED_STOPTIMES_PATH = 'stoptimes_planned.csv'
STATIONS_PATH = './static/stations.csv'
REQUEST_LOG_PATH = './request_log.csv'
FV_CATEGORIES = ["IC", "EC", "ICE", "FLX", "WB", "RJ", "RJX", "ECE", "EST", "TGV", "NJ", "EN", "ES", "DN", "D", "SJ"]

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


# In[20]:


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


# In[21]:


# calculate which times need to be requested

date_hour_tuples_to_request = []

current_datetime = datetime.datetime.today()

for hour_offset in range(-4,5):
    datetime_to_request = current_datetime + datetime.timedelta(hours=hour_offset)
    date_hour_tuple = datetimeToDBDateAndHourTuple(datetime_to_request)
    date_hour_tuples_to_request.append(datetimeToDBDateAndHourTuple(datetime_to_request))


print(date_hour_tuples_to_request)



# In[22]:


# load stations that need to be requested
df_stations = pd.read_csv(STATIONS_PATH, dtype=str).dropna(how='all')
print(df_stations)


# In[23]:


# request and process timetables
import requests
import xmltodict
import time
import os.path as path

# load envs
db_timetables_base_url = getenv("db_timetables_base_url")
db_client_id = getenv("db_client_id")
db_client_secret = getenv("db_client_secret")



# delete stop times belonging to hours more than 4 hours ago (request timestamp marks the hour in which the stoptime happens)
df_stoptimes = None

four_hours_ago_tuple = datetimeToDBDateAndHourTuple(datetime.datetime.now() - datetime.timedelta(hours=4))
request_timestamp_four_hours_ago = f"{four_hours_ago_tuple[0]}{four_hours_ago_tuple[1]}"

if path.exists(PLANNED_STOPTIMES_PATH):
    df_stoptimes = pd.read_csv(PLANNED_STOPTIMES_PATH, dtype=str).dropna(how='all')
    df_stoptimes = df_stoptimes.drop(df_stoptimes[df_stoptimes['request_timestamp'] < request_timestamp_four_hours_ago].index)
    
else:
    df_stoptimes = pd.DataFrame(columns=['trip_id', 'category', 'number', 'station_name', 'arrival_planned_dbdatetime', 'departure_planned_dbdatetime', 'arrival_ppth', 'departure_ppth', 'request_timestamp','station_uic'])



# load request log or create if not exists and delete entries older than 9 hours
df_request_log = None
if(path.exists(REQUEST_LOG_PATH)):
    df_request_log = pd.read_csv(REQUEST_LOG_PATH, dtype=str).dropna(how='all')
    df_request_log = df_request_log.drop(df_request_log[df_request_log['request_timestamp'] < request_timestamp_four_hours_ago].index)
else:
    df_request_log = pd.DataFrame(columns=['request_timestamp', 'station_uic'])
    

xml_timestamp_tuple = []

request_counter = 0


for index, station_row in df_stations.iterrows():

    station_uic = station_row['station_uic']
    station_name = station_row['station_name']
    
    print(f"requesting {station_name}")
        
    timetable_rows_for_current_station = []
        
    for date_hour_tuple in date_hour_tuples_to_request:
        try:
            date_to_request = date_hour_tuple[0] 
            hour_to_request = date_hour_tuple[1] 
            request_timestamp = f"{date_to_request}{hour_to_request}"
            
            # check if station / request_timestamp combination has already been fetched
            rows_for_timestamp_and_station = df_request_log[(df_request_log['request_timestamp'] == request_timestamp) & (df_request_log['station_uic'] == station_uic)]
            no_rows_for_timestamp_and_station = rows_for_timestamp_and_station.shape[0]
            
            
            if no_rows_for_timestamp_and_station > 0:
                print(f"{date_to_request} / {hour_to_request}:00 / {station_name} already present")
                # already fetched
                continue
            
            # respect rate limiting
            ratelimit.wait_for_slot()
            
            
            print(f"fetching {date_to_request} / {hour_to_request}:00 / {station_name}")
            
            # prepare request headers
            auth_headers = {
                'DB-Client-Id': db_client_id,
                'DB-Api-Key': db_client_secret
            }
            
            # {hour:02} means print hour, fill (0) up to 2 (2) digits
            url = f"{db_timetables_base_url}/plan/{station_uic}/{date_to_request}/{hour_to_request}"
            
            
            response = requests.get(url=url, headers=auth_headers)
            if response.status_code != 200:
                print(f"skipping hour {hour_to_request}, station {station_uic}, {response.status_code}")
                continue
            
            # note which stations / times have already been requested
            df_request_log = pd.concat([df_request_log, pd.DataFrame(data={'request_timestamp': [request_timestamp], 'station_uic': [station_uic]})])
            
            
            # process response
            timetable_dict = xmltodict.parse(response.content)
            if timetable_dict['timetable'] is None:
                print(f'empty timetable: skipping hour {hour_to_request}, station {station_uic}')
                continue
            
            timetable_stops = timetable_dict['timetable']['s']
            
            # if there is only one trip in the requested hour, the xml parser parses the timetable stop entry into a dict rather than a list
            if not isinstance(timetable_stops, list):
                timetable_stops = [timetable_stops]
            
            for timetable_stop in timetable_stops:
                try:
                    # category (e.g. ICE, RE, S)
                    trip_label = timetable_stop['tl']
                    category = trip_label['@c']
                    number = trip_label['@n']
                    
                    # for some idiotic reason, the ids can start with a dash while also being separated by a dash
                    stop_id = timetable_stop['@id']
                    
                    trip_id = extract_tripid_from_stopid(stop_id)
                    
                    
                    # only save Fernverkehr (not using filter flag because NJ dont have them)
                    if category not in FV_CATEGORIES:
                        continue
                    
                    # arrival
                    arrival_planned_dbdatetime = None
                    arrival_ppth = None
                    
                    if 'ar' in timetable_stop:
                        arrival = timetable_stop['ar']
                        arrival_planned_dbdatetime = arrival['@pt']
                        arrival_ppth = arrival['@ppth']
                        
                    # departure
                    departure_planned_dbdatetime = None
                    
                    if 'dp' in timetable_stop:
                        departure = timetable_stop['dp']
                        departure_planned_dbdatetime = departure['@pt']   
                        departure_ppth = departure['@ppth']
                    
                            
                    stoptimes_row = pd.DataFrame(data={'trip_id': [trip_id], 'category':[category], 'number': [number], 'station_name':[station_name], 'arrival_planned_dbdatetime': [arrival_planned_dbdatetime], 'departure_planned_dbdatetime':[departure_planned_dbdatetime], 'arrival_ppth': [arrival_ppth], 'departure_ppth': [departure_ppth], 'request_timestamp': [request_timestamp], 'station_uic': station_uic})

                    df_stoptimes = pd.concat([df_stoptimes, stoptimes_row], ignore_index=True)
                    
                except Exception as e:
                    print(f"error while processing timetable stop")
                    print(e)
                    
        except Exception as e:
            print(f"error while fetching or converting {date_to_request} / {hour_to_request}:00 / {station_name}")
            print(e)
    
    # after every station postprocess and save:
    
    # remove duplicates
    # duplicates can occur when a train arrives before and departs after the full hour, because in this case the train will be included in both slices

    df_stoptimes = df_stoptimes.drop_duplicates(subset=['trip_id', 'station_uic', 'departure_planned_dbdatetime'])
    

    
    # sort
    df_stoptimes = df_stoptimes.sort_values(by=['trip_id','departure_planned_dbdatetime'])
    
    # duplicate departures and arrivals to prepare for realtime changes
    df_stoptimes['arrival_actual_dbdatetime'] = df_stoptimes.loc[:,'arrival_planned_dbdatetime']
    df_stoptimes['departure_actual_dbdatetime'] = df_stoptimes.loc[:,'departure_planned_dbdatetime']
    
    # save after every station 
    df_stoptimes.to_csv(PLANNED_STOPTIMES_PATH, index=False)
    df_request_log.to_csv(REQUEST_LOG_PATH, index=False)


# In[24]:


# sort dataframe by tripid and departure

df_stoptimes = df_stoptimes.sort_values(by=['trip_id','departure_planned_dbdatetime'])

df_stoptimes.to_csv(PLANNED_STOPTIMES_PATH, index=False)


# In[ ]:




