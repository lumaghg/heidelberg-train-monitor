#!/usr/bin/env python
# coding: utf-8

# # Preprocess static data from DB Timetables API
# 
# - request departures and arrivals from / to relevant stations for the whole day
# - filter trains for relevant service types (e.g. ICE / S / RE etc.)
# - save to disk
# 
# runs once at startup and once every night at 0:05 am

# ## Request timetables for the current day from 1-23 am (0am doesnt work for some reason)

# ### helper functions for handling db dates

# In[4]:


import datetime
from dotenv import load_dotenv
from os import getenv

load_dotenv()

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


# In[5]:


# download all 23 available timeslots for the day
import requests
import xmltodict

# load envs
db_timetables_base_url = getenv("db_timetables_base_url")
db_client_id = getenv("db_client_id")
db_client_secret = getenv("db_client_secret")

eva_number_heidelberg_hbf = 8000156

# prepare date
date_today = datetime.date.today()
dbdate_today = dateToDBDate(date_today)

print(dbdate_today)

# prepare request headers
auth_headers = {
    'DB-Client-Id': db_client_id,
    'DB-Api-Key': db_client_secret
}

responses_xml = []

for hour in range(1,24):
    # {hour:02} means print hour, fill (0) up to 2 (2) digits
    url = f"{db_timetables_base_url}/plan/{eva_number_heidelberg_hbf}/{dbdate_today}/{hour:02}"
    
    response = requests.get(url=url, headers=auth_headers)
    if response.status_code != 200:
        print(f"skipping hour {hour}, {response.status_code}")
        continue
    responses_xml.append(response)
    


# ## process xml responses
# 
# now that we have saved all the xmls we need, we can go through them one by one, extract the relevant attributes and save them in a dataframe 

# In[6]:


import pandas as pd

def process_timetable_stop(timetable_stop):
    try:
        
        # category (e.g. ICE, RE, S)
        trip_label = timetable_stop['tl']
        category = trip_label['@c']
        
        # arrival
        arrival_dbdatetime = None
        arrival_path = None
        
        if 'ar' in timetable_stop:
            arrival = timetable_stop['ar']
            arrival_dbdatetime = arrival['@pt']
            arrival_path = arrival['@ppth']
            
        # departure
        departure_dbdatetime = None
        departure_path = None
        
        if 'dp' in timetable_stop:
            departure = timetable_stop['dp']
            departure_dbdatetime = departure['@pt']
            departure_path = departure['@ppth']
        
        # line (just for development)
        line = None
        
        if category in ["ICE", "IC", "FLX", "RJ", "RJX", "NJ", "TGV"]:
            line = trip_label['@n']
        elif 'ar' in timetable_stop:
            line = timetable_stop['ar']['@l']
        elif 'dp' in timetable_stop:
            line = timetable_stop['dp']['@l']
                
        timetable_row = pd.DataFrame(data={'category':[category], 'line': [line], 'arrival_dbdatetime': [arrival_dbdatetime], 'arrival_path':[arrival_path], 'departure_dbdatetime':[departure_dbdatetime], 'departure_path':[departure_path]})
        return timetable_row
    
    except Exception as e:
        print(e)


timetable_rows = []

for response_xml in responses_xml:
    try:
        
        # convert response_xml to dict
        timetable = xmltodict.parse(response_xml.content)

        timetable_stops = timetable['timetable']['s']
        
        # if there is only one trip in the requested hour, the xml parser parses the timetable stop entry into a dict rather than a list
        if isinstance(timetable_stops, list):
            for timetable_stop in timetable_stops:
                timetable_row = process_timetable_stop(timetable_stop)
                timetable_rows.append(timetable_row)
        else:
            timetable_row = process_timetable_stop(timetable_stops)
            timetable_rows.append(timetable_row)
    except:
        print(f"error while processing timetable response. maybe this timetable was empty?")
df_timetable = pd.concat(timetable_rows, ignore_index=True)
print(df_timetable.head(5))



# finally, sort the list by arrival_dbdatetime and save the timetable to disk for later use throughout the day

# In[7]:


df_timetable = df_timetable.drop_duplicates()
df_timetable.to_csv('db_timetable.csv', index=False)


# In[ ]:




