animationcodes follow the format
`trip_category`:`statuscode`#`primaryColor`_`secondaryColor`

trip_category is used to determine which statuscode_led_mapping to use, e.g. RNV, DB_NV, DB_FV  
statuscode is the value under which the status can be found in the respective mapping   
primaryColor and secondaryColor are the colors which are used to light the primary and secondary LEDs which are specified in the mapping



# IDEAS
1. Straßenbahnen Richtungsinvariant implementieren => Hbf Süd als 4272 für alle Steige statt 427234 / 427202 / 427201 / 427211 / 427212
2. Stop times im preprocess_static filtern nach ids, deren services tatsächlich auch am heutigen Tag verkehren, um den Rechenaufwand zu verringern
3. Live DB Timetable updates



# heidelberg-train-monitor
@reboot sleep 20; sudo bash /home/robin/Documents/github/heidelberg-train-monitor/scriptwrappers/preprocess_static_wrapper.bash >> /home/robin/cronlogs/htm_preprocess_static.log 2>&1
0 0,6,12,18 * * * sudo bash /home/robin/Documents/github/heidelberg-train-monitor/scriptwrappers/preprocess_static_wrapper.bash >> /home/robin/cronlogs/htm_preprocess_static.log 2>&1
* * * * * sudo bash /home/robin/Documents/github/heidelberg-train-monitor/scriptwrappers/rnv_compute_animationcodes_wrapper.bash >> /home/robin/cronlogs/htm_rnv_codes.log 2>&1
* * * * * sudo bash /home/robin/Documents/github/heidelberg-train-monitor/scriptwrappers/db_compute_animationcodes_wrapper.bash >> /home/robin/cronlogs/htm_db_codes.log 2>&1
* * * * * sleep 15; sudo bash /home/robin/Documents/github/heidelberg-train-monitor/scriptwrappers/db_compute_animationcodes_wrapper.bash >> /home/robin/cronlogs/htm_db_codes.log 2>&1
* * * * * sleep 30; sudo bash /home/robin/Documents/github/heidelberg-train-monitor/scriptwrappers/db_compute_animationcodes_wrapper.bash >> /home/robin/cronlogs/htm_db_codes.log 2>&1
* * * * * sleep 45; sudo bash /home/robin/Documents/github/heidelberg-train-monitor/scriptwrappers/db_compute_animationcodes_wrapper.bash >> /home/robin/cronlogs/htm_db_codes.log 2>&1
@reboot sleep 20; sudo bash /home/robin/Documents/github/heidelberg-train-monitor/scriptwrappers/display_animationcodes_wrapper.bash >> /home/robin/cronlogs/htm_display_codes.log 2>&1



Sprinterstrecken:
- Hamburg - Essen
- Köln - Berlin (über Hannover, Hagen ohne Halt)
- Frankfurt - Berlin (über Hannover, Fulda ohne Halt)
- Berlin - Nürnberg (pber Erfurt, Halle ohne Halt)

Hauptstrecken:
- Hamburg - Hannover
- Hamburg - Berlin
- Hamburg - Dortmund
- Hannover - Dortmund - Duisburg - Köln
- Hannover - Dortmund - Hagen - Köln
- Hannover - Berlin
- Hannover - Nürnberg
- Hannover - Frankfurt
- Göttingen - Wolfsburg
- Frankfurt - Nürnberg
- Frankfurt - Erfurt
- Berlin - Halle - Erfurt
- Berlin - Leipzig - Erfurt
- Erfurt - Nürnberg
- München - Nürnberg
- Köln - Montabaur - Frankfurt
- Frankfurt - Basel 
- Frankfurt - Stuttgart - München
- Karlsruhe - Stuttgart (/Esslingen)

Nebenstrecken:

TODO



ungepixelte Strecken:
- Berlin - Cottbus (IC zählt als RE)
- Dresden - Chemnitz (IC zählt als RE)
- München - Berchtesgarden (keine Züge)
- Ulm - Oberstdorf (nur 1 IC pro Tag)
- Augsburg - Oberstdorf (nur 1 IC pro Tag)
- Stuttgart - Tübingen (nur 1 IC pro Tag)
- Stuttgart - Tuttlingen (nur 1 IC pro Tag, der nicht als RE zählt)
- Offenburg - Konstanz (nur 1 ICE pro Tag im Sommer)
- Koblenz - Luxemburg (keine Züge)
- Dortmund - Siegen - Frankfurt (Zug zählt als RE)
- Duisburg - M'gladbach - Aachen (1 Zug pro Tag)
- Düsseldorf - M'gladbach - Aachen (1 Zug pro Tag)