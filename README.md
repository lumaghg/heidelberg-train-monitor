animationcodes follow the format
`trip_category`:`statuscode`#`primaryColor`_`secondaryColor`

trip_category is used to determine which statuscode_led_mapping to use, e.g. RNV, DB_NV, DB_FV  
statuscode is the value under which the status can be found in the respective mapping   
primaryColor and secondaryColor are the colors which are used to light the primary and secondary LEDs which are specified in the mapping



# IDEAS
1. Straßenbahnen Richtungsinvariant implementieren => Hbf Süd als 4272 für alle Steige statt 427234 / 427202 / 427201 / 427211 / 427212
2. Stop times im preprocess_static filtern nach ids, deren services tatsächlich auch am heutigen Tag verkehren, um den Rechenaufwand zu verringern
3. Live DB Timetable updates