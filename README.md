# polycalc

### Create AutoCAD polylines from line table data

This tool allows the user to create a command file from line table data. 
The command file can then be processed to create AutoCAD LW polylines. 
A typical line table looks like this ... 

![alt text](https://raw.githubusercontent.com/chasmack/polycalc/master/data/line-table.jpg "PM1241 sheet 3/3 detail")

As a line table may contain many dozens of lines it can be error prone to enter 
the line and curve data interactively. The command file approach has a few advantages.

* Command files can be easily checked against the original line table data 
* Command file processing lists derived segment values and flags non-tangent curves
* Use of polylines ensures all segments are contiguous

### Command language

Each line of a command file describes one segment or auxiliary operation. 
Blank lines and lines starting with a hash (#) are ignored. A list of polylines 
and a points list are maintained as the command file is processed. New segments 
are added to the current polyline, 
i.e. the last polyline in the list of polylines. Each non-comment line consists a 
command (case-insensitive) followed by zero or more parameters separated by space.

### Commands

`BEGIN <point_id>`  
`BEGIN <northing> <easting>`  
Start a new polyline at the specified point or coordinates.

`POINT <point_id> LAST <description>`  
`POINT <point_id> <northing> <easting> <description>`  
Save the last ployline endpoint or specified coordinates in the points list.  
`<point_id>` is case insensitive and can contain no spaces. The `<description>` is optional.

`<quadrant> <bearing> <distance>`  
Add a line segment. `<quadrant>` is 1=NE, 2=SE, 3=SW, 4=NW.  
`<bearing>` is in Degrees-Minutes-Seconds (DD.MMSS). 

`<direction> <delta> <radius>`  
Add a curve tangent to previous segment. `<direction>` is L=Left, R=Right.  
`<delta>` is in Degrees-Minutes-Seconds (DDD.MMSS). 

`<direction> <delta> <radius> <quadrant> <bearing>`  
Add a non-tangent curve segment. Radial `<quadrant>`/`<bearing>` is from BC to RP. 

`<deflection> <delta> <distance>`  
Add a line segment using a deflection angle. `<deflection>` is DL=Left, DR=Right.  
`<delta>` is in Degrees-Minutes-Seconds (DDD.MMSS). 

`BRANCH` - Start a new polyline from the endpoint of the current polyline. 

`RESUME` - Resume with the polyline prior to last `BRANCH`. 

`UNDO` - Remove the last segment from the current polyline. 

`CLOSE <point_id>` - Calculate closure from endpoint of current polyline to specified point. 

### Listing

Processing of the line data produces a listing showing commands and 
derived line and curve data. Non-tangent segments following a curve are flagged. 
A PNEZD list of points is included at the bottom of the listing. 

### Example

See `linedata-demo.txt` and parcel map `PM1241` in the `data` directory for an example. 

```
# Alderpoint Rd
# PM1241 sheet 2/3 and line table sheet 3/3.

# Begin on east edge R/W at line 18
POINT 1 1929390.126 6074201.714 CALC_RW_PM1241
BEGIN 1
4 73.1430 25.00

# Radial calculated from line 17 for non-tangent curve
R 65.5030 150.00 2 73.1430
1 82.3600 76.56

# Road B PM1241 detail D
POINT XN_ROAD_B LAST

# Alderpoint Rd PM1241 line 20
L 42.0200 270.00
1 40.3400 108.71

# Property line parcels 1 & 2 PM1241 detail A
R 10.1240 220.00
BRANCH
2 39.1320 25.00
POINT 2 LAST CACL_RW_PAR_1+2_PM1241
RESUME

# Alderpoint Rd PM1241 line 23
R 15.0705 220.00
1 65.5345 103.79
R 14.5330 330.00

# South edge R/w
DR 90.0000 25.00
POINT 3 LAST CALC_RW_PM1241

# Road B PM1241 detail D
BEGIN XN_ROAD_B
2 7.2400 26.03
L 24.5315 90.00
2 32.1715 25.64
L 61.2515 65.00
1 86.1730 253.50

# Road B PM1241 detail A
R 6.4415 150.00
POINT RB06A LAST
R 11.4045 150.00
2 75.1730 26.19
POINT RB07A LAST
2 75.1730 30.40

# Property line parcels 1 & 2 PM1241 detail A
BEGIN 2
2 15.0000 290.24
CLOSE RB06A

# Fence line PM1241 details A & C
BEGIN RB07A
2 10.3620 136.38
POINT 4 LAST CALC_PL_PAR_1+2_PM1241
3 60.1110 55.91
POINT 5 LAST CALC_PL_PAR_1+2_PM1241
2 15.5230 354.22
1 81.5415 223.83
1 61.2510 157.32
2 85.0245 301.26
3 4.3135 180.94
3 18.1330 112.14
BRANCH
2 65.5800 112.66
RESUME
3 18.1330 77.21
```

![alt text](https://raw.githubusercontent.com/chasmack/polycalc/master/data/linedata-demo.jpg "PM1241 portion")

