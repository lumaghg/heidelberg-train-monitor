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

base_overlay_db = np.full((64,32), "000000")

# backgrund lighting
df_background_lighting_db = pd.read_csv('../background/background_lighting_db_fv.csv', dtype=str)

df_background_lighting_db = df_background_lighting_db.reset_index()  # make sure indexes pair with number of rows

    
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
        
        while True:
            try:
                
                # background: 
                overlay = None
                
                for x in range(overlay.shape[0]):
                    for y in range(overlay.shape[1]):
                        color_hex = overlay[x,y]                    
                        color_rgb = ImageColor.getcolor(f"#{color_hex}", "RGB")
                        offset_canvas.SetPixel(int(x), int(y), color_rgb[0], color_rgb[1], color_rgb[2])   
                offset_canvas = self.matrix.SwapOnVSync(offset_canvas)
                
                
            except Exception as e:
                print(e)
                continue
           
            time.sleep(5)

# Main function
if __name__ == "__main__":
    simple_square = DisplayCSV()
    if (not simple_square.process()):
        simple_square.print_help()


    

