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

NO_PRIMARY_LEDS = 1
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
    
    
    
    
# prepare base_overlay
base_overlay = np.full((64,32), "000000")

# backgrund lighting
df_background_lighting = pd.read_csv('../background/background_lighting.csv', dtype=str)

df_background_lighting = df_background_lighting.reset_index()  # make sure indexes pair with number of rows

for index, row in df_background_lighting.iterrows():
    led = row['led']
    color_hex = row['color']
    
    x = int(led.split("-")[0])
    y = int(led.split("-")[1])
    
    base_overlay[x,y] = color_hex
    
    
    

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
            if not pd.isna(leds_primary) or not pd.isna(leds_secondary):
                continue


            def letUserInputPixels(is_primary, current_x, current_y, offset_canvas):

                pixels = []
                
                no_pixels = NO_PRIMARY_LEDS if is_primary else NO_SECONDARY_LEDS
                mode = 'PRIMARY' if is_primary else 'SECONDARY'    
                    
                
                for i in range(no_pixels):
                    print(f"\n{readable_statuscode} {mode} ({i+1}/{NO_PRIMARY_LEDS}):\n")

                    print("Drücke W, A, S, D oder Enter. Mit Q beenden.")
                    while True:
                        key = get_key()
                        if key in ("w", "a", "s", "d"):
                            if key == "w" and current_x > 0:
                                current_x -= 1
                            if key == "s" and current_x < 63:
                                current_x += 1
                            if key == "d" and current_y > 0:
                                current_y -= 1
                            if key == "a" and current_y < 31:
                                current_y += 1
                                
                            #print(current_x, current_y)
                            overlay = base_overlay.copy()
                            # current pixel
                            overlay[int(current_x), int(current_y)] = "FFFFFF"
                            
                            for x in range(overlay.shape[0]):
                                for y in range(overlay.shape[1]):
                                    color_hex = overlay[x,y]                    
                                    color_rgb = ImageColor.getcolor(f"#{color_hex}", "RGB")
                                    offset_canvas.SetPixel(int(x), int(y), color_rgb[0], color_rgb[1], color_rgb[2])   
                            offset_canvas = self.matrix.SwapOnVSync(offset_canvas)
                            
                            
                                
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
                
            current_x, current_y = letUserInputPixels(True, current_x, current_y, offset_canvas)
            current_x, current_y = letUserInputPixels(False, current_x, current_y, offset_canvas)
            df_mapping.to_csv(MAPPING_PATH, index=False)    
            print('\n\n')
                
                
                
                

                

                
            
           

# Main function
if __name__ == "__main__":
    simple_square = DisplayCSV()
    if (not simple_square.process()):
        simple_square.print_help()


    

