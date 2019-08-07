# Axis-Aligned-Box-Physics

Python Version 3+

## Test
Test requires pygame
```
pip install pygame
```

To run SpaceTest.pyw:
```
SpaceTest.pyw
```

Use arrow keys to manipulate a box.

## Description
An Axis-Aligned Box Physics module that allows for the creation of Space, Entity and Concrete Objects.
Entity and Concrete Objects are PhysObjs (Physics Objects) that exist and interract within
the Space. A Concrete Objects may interract with Entity Objects but not other Concrete objects.
An entity object may interract with other entity objects.
	
Entity-Entity collision resolution works by applying an equal but opposite force related to a collision
coefficient defined in the space and a bouncy coefficients between the entity objects.
	
Entity-Concrete collision resolution works by first moving all physObjs in the X axis, and finding
any collisions that occur, and if a collision has occured, move the entity in the opposite direction of 
the entity objects velocity, relative to the concrete object. The same then happens with the Y axis.
