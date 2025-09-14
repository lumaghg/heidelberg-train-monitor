#!/usr/bin/env python
# coding: utf-8

# In[45]:


import pandas as pd
import networkx as nx

df_stations = pd.read_csv('./static/stations.csv', dtype=str).dropna(how='all')
df_stretches = pd.read_csv('./static/stretches.csv', dtype=str).dropna(how='all')

G = nx.Graph()

# add nodes
station_list = list(df_stations.itertuples(index=False, name=None)) # [(station_name, station_uic)]
nodes = [(station[1], {'station_name': station[0]}) for station in station_list]
G.add_nodes_from(nodes)

# add edges
# attraction force is used to draw the graph by defining the attraction force between the two nodes and is the inverted travel time
edge_list = list(df_stretches[['station_uic_from', 'station_uic_to', 'station_name_from','station_name_to','travel_cost','super_name']].itertuples(index=False, name=None)) # [(station_name_from, station_uic_from, station_name_to, station_uic_from, travel_cost, super_name)]
edges = [(edge[0], edge[1], {'station_name_from': edge[2], 'station_name_to': edge[3], 'travel_cost': int(edge[4]), 'super_name': edge[5]}) for edge in edge_list]
G.add_edges_from(edges)


# In[46]:


df_stoptimes_planned = pd.read_csv('./stoptimes_planned.csv').dropna(how='all')
df_stoptimes_planned = df_stoptimes_planned[['trip_id', 'arrival_ppth', 'departure_ppth', 'station_name']]

# only one entry of each tripid need to be examined

df_trips = df_stoptimes_planned.groupby('trip_id', as_index=False).first()


df_tripid_stretchid = pd.DataFrame(columns=['trip_id', 'stretch_id', 'stretch_name'])

# for every tripid, add one entry for every stretchid that corresponds to 


def get_station_uic_for_station_name(station_name:str):
    possible_stations = df_stations[df_stations['station_name'] == station_name]
    if len(possible_stations) == 0:
        return None
    return possible_stations.iloc[0]['station_uic']

for index, row in df_trips.iterrows():
    
    trip_id = row['trip_id']
    arrival_ppth:str = row['arrival_ppth']
    current_station_name:str = row['station_name']
    departure_ppth:str = row['departure_ppth']
    
    station_uics = []
    station_names = []
    
    if arrival_ppth != None:
        for station in arrival_ppth.split("|"):
            station_names.append(station)
            station_uic = get_station_uic_for_station_name(station)
            station_uics.append(station_uic)
     
    station_uics.append(get_station_uic_for_station_name(current_station_name))
    station_names.append(current_station_name)
            
    if departure_ppth != None:
        for station in departure_ppth.split("|"):
            station_names.append(station)
            station_uic = get_station_uic_for_station_name(station)
            station_uics.append(station_uic)
            
            
    # filter so that only station uics that are supported by the application remain to avoid nodes not being found in the Graph
    
    filtered_station_uics = [i for i in station_uics if i in df_stations['station_uic'].values]
    filtered_station_names = [i for i in station_names if i in df_stations['station_name'].values]

            
    # now go over all the tuples of stations and find the shortest path to compute all the stretches

    for i in range(len(filtered_station_uics)-1):
        
        
        previous_station_uic = filtered_station_uics[i]
        next_station_uic = filtered_station_uics[i+1]

        shortest_path = nx.shortest_path(G, previous_station_uic, next_station_uic, weight='travel_cost')

                
        # every tuple of the shortest path is a stretch (graph edge) by definition
        
        for j in range(len(shortest_path) - 1):
            previous_station_uic = shortest_path[j]
            next_station_uic = shortest_path[j+1]
            
            # stretches are only marked in one direction, so try both permutations
            stretch_candidates = df_stretches[
                ((df_stretches['station_uic_from'] == previous_station_uic) & (df_stretches['station_uic_to'] == next_station_uic)) | 
                ((df_stretches['station_uic_from'] == next_station_uic) & (df_stretches['station_uic_to'] == previous_station_uic))
                                   ]
            
            if len(stretch_candidates) == 0:
                # skip if stretch doesnt exist for whatever reason
                continue
            
            stretch_id = stretch_candidates.iloc[0]['stretch_id']
            stretch_name = stretch_candidates.iloc[0]['stretch_name']
            
            tripid_stretchid_row = pd.DataFrame(data={'trip_id': [trip_id], 'stretch_id': [stretch_id], 'stretch_name': [stretch_name]})
            
            df_tripid_stretchid = pd.concat(objs=[df_tripid_stretchid, tripid_stretchid_row])

df_tripid_stretchid.to_csv("tripid_stretchid.csv", index=False)


# In[ ]:




