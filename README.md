# polycalc

### Create AutoCAD polylines from line table data

This tool allows the user to create a command file from line table data 
which can then be processed into AutoCAD LW polylines. A typical 
line table looks like this ... 

![alt text](https://raw.githubusercontent.com/chasmack/polycalc/master/data/line-table.jpg "PM1241 sheet 3/3 detail")

As line table data can go on for dozens of lines it can be error prone to enter 
the line and curve data interactively. The command file approach has a few advantages.

* Command files can be easily checked against the original data 
* Processing lists derived segment values and flags non-tangent curves
* Use of polylines ensures all segments are continuous

### Command language

Each line of a command file describes one segment or auxiliary operation. 
Blank lines and lines starting with a hash (#) are ignored. A list of polylines 
and a coordinate stack are maintained. New segments are added to the last 
polyline in the polyline list. Each command starts an arbitrary id and subsequent 
command elements are separated by space. The command id and subsequent command elements 
can contain no spaces. 

#### Commands are ...

* `<id> BEGIN <x> <y>` - start a new polyline ar the specified coordinates.
* `<id> <quadrant> <bearing> <distance>` - add a line segment. Quadrants are 
1-NE 2=SE 3=SW 4=NW. Bearing is in DMS formatted as DD.MMSS.
* `<id> <direction> <delta> <radius>` - add a curve tangent to previous segment. 
Dierction is L=Left R=Right. Delta is in DMS as DDD.MMSS.
* `<id> <direction> <delta> <radius> <quadrant> <bearing>` - add a non-tangent curve 
segment. Quadrant and bearing are for the curve radial from the BC 
(begin curve, i.e. end of previous segment) to RP (radial point). 
* `<id> PUSH` - push the last coordinate onto the coordinate stack.
* `<id> POP` - pop the last coordinate from the coordinate stack and 
start a new polyline.
* `<id> UNDO` - remove the last segment from the polyline.

See the `linedata-demo` and associated parcel maps in the `data` directory for 
an example.
