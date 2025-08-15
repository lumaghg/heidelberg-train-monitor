# init display connection
# startup animation
# animate animationcodes twice a minute (after executing, calculated  necessary sleep time to stay in the rythm)

#!/usr/bin/env python
from matrixbase import MatrixBase
import time
from PIL import ImageColor
import pandas as pd
import numpy as np



class DisplayCSV(MatrixBase):
    def __init__(self, *args, **kwargs):
        super(DisplayCSV, self).__init__(*args, **kwargs)





    def run(self):
        offset_canvas = self.matrix.CreateFrameCanvas()
        # loop

        while True:
            try:
                
                # background: 
                
                df_background_lighting = pd.read_csv('../background/background_lighting.csv', dtype=str)
                
                df_background_lighting = df_background_lighting.reset_index()  # make sure indexes pair with number of rows

                for index, row in df_background_lighting.iterrows():
                    led = row['led']
                    color_hex = row['color']
                
                    x = int(led.split("-")[0])
                    y = int(led.split("-")[1])
                                   
                    color_rgb = ImageColor.getcolor(f"#{color_hex}", "RGB")
                    offset_canvas.SetPixel(x, y, color_rgb[0], color_rgb[1], color_rgb[2])      
                
                
                # process animationcodes

                df_animationcodes = pd.read_csv('../db/db_animationcodes.csv', dtype=str)

                df_db_rfv_mapping = pd.read_csv('./db_rfv_mapping.csv', dtype=str)
                df_db_snv_mapping = pd.read_csv('./db_snv_mapping.csv', dtype=str)


                def process_animationcode(animationcode: str):
                    try:
                        
                        type, statuscode, colors = animationcode.split(":")
                        
                        primary_color_hex = colors.split("_")[0]
                        primary_color_rgb = ImageColor.getcolor(f"#{primary_color_hex}", "RGB")
                        
                        secondary_color_hex = colors.split("_")[1]
                        secondary_color_rgb = ImageColor.getcolor(f"#{secondary_color_hex}", "RGB")
                        
                        df_mapping = None
                        if type == 'DB_SNV':
                            df_mapping = df_db_snv_mapping
                        elif type == 'DB_RFV':
                            df_mapping = df_db_rfv_mapping
                        else:
                            return
                        
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
                                
                                offset_canvas.SetPixel(x, y, primary_color_rgb[0], primary_color_rgb[1], primary_color_rgb[2])   
                            
                            
                        secondary_leds:str = mapping_row['leds_secondary']
                        
                        if not pd.isna(secondary_leds):
                            pixels_xy = secondary_leds.split("&")
                            for pixel in pixels_xy:
                                x = int(pixel.split("-")[0])
                                y = int(pixel.split("-")[1])
                                
                                offset_canvas.SetPixel(x, y, secondary_color_rgb[0], secondary_color_rgb[1], secondary_color_rgb[2])   
                    except Exception as e:
                        print(e)
                    
                    
                df_animationcodes['animationcode'].map(process_animationcode)    
                offset_canvas = self.matrix.SwapOnVSync(offset_canvas)
                
                
            except Exception as e:
                print(e)
                continue
           
            time.sleep(14)

# Main function
if __name__ == "__main__":
    simple_square = DisplayCSV()
    if (not simple_square.process()):
        simple_square.print_help()


    

