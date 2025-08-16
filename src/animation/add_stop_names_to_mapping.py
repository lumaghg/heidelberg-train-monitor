import pandas as pd
rnv_mapping = pd.read_csv('rnv_mapping_raw.csv', dtype=str)

stops = pd.read_csv('stops.csv', dtype=str, delimiter=',')

print(stops.head(5))
print(rnv_mapping.head(5))



def compute_readable(statuscode: str):
    try:
        statuscode_from = statuscode.split("_")[0]
        statuscode_to = statuscode.split("_")[1]

        stop_name_from = stops[stops['stop_base_id'] == statuscode_from].iloc[0]['stop_name']
        stop_name_to = stops[stops['stop_base_id'] == statuscode_to].iloc[0]['stop_name']
        
        return f"{stop_name_from} -> {stop_name_to}"
    except Exception as e:
        print(f"Error while looking up: {statuscode}")
        
rnv_mapping['readable'] = rnv_mapping['statuscode'].map(compute_readable)

print(rnv_mapping.head(5))

rnv_mapping.to_csv('rnv_mapping.csv')
