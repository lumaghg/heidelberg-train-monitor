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


Graph Update:

Knoten müssen sein
- Bahnhöfe, an denen Züge starten und enden
- Bahnhöfe, an denen sich Strecken kreuzen,

Alle Knoten müssen abgefragt werden

Alle Strecken zwischen zwei Knoten werden Kanten.

Die reguläre Fahrzeit einer Kante werden ihre Kosten.

Wo sich ein Zug befindet, wird durch folgende Schritte ermittelt:
1. Shortest Path zwischen dem vorherigen und aktuellen Bahnhof
2. Ermittlung der Gesamtkosten der Shortest Path
3. Ermittlung der relativen Kosten der Kanten des Shortest Path
3.5 Ermittlung der Zuordnung Zeitprozent (Start + Ende) -> Kante
4. Ermittlung der Zugposition auf dem Shortest Path in Zeitprozent
5. Ermittlung, auf welcher Kante der Zug ist durch Lookup in Tabelle aus 3.5
6. Durch Zugposition auf dem shortest path in % und Start / Ende Zeitprozent der Kante die relative Position in % auf der Kante bestimmen

Animation durch Tabelle aus kantenname, zeitprozent start + ende, LED primary, LED secondary
-> display.csv lookup anpassen


-> Das erste Kantensegment wird ohne Trails animiert, da nicht eindeutig ist, wo der Zug herkommt. Zusätzlich ist die Streckenführung im Knotenbereich oft etwas durcheinander, ist also nicht so unrealistisch abgebildet-
-> Entscheidung gegen die Variante, bei der der Zug ab der ersten Sekunde nach der Abfahrt mit der ersten LED außerhalb des Bahnhofs angezeigt wird, um das Animieren des Trails zu ermöglichen, da das bei nah aneinander liegenden Bahnhöfen zu Verwirrung führen würde.

-> Cost zwischen Haltestellen wird nicht automatisch berechnet sondern von gelookuped, weil es teilweise nachts oder mit IC/ICE Unterschied zu großen Schwankungen in einigen Abschnitten führt, da andere Strecken ausnahmsweise benutzt werden. Der reguläre Fall soll zur Animation verwendet werden. Und weil Spaß :)









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

- Hamburg - Westerland
- Hamburg - Padborg
- Hamburg - Kiel
- Hamburg - Lübeck - Puttgarden
- Hamburg - Rostock - Stralsund - Ostseebad Binz
- Hamburg - Stendal 
- Berlin - Rostock - Warnemünde
- Stendal - Rostock
- Hannover - Braunschweig - Leipzig
- Magdeburg - Stendal 
- Magdeburg - Berlin
- Berlin - Stralsund
- Berlin - Frankfurt (Oder)
- Berlin - Dresden - Prag
- Leipzig - Dresden
- Leipzig - Jena - Nürnberg
- Erfurt - Gera
- Erfurt - Kassel 
- Nürnberg - Passau - Linz
- München - Salzburg - Bischofshofen - Graz
- München - Kufstein - Wörgl
- München - Seefeld
- München - Lindau - Bregenz - Zürich
- Ulm - Lindau - Bregenz - Feldkirch
- Basel - Zürich
- Augsburg - Nürnberg
- Augsburg - Würzburg
- Nürnberg - Stuttgart
- Karlsruhe - Pforzheim - Stuttgart
- Karlsruhe - Paris
- Mannheim - Saarbrücken - Paris
- Frankfurt - Darmstadt - Mannheim
- Frankfurt - Darmstadt - Heidelberg - Stuttgart
- Mannheim - Heidelberg
- Mannheim - Ludwigshafen - Mainz - Koblenz - Bonn - Köln
- Frankfurt - Mainz - Wiesbaden - Siegburg - Köln
- Frankfurt - Gießen - Kassel
- Köln - Aachen - Brüssel
- Köln - Mönchengladbach - Utrecht
- Duisburg - Oberhausen - Utrecht 
- Duisburg - Oberhausen - Gelsenkirchen - Münster
- Essen - Gelsenkirchen - Münster 
- Dortmund - Paderborn - Kassel
- Münster - Rheine - Leer - Norddeich (Mole)
- Hannover - Osnabrück - Rheine - Amsterdam
- Hannover - Bremen - Leer - Norddeich (Mole)





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