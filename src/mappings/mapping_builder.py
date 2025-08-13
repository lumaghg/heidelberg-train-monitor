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
import platform
import sys


MAPPING_PATH = 'db_rfv_mapping.csv'

NO_PRIMARY_LEDS = 3
NO_SECONDARY_LEDS = 1

# Plattform erkennen
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import msvcrt

    def get_key():
        """Liest eine Taste unter Windows (ohne Enter)."""
        ch = msvcrt.getch()
        try:
            return ch.decode("utf-8").lower()
        except UnicodeDecodeError:
            return ""
else:
    import tty
    import termios

    def get_key():
        """Liest eine Taste unter Linux/Mac (ohne Enter)."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch.lower()

class DisplayCSV(MatrixBase):
    def __init__(self, *args, **kwargs):
        super(DisplayCSV, self).__init__(*args, **kwargs)

    def run(self):
        offset_canvas = self.matrix.CreateFrameCanvas()
        # loop

        df_mapping = pd.read_csv(MAPPING_PATH, dtype=str)
        
        current_x = 0
        current_y = 0

        for index, row in df_mapping.iterrows():
            readable_statuscode = row['readable']
            leds_primary = df_mapping.at[index, 'leds_primary']
            leds_secondary = df_mapping.at[index, 'leds_secondary']
            
            # skip already filled rows
            if not pd.isna(leds_primary) and not pd.isna(leds_secondary):
                continue


            def letUserInputPixels(is_primary, current_x, current_y):

                pixels = []
                
                no_pixels = NO_PRIMARY_LEDS if is_primary else NO_SECONDARY_LEDS
                mode = 'PRIMARY' if is_primary else 'SECONDARY'    
                    
                
                for i in range(no_pixels):
                    print(f"\n{readable_statuscode} {mode} ({i+1}/{NO_PRIMARY_LEDS}):\n")

                    print("Drücke W, A, S, D oder Enter. Mit Q beenden.")
                    while True:
                        key = get_key()
                        if key in ("w", "a", "s", "d"):
                            if key == "w":
                                current_x += 1
                            if key == "a":
                                current_y += 1
                            if key == "s":
                                current_x -= 1
                            if key == "d":
                                current_y -= 1
                            
                                
                            # display new pixel
                                
                        elif key in ("\r", "\n"):  # Enter
                            pixels.append(f"{current_x}-{current_y}")
                            print(f"added pixel {current_x}-{current_y} ")
                            break
                        
                        elif key == "q":
                            quit()
                            
                leds = '&'.join(pixels)
                if is_primary:
                    df_mapping.at[index, 'leds_primary'] = leds
                else:
                    df_mapping.at[index, 'leds_secondary'] = leds
                # primary leds
                
                return current_x, current_y
                
            current_x, current_y = letUserInputPixels(True, current_x, current_y)
            current_x, current_y = letUserInputPixels(False, current_x, current_y)
            df_mapping.to_csv('db_rfv_mapping.csv', index=False)    
                
                
                
                

                

                
            
           

# Main function
if __name__ == "__main__":
    simple_square = DisplayCSV()
    if (not simple_square.process()):
        simple_square.print_help()


    

