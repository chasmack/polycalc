# polycalc

### Create AutoCAD polylines from line table data

This tool allows the user to create a command file from line table data. 
The command file can then be processed to create AutoCAD LW polylines. 
A typical line table looks like this ... 

![alt text](https://raw.githubusercontent.com/chasmack/polycalc/master/data/line-table.jpg "PM1241 sheet 3/3 detail")

As a line table can contain many dozens of lines it can be error prone to enter 
the line and curve data interactively. The command file approach has a few advantages.

* Command files can be easily checked against the original line table data 
* Command file processing lists derived segment values and flags non-tangent curves
* Use of polylines ensures all segments are contiguous

### Command language

Each line of a command file describes one segment or auxiliary operation. 
Blank lines and lines starting with a hash (#) are ignored. A list of polylines 
and a coordinate stack are maintained as the command file is processed. New segments 
are added to the current polyline, 
i.e. the last polyline in the polyline list. Each command starts with an arbitrary id 
and subsequent command elements are separated by space. The command id and subsequent 
command elements can contain no spaces. 

### Commands

`<id> BEGIN <northing> <easting>` - Start a new polyline at the specified x/y coordinates.

`<id> <quadrant> <bearing> <distance>` - Add a line segment.  
Quadrants are 1=NE, 2=SE, 3=SW, 4=NW. Bearing is in Degrees-Minutes-Seconds (DD.MMSS). 

`<id> <direction> <delta> <radius>` - Add a curve tangent to previous segment.  
Direction is L=Left, R=Right. Delta is in Degrees-Minutes-Seconds (DDD.MMSS). 

`<id> <direction> <delta> <radius> <quadrant> <bearing>` - Add a non-tangent curve segment.  
Radial quadrant and bearing are from the BC (Begin Curve) to the RP (Radial Point). 

`<id> <deflection> <delta> <distance>` - Add a line segment using a deflection angle.  
Deflection is DL=Left, DR=Right. Delta is in Degrees-Minutes-Seconds (DDD.MMSS). 

`<id> STORE <northing> <easting>` - Store a coordinate in the coordinate list as `<id>`.  
The current polyline is not affected. 

`<id> STORE` - Store the last coordinate in the current polyline in the coordinate list as `<id>`. 

`<id> RECALL` - Start a new polyline from the saved coordinate `<id>`. 

`<id> BRANCH` - Start a new polyline from the endpoint of the current polyline. 

`<id> RESUME` - Resume with the polyline prior to last `BRANCH`. 

`<id> UNDO` - Remove the last segment from the current polyline. 

`<id> CLOSE` - Calculate closure from endpoint of current polyline to saved coordinate `<id>`. 

### Example

See the `linedata-demo` and parcel map `PM1241` in the `data` directory for 
an example. 

```
# Portion of Alderpoint Road per PM1241. See line table sheet 3.
# Begin on right edge-of-right of way at the end of segment #17
AP00 BEGIN 1929390.126 6074201.714
APXX 4 73.1430 25.00
# Radial calculated from segment #17 for non-tangent curve
AP18 R 65.5030 150.00 2 73.1430
AP19 1 82.3600 76.56
# Intersection Road B per Detail D
RB00 BRANCH
RB01 2 7.2400 26.03
RB02 L 24.5315 90.00
RB03 2 32.1715 25.64
RB04 L 61.2515 65.00
RB05 1 86.1730 253.50
RB06A R 6.4415 150.00
# Intersection Road B and PL
RB06A STORE
RB06B R 11.4045 150.00
RB07A 2 75.1730 26.19
# Intersection Road B and fence line
RB07A STORE
RB07B 2 75.1730 30.40
# Resume along Alderpoint Rd.
AP19 RESUME
AP20 L 42.0200 270.00
AP21 1 40.3400 108.71
AP22 R 10.1240 220.00
# Intersection property line parcels 1 & 2
PL00 BRANCH
PL01 2 39.1320 25.00
PL02 2 15.0000 290.24
RB06A CLOSE
# Resume along Alderpoint Rd.
AP22 RESUME
AP23 R 15.0705 220.00
AP24 1 65.5345 103.79
AP25 R 14.5330 330.00
# Right to the edge of right-of-way
APXX DR 90.0000 25.00
# Fence line
RB07A RECALL
FL01 2 10.3620 136.38
FL02 3 60.1110 55.91
FL03 2 15.5230 354.22
```

![alt text](https://raw.githubusercontent.com/chasmack/polycalc/master/data/linedata-demo.jpg "PM1241 portion")

