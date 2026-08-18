#!/usr/bin/env python3
"""Every JEDEC P-number the simulator can honestly render as a page.

Source: the JEDEC P-number table in Wikipedia's "Phosphor" article, fetched
2026-08-17, plus Phosphor Technology Ltd's CRT phosphor table for the seven
rows with a MEASURED CIE point. Where both exist the measured point wins.

Fields: (key, name, pnum, composition, colour, xy or nm, persistence, decayMs,
         afterglow-nm or None, note)

`decayMs` is this repo's ladder for a class-only persistence, or the published
figure when there is one. The ladder (unchanged):
    very short 0.05   short 0.5   medium short 1
    medium    10      long 150    very long 1000
"""

# Already shipped by hand; listed so the generator can refuse to re-derive them.
SHIPPED = {"P1", "P3", "P4", "P7", "P11", "P22R", "P22B", "P31", "P39",
           "P45", "P47", "P56"}

# (pnum, name, composition, colour, source, persistence, decayMs, afterglow)
# source: ('xy', x, y) measured, or ('nm', peak), or ('mix', [(nm, weight)...])
TABLE = [
    ("P2",   "Blue-Green Long", "ZnS:Cu(Ag)", "Blue-Green",
     ('nm', 543), "Long", 150.0, None),
    ("P5",   "Blue Fastest", "CaWO4:W", "Blue",
     ('nm', 430), "Very Short", 0.05, None),
    ("P6",   "White TV", "ZnS:Ag+ZnS:CdS:Ag", "White",
     ('xy', 0.272, 0.290), "Short", 0.5, None),   # JEDEC white, cool side
    ("P10",  "Dark Trace", "KCl", "Green-absorbing scotophor",
     ('scotophor', None), "Long", 150.0, None),
    ("P12",  "Orange Persistent", "Zn(Mg)F2:Mn", "Orange",
     ('nm', 590), "Medium/long", 150.0, None),
    ("P13",  "Red-Orange", "MgSi2O6:Mn", "Reddish-Orange",
     ('nm', 640), "Medium", 10.0, None),
    ("P14",  "Cascade Orange", "ZnS:Ag on ZnS:CdS:Cu", "Blue with Orange persistence",
     ('mix', [(460, 0.7), (600, 0.3)]), "Medium/long", 150.0, 600),
    ("P15",  "Blue-Green Fastest", "ZnO:Zn", "Blue-Green",
     ('nm', 504), "Extremely Short", 0.05, None),
    ("P16",  "Violet", "CaMgSi2O6:Ce", "Blue-Purple",
     ('nm', 400), "Very Short", 0.05, None),
    ("P17",  "Cascade Yellow", "ZnO,ZnCdS:Cu", "Blue-Yellow",
     ('mix', [(460, 0.6), (575, 0.4)]), "Blue-Short, Yellow-Long", 150.0, 575),
    ("P18",  "White Soft", "CaMgSi2O6:Ti, BeSi2O6:Mn", "White",
     ('xy', 0.280, 0.300), "Medium to Short", 1.0, None),  # JEDEC white centre
    ("P19",  "Radar Orange", "(KF,MgF2):Mn", "Orange-Yellow",
     ('nm', 590), "Long", 150.0, None),
    ("P20",  "Terminal Green", "(Zn,Cd)S:Ag or (Zn,Cd)S:Cu", "Yellow-Green",
     ('nm', 555), "1-100 ms", 20.0, None),
    ("P21",  "Radar Red", "MgF2:Mn2+", "Reddish",
     ('nm', 605), "not published", 150.0, None),
    ("P22G", "TV Green", "(Zn,Cd)S:Cu,Al", "Green",
     ('nm', 530), "Short", 0.5, None),
    ("P23",  "White Warm", "ZnS:Ag+(Zn,Cd)S:Ag", "White",
     ('xy', 0.300, 0.315), "Short", 0.5, None),   # JEDEC white, warm side
    ("P24",  "VFD Green", "ZnO:Zn", "Green",
     ('nm', 505), "1-10 us", 0.05, None),
    ("P25",  "Orange Lead", "CaSi2O6:Pb:Mn", "Orange",
     ('nm', 610), "Medium", 10.0, None),
    ("P26",  "Radar Orange Long", "(KF,MgF2):Mn", "Orange",
     ('nm', 595), "Long", 150.0, None),
    ("P27",  "Red-Orange Deep", "ZnPO4:Mn", "Reddish Orange",
     ('nm', 635), "Medium", 10.0, None),
    ("P28",  "Yellow", "(Zn,Cd)S:Cu,Cl", "Yellow",
     ('nm', 578), "Medium", 10.0, None),
    ("P33",  "Radar Orange Longest", "MgF2:Mn", "Orange",
     ('nm', 590), "> 1 sec", 1000.0, None),
    ("P34",  "Storage Green", "not published", "Bluish Green-Yellow Green",
     ('nm', 520), "Very Long", 1000.0, None),
    ("P35",  "Blue-White", "ZnS,ZnSe:Ag", "Blue-White",
     ('xy', 0.250, 0.265), "Medium Short", 1.0, None),  # blue-white, off-JEDEC
    ("P38",  "Radar Amber", "(Zn,Mg)F2:Mn", "Orange-Yellow",
     ('nm', 590), "Long", 150.0, None),
    ("P40",  "White Long", "ZnS:Ag+(Zn,Cd)S:Cu", "White",
     ('xy', 0.286, 0.326), "Long", 150.0, None),  # JEDEC white corner C
    ("P43",  "Terbium Green", "Gd2O2S:Tb", "Yellow-Green",
     ('nm', 545), "Medium", 10.0, None),
    ("P46",  "Green Fastest", "Y3Al5O12:Ce", "Green",
     ('nm', 530), "Very short (70 ns)", 0.00007, None),
    ("P53",  "Projector Green", "Y3Al5O12:Tb", "Yellow-Green",
     ('nm', 544), "Short", 0.5, None),
    ("P55",  "Blue Projector", "ZnS:Ag,Al", "Blue",
     ('nm', 450), "Short", 0.5, None),
]
