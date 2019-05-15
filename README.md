# polycalc

### Create AutoCAD polylines from line table data

This tool allows the user to create a command file from line table data. 
The command file can then be processed to create AutoCAD LW polylines. 
A typical line table looks like ... 

![alt text](https://raw.githubusercontent.com/chasmack/polycalc/master/data/line-table.jpg "PM1241 sheet 3/3 detail")

As a line table can contain many dozens of lines it can be error prone to enter 
the line and curve data interactively. The command file approach has a few advantages.

* Command files can be easily checked against the original data 
* Processing lists derived segment values and flags non-tangent curves
* Use of polylines ensures all segments are continuous

### Command language

Each line of a command file describes one segment or auxiliary operation. 
Blank lines and lines starting with a hash (#) are ignored. A list of polylines 
and a coordinate stack are maintained as the command file is processed. New segments 
are added to the current polyline, 
i.e. the last polyline in the polyline list. Each command starts with an arbitrary id 
and subsequent command elements are separated by space. The command id and subsequent 
command elements can contain no spaces. 

See the `linedata-demo` and associated parcel maps in the `data` directory for 
an example. 

### Commands

`<id> BEGIN <x> <y>`  
Start a new polyline at the specified x/y coordinates.

`<id> <quadrant> <bearing> <distance>`  
Add a line segment.  
Quadrants are 1-NE 2=SE 3=SW 4=NW, bearing is in DMS (DD.MMSS). 

`<id> <direction> <delta> <radius>`  
Add a curve tangent to previous segment.  
Dierction is L=Left R=Right, delta is in DMS (DDD.MMSS). 

`<id> <direction> <delta> <radius> <quadrant> <bearing>`  
Add a non-tangent curve segment.  
Quadrant and bearing is for the radial from the BC (Begin Curve) to the RP (Radial Point). 

`<id> PUSH`  
Push the last coordinate in the current polyline onto the coordinate stack. 
The current polyline is not affected. 

`<id> POP`  
Pop the last coordinate from the coordinate stack and start a new polyline. 

`<id> UNDO`  
Remove the last segment from the current polyline. 
