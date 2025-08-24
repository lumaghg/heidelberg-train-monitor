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
7. Lookup des kantensegments in Tabelle aus Kantenzeitprozent Start + Ende, Kante, Segmentnr., LED
(8. Übersetzung des Gesamtpaths des Zuges aus den Stoptimes in eine Liste von Kantensegmenten (möglich, weil per Definition immer nur ganze Kanten befahren werden können und damit einfach alle Kantensegmente der jeweiligen Kante in die Liste hinzugefügt werden))
(9. Lookup der Trail LED durch herausfinden der ersten vorherigen Kantensegments, das eine andere LED hat.
10. Beleuchtung der LED(s)

-> Es gibt keine Trails an Startbahnhöfen einer Zugfahrt (Macht ja Sinn, der Zug kommt ja noch von nirgendwo :) )

-> Kanten müssen nur in eine Richtung definiert werden, bei der Suche nach dem Kantensegment in der Tabelle wird die Reihenfolge der beiden Knoten einfach umgedreht. In dem Falle wird dann die Kantenzeitprozentzahl reversed. Hamburg - Bremen 20% ist die gleiche Position wie Bremen - Hamburg 80%.
Convention: Kanten immer so herum festlegen, dass sie möglichst alle in einer Linie und Richtung liegen, damit das mapping nachher nicht so krampfig zu erstellen ist. 

-> So kann jetzt auch zuerst die Variante ohne Trails implementiert werden und die Trails in beliebiger Länge später hinzugefügt werden.

-> Cost zwischen Haltestellen wird nicht automatisch berechnet sondern von gelookuped, weil es teilweise nachts oder mit IC/ICE Unterschied zu großen Schwankungen in einigen Abschnitten führt, da andere Strecken ausnahmsweise benutzt werden. Der reguläre Fall soll zur Animation verwendet werden. Und weil Spaß :)




Sprinterstrecken:
- Hamburg - Essen
- Köln - Berlin (über Hannover, Hagen ohne Halt)
- Frankfurt - Berlin (über Hannover, Fulda ohne Halt)
- Berlin - Nürnberg (pber Erfurt, Halle ohne Halt)

Hauptstrecken:
- Hamburg - Hannover
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
- Hamburg - Berlin (gerade gesperrt)

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



# Next Steps
- Echtzeitupdateunterstützung auf neue Stops und Ersatzfahrten erweitern
- Nodes in PixelStudio festlegen
- ggf. nochmal Pixeling überarbeiten
- Stück für Stück alle Strecken zu Stations, Stretches, Stretch-Segments und LED Mapping hinzufügen.

# Optional Improvements
- Follow - Highlighting

# Rejected Improvements
- Trails
-> Trails werden nicht implementiert weil 
1. um die Trails zu implementieren, müsste man wissen, welche LED zuletzt geleuchtet hat. Das geht nicht über primary und secondary LED im mapping, weil man dann auf dem ersten Segment eines Stretches nicht weiß, von welchem Stretch der Zug kommt. Es geht nicht durch Speichern der letzten berechneten LED, weil es bei sehr schnellen Zügen oder Änderungen in der Verspätung sein kann, dass ein Zug innerhalb eines Ticks mehr als eine LED weiter oder sogar zurück wandert.
Die einzige Möglichkeit wäre es, alle LEDs, die im Laufe der Fahrt beleuchtet werden, für jeden Trip in ein DF zu schreiben und von der aktuellen LED einen zurück zu gehen. Das ist aber 1. nicht so geil zu implementieren und noch viel wichtiger sehr rechenaufwendig, weil man für jede Fahrt zwischen zwei Halten den shortest Path im Graphen berechnen muss und dann die Stretches, Segmente und LEDs lookupen muss. Und das wird bei > 400 aktiven Trips gleichzeitig mit jeweils 5 - 30 Halten viel zu lange dauern, bzw. nicht so schnell gehen, dass es den Informationszuwachs rechtfertigen würde, weil während der Berechnung das Display auch noch flackert.
