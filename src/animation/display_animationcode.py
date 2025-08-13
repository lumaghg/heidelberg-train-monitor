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
                
                print(df_background_lighting.head(5))

                for index, row in df_background_lighting.iterrows():
                    led = row['led']
                    color_hex = row['color']
                
                    x = int(led.split("-")[0])
                    y = int(led.split("-")[1])
                                   
                    color_rgb = ImageColor.getcolor(f"#{color_hex}", "RGB")
                    offset_canvas.SetPixel(x, y, color_rgb[0], color_rgb[1], color_rgb[2])      
                offset_canvas = self.matrix.SwapOnVSync(offset_canvas)
                
                # process animationcodes
                
                df_statuscodes = pd.read_csv('../db/db_animationcodes.csv', dtype=str)
                
                
                
                
                

                time.sleep(2)
            except Exception as e:
                print(e)
                continue
           

# Main function
if __name__ == "__main__":
    simple_square = DisplayCSV()
    if (not simple_square.process()):
        simple_square.print_help()


    

