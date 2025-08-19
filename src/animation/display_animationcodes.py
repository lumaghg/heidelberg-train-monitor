# init display connection
# startup animation
# animate animationcodes twice a minute (after executing, calculated  necessary sleep time to stay in the rythm)

#!/usr/bin/env python
from matrixbase import MatrixBase
import time
from PIL import ImageColor
import pandas as pd
import numpy as np


# prepare base_overlay
base_overlay_rnv = np.full((64,32), "000000")
base_overlay_db = np.full((64,32), "000000")

# backgrund lighting
df_background_lighting_rnv = pd.read_csv('../background/background_lighting_rnv.csv', dtype=str)
df_background_lighting_db = pd.read_csv('../background/background_lighting_db.csv', dtype=str)

df_background_lighting_rnv = df_background_lighting_rnv.reset_index()  # make sure indexes pair with number of rows
df_background_lighting_db = df_background_lighting_db.reset_index()  # make sure indexes pair with number of rows

for index, row in df_background_lighting_rnv.iterrows():
    led = row['led']
    color_hex = row['color']
    
    x = int(led.split("-")[0])
    y = int(led.split("-")[1])
    
    base_overlay_rnv[x,y] = color_hex
    
for index, row in df_background_lighting_db.iterrows():
    led = row['led']
    color_hex = row['color']
    
    x = int(led.split("-")[0])
    y = int(led.split("-")[1])
    
    base_overlay_db[x,y] = color_hex


class DisplayCSV(MatrixBase):
    def __init__(self, *args, **kwargs):
        super(DisplayCSV, self).__init__(*args, **kwargs)


    def run(self):
        offset_canvas = self.matrix.CreateFrameCanvas()
        # loop

        tick_counter = 0
        
        while True:
            try:
                
                # background: 
                overlay = None
                df_animationcodes = None
                
                df_db_animationcodes = pd.read_csv('../db/db_animationcodes.csv', dtype=str)
                df_rnv_animationcodes = pd.read_csv('../rnv/rnv_animationcodes.csv', dtype=str)

                # always do two ticks of db, then two ticks of rnv
                if tick_counter <= 2:
                    overlay = base_overlay_db.copy()
                    df_animationcodes = df_db_animationcodes
                    
                if tick_counter >= 3:
                    overlay = base_overlay_rnv.copy()
                    df_animationcodes = df_rnv_animationcodes
                    
                tick_counter = tick_counter + 1 if tick_counter != 6 else 0
                     
                
                #df_animationcodes = pd.concat([df_db_animationcodes, df_rnv_animationcodes])
                

                df_db_rfv_mapping = pd.read_csv('./mappings/db_rfv_mapping.csv', dtype=str)
                df_db_snv_mapping = pd.read_csv('./mappings/db_snv_mapping.csv', dtype=str)
                df_rnv_mapping = pd.read_csv('./mappings/rnv_mapping.csv', dtype=str)


                def process_animationcode(animationcode: str):
                    try:
                        
                        type, statuscode, colors = animationcode.split(":")
                        
                        primary_color_hex = colors.split("_")[0]
                        secondary_color_hex = colors.split("_")[1]
                        
                        df_mapping = None
                        if type == 'DB_SNV':
                            df_mapping = df_db_snv_mapping
                        elif type == 'DB_RFV':
                            df_mapping = df_db_rfv_mapping
                        else:
                            df_mapping = df_rnv_mapping
                        
                        applicable_mapping_rows = df_mapping[df_mapping['statuscode'] == statuscode].reset_index(drop=True)
                        
                        if len(applicable_mapping_rows) == 0:
                            return

                        mapping_row = applicable_mapping_rows.iloc[0]
                        
                        primary_leds:str = mapping_row['leds_primary']
                        
                        if not pd.isna(primary_leds):
                            pixels_xy = primary_leds.split("&")
                            
                            for pixel in pixels_xy:
                                x = int(pixel.split("-")[0])
                                y = int(pixel.split("-")[1])
                                
                                overlay[x,y] = primary_color_hex
                            
                            
                        secondary_leds:str = mapping_row['leds_secondary']
                        
                        if not pd.isna(secondary_leds):
                            pixels_xy = secondary_leds.split("&")
                            for pixel in pixels_xy:
                                x = int(pixel.split("-")[0])
                                y = int(pixel.split("-")[1])
                                
                                overlay[x,y] = secondary_color_hex
                                
                    except Exception as e:
                        print(e)
                    
                df_animationcodes['animationcode'].map(process_animationcode)    
                
                for x in range(overlay.shape[0]):
                    for y in range(overlay.shape[1]):
                        color_hex = overlay[x,y]                    
                        color_rgb = ImageColor.getcolor(f"#{color_hex}", "RGB")
                        offset_canvas.SetPixel(int(x), int(y), color_rgb[0], color_rgb[1], color_rgb[2])   
                offset_canvas = self.matrix.SwapOnVSync(offset_canvas)
                
                
            except Exception as e:
                print(e)
                continue
           
            time.sleep(15)

# Main function
if __name__ == "__main__":
    simple_square = DisplayCSV()
    if (not simple_square.process()):
        simple_square.print_help()


    

