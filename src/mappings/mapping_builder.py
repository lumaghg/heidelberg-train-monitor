# script to iterate through a statuscode - led mapping and fill the missing leds by moving around the screen

import pandas as pd
import matrixbase

# init display connection
# startup animation
# animate animationcodes twice a minute (after executing, calculated  necessary sleep time to stay in the rythm)

#!/usr/bin/env python
from matrixbase import MatrixBase
import time
from PIL import ImageColor
import pandas as pd
import numpy as np


MAPPING_PATH = './db_rfv_mapping.csv'

class DisplayCSV(MatrixBase):
    def __init__(self, *args, **kwargs):
        super(DisplayCSV, self).__init__(*args, **kwargs)

    def run(self):
        offset_canvas = self.matrix.CreateFrameCanvas()
        # loop
        
        df_mapping = pd.read_csv(MAPPING_PATH, dtype=str)
        df_mapping = df_mapping.reset_index()  # make sure indexes pair with number of rows
                
        print(df_mapping.head(5))
        
        
        current_x = 0
        current_y = 0

        for index, row in df_mapping.iterrows():
            if df_mapping.at[index, 'leds']
            
                
                
                
                

                

                
            
           

# Main function
if __name__ == "__main__":
    simple_square = DisplayCSV()
    if (not simple_square.process()):
        simple_square.print_help()


    

