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


TRAVEL COST AUCH BEI GETEILTEN BAHNHÖFEN MIND. 1 SONST DIVISION DURCH 0 ERROR

Hauptstrecken:
X Hamburg - Hannover
X Hamburg - Dortmund - Hagen - Köln
X Hannover - Dortmund
X Dortmund - Duisburg - Köln
X Hannover - Berlin
X Fulda - Nürnberg
X Hannover - Frankfurt
X Göttingen - Wolfsburg
X Hanau - Würzburg
X Fulda - Erfurt
X Berlin - Halle - Erfurt
X Bitterfeld - Leipzig - Erfurt
X Erfurt - Nürnberg
X München - Nürnberg
X Köln - Montabaur - Frankfurt
X Frankfurt - Stuttgart - München
X Karlsruhe - Vaihingen
X Hamburg - Berlin (gerade gesperrt)
X Mannheim - Basel 

Nebenstrecken:

X Hamburg - Westerland
X Hamburg - Padborg - Kopenhagen - Malmö
X Hamburg - Kiel
X Hamburg - Lübeck
- Hamburg - Rostock - Stralsund - Ostseebad Binz
X Uelzen - Stendal 
- Berlin - Rostock - Warnemünde
X Stendal - Ludwigslust
- Ludwigslust - Rostock
X Hannover - Braunschweig - Leipzig
X Magdeburg - Stendal 
X Magdeburg - Berlin
- Berlin - Stralsund
- Berlin - Frankfurt (Oder)
- Berlin - Dresden - Prag
- Leipzig - Dresden
- Leipzig - Jena - Nürnberg
- Erfurt - Gera
- Erfurt - Kassel 
- Nürnberg - Passau - Wels - Linz
- München - Salzburg - Bischofshofen - Graz
X München - Kufstein - Wörgl
X München - Seefeld - Innsbruck
X München - Lindau - Bregenz - Zürich
X Ulm - Lindau - Bregenz - Feldkirch - Innsbruck
X Basel - Zürich
X Augsburg - Nürnberg
X Augsburg - Ansbach - Würzburg
X Nürnberg - Ansbach - Stuttgart
X Karlsruhe - Pforzheim - Stuttgart
X Karlsruhe - Paris
X Mannheim - Saarbrücken - Paris
X Frankfurt - Weinheim
X Weinheim - Mannheim
X Weinheim - Heidelberg
X Mannheim - Heidelberg
X Heidelberg - Vaihingen
X Heidelberg - Bruchsal
X Mannheim - Mainz - Koblenz - Bonn - Köln
X Mainz - Wiesbaden - Limburg Süd
X Frankfurt - Mainz
X Frankfurt - Gießen - Kassel
X Köln - Aachen - Brüssel
X Duisburg - Oberhausen
X Oberhausen - Utrecht 
X Oberhausen - Gelsenkirchen - Münster
X Essen - Gelsenkirchen
X Dortmund - Paderborn - Kassel
X Hannover - Osnabrück - Rheine - Amsterdam
X Münster - Rheine - Leer
X Hannover - Bremen - Leer
X Leer - Norddeich(Mole)
X Ulm - Oberstdorf
X Augsburg - Oberstdorf 
X Stuttgart - Zürich
X Strasbourg - Lyon
- Salzburg - Wels
X Feldkirch - Zürich
- Lübeck - Puttgarden - Kopenhagen (wenn irgendwann fertig in 10 Jahren)
X Duisburg - M'gladbach - Aachen 
X Düsseldorf - M'gladbach - Aachen 

ungepixelte Strecken:
- Berlin - Cottbus (IC zählt als RE)
- Dresden - Chemnitz (IC zählt als RE)
- München - Berchtesgarden (keine Züge)
- Stuttgart - Tübingen (nur 1 IC pro Tag)
- Stuttgart - Tuttlingen (nur 1 IC pro Tag, der nicht als RE zählt)
- Offenburg - Konstanz (nur 1 ICE pro Tag im Sommer)
- Koblenz - Luxemburg (keine Züge)
- Dortmund - Siegen - Frankfurt (Zug zählt als RE)




# Next Steps
X neue Farben: Grün, Gelb, Rot, Lila
X Echtzeitupdateunterstützung auf neue Stops und Ersatzfahrten erweitern
-> neue Stops bei bekannter Id: aus anderem Stop die category und number ziehen, Rest aus den fchg Daten nehmen
-> neue Stops bei unbekannter Id: Wenn kein Trip Label -> keine Ersatzfahrt sondern Regionalverkehr, skippen / Wenn Trip Label -> prüfen auf Fernverkehr, wenn kein Fernverkehr, skippen / wenn Fernverkehr, neuen Stop mit category und number aus dem Trip Label und id aus dem fchg stop anlegen
- Nodes in PixelStudio festlegen
- ggf. nochmal Pixeling überarbeiten
- Stück für Stück alle Strecken zu Stations, Stretches, Stretch-Segments und LED Mapping hinzufügen.
- Focus Mode: Ein Zug alleine auf der Map, planned path highlighted in der Farbe des Zugtyps in dunkel, Position des Zugs hell. 4 Stück, die nacheinander gezeigt werden für jeweils 30 Sekunden. Wenn über env Variablen eine Kategorie + Zugnummer gesetzt ist, wird das genommen, wenn nicht wird zufällig ein aktuell fahrender Zug ausgewählt. Ist der gesetzte Zug nicht auffindbar, wird auch automatisch ein anderer ausgewählt


## Infrastruktur Refactoring

- Mappings aus dem animation Ordner in die einzelnen Ordner verschieben
- Animationscode so anpassen, dass sie immer eine LED und eine Farbe beinhalten, alles dafür in den jeweiligen Ordnern berechnen
- Webserver bauen, der die animationcode files auf routes verfügbar macht
- Alles so bauen, dass man einfach ein zweites stretch_segments und mapping für eine andere LED Dimension oder Darstellung machen könnte und dafür dann auch die animationcodes berechnet werden und unter eigenen routes exposed werden
- de/db/rnv Ordner => Server
- animation Ordner => Client
- Server berechnet alle x Minuten / Sekunden immer die animationcodes und hält die Dateien lokal aktuell, jedes Mal wenn der Client etwas anzeigen will (z.B. alle 15 Sekunden), fragt der Client die entsprechenden neuen Animationcodes (LED + Farbe) an, der Server schickt dann einfach den aktuellen State des jeweiligen Files zurück
- Ausprobieren, ob der Raspi Pico ausreicht für das Powern des Displays, ansonsten entweder Server mieten oder alten Raspberry von Manuel als Server umfunktionieren mit Fritzbox VPN


# Rejected Improvements
- Trails
-> Trails werden nicht implementiert weil 
1. um die Trails zu implementieren, müsste man wissen, welche LED zuletzt geleuchtet hat. Das geht nicht über primary und secondary LED im mapping, weil man dann auf dem ersten Segment eines Stretches nicht weiß, von welchem Stretch der Zug kommt. Es geht nicht durch Speichern der letzten berechneten LED, weil es bei sehr schnellen Zügen oder Änderungen in der Verspätung sein kann, dass ein Zug innerhalb eines Ticks mehr als eine LED weiter oder sogar zurück wandert.
Die einzige Möglichkeit wäre es, alle LEDs, die im Laufe der Fahrt beleuchtet werden, für jeden Trip in ein DF zu schreiben und von der aktuellen LED einen zurück zu gehen. Das ist aber 1. nicht so geil zu implementieren und noch viel wichtiger sehr rechenaufwendig, weil man für jede Fahrt zwischen zwei Halten den shortest Path im Graphen berechnen muss und dann die Stretches, Segmente und LEDs lookupen muss. Und das wird bei > 400 aktiven Trips gleichzeitig mit jeweils 5 - 30 Halten viel zu lange dauern, bzw. nicht so schnell gehen, dass es den Informationszuwachs rechtfertigen würde, weil während der Berechnung das Display auch noch flackert.
