"""
	Author: William Garvey
	
	An Axis-Aligned Box Physics module that allows for the creation of Space, Entity and Concrete Objects.
	Entity and Concrete Objects are PhysObjs (Physics Objects) that exist and interract within
	the Space. A Concrete Objects may interract with Entity Objects but not other Concrete objects.
	An entity object may interract with other entity objects.
	
	Entity-Entity collision resolution works by applying an equal an opposite force related to a collision
	coefficient defined in the space and a bouncy coefficients between the entity objects.
	
	Entity-Concrete collision resolution works by first moving all physObjs in the X axis, and finding
	any collisions that occur, and if a collision has occured, move the entity in the opposite direction of 
	the entity objects velocity, relative to the concrete object. The same then happens with the Y axis.
"""

from enum import Enum
import math

# Allow for other space events to be added in future
class SpaceEventType(Enum):
	COLLISION = 1

class Axis(Enum):
	X = 0
	Y = 1
	
class CollisionEvent:
	# party_one/two are the two parties involved with the collision
	def __init__(self, party_one, party_two, collision_rect, axis):
		self.collision_rect = collision_rect # A square representing the overlap of the two hitboxes
		self.party_one = party_one
		self.party_two = party_two
		self.axis = axis # Axis of which collision took place
	
	def type(self):
		return SpaceEventType.COLLISION
		
	# returns true if one of the parties is a concrete
	def has_concrete(self): # 
		return isinstance(self.party_one, Concrete) or isinstance(self.party_two, Concrete)
	
	def has_entity(self):
		return isinstance(self.party_one, Entity) or isinstance(self.party_two, Entity)
	
	# in a combination of concrete and entity, returns the concrete party
	def get_concrete(self):
		if isinstance(self.party_one, Concrete):
			return self.party_one
		elif isinstance(self.party_two, Concrete):
			return self.party_two
		else:
			raise RuntimeError("No Concrete party when using get_concrete()")
			
	# in a combination of concrete and entity, returns the entity party		
	def get_entity(self):
		if isinstance(self.party_one, Entity):
			return self.party_one
		elif isinstance(self.party_two, Entity):
			return self.party_two
		else:
			raise RuntimeError("No Entity party when using get_entity()")


		
class Space:
	def __init__(self):
		self.events = []
		self.entities = []
		self.concretes = []
		self.axis_speed_limit = 100 # less than the length of the smallest square
		self.collision_coefficient = 3
		self.gravity = 0.3
		self.air_resistance = 0.3 # as a percentage of speed
	
	# get list of all physics objects
	def get_all(self):
		return self.entities + self.concretes
	
	# Adding new physics objects to the space
	# Sorry for the mix of camel case into this...
	def add_physObj(self, physObj):
		if isinstance(physObj, Entity):
			self.entities.append(physObj)
		elif isinstance(physObj, Concrete):
			self.concretes.append(physObj)
		physObj.space = self
	
	"""
		1. Translate forces applied to an entity to accelerations and then to chances in velocities
		2. If an entity and concrete are colliding BEFORE the update, mark the entity involved as as precollided
		3. Move all physObjs in the X according to their x_vel
		4. detect collisions between entities and concretes
		5. resolve in the X between for non-precollided entities and concretes 
		5. add the collision to the events list
		6. do the same for Y
	"""
	def update(self):
		# get rid of all events from previous update
		self.events = []
		# translate forces to accelerations to velocities
		self.resolve_forces()
		self.mark_precollisions() # mark any objects that are precollidede
		self.move_all_x() # attempt to move all objects in X, resolve any entity collisions
		self.move_all_y()
		self.search_for_entity_collisions()
		self.resolve_entity_collisions()
		self.apply_friction()
		self.apply_bouncy()
		self.custom_updates()
		
	""" 
	Execute at beginning of physics update to ensure there is NOT a pair consisting of
	a entity and a concrete that are colliding. (Entity-Entity collisions are permitted to collide)
	
	Each physics update collision's resolution works based off of the assumption that
	there are not unresolved collided entity-concrete collisions.
	"""
	def mark_precollisions(self):
		for entity in self.entities:
			if self.check_for_concrete_colliding(entity):
				entity.pre_collided = True
				entity.y -= 1
				print("precollision detected")
			else:
				entity.pre_collided = False
	
	# Apply the force of bouncy to objects
	# Bouncy is actually the RESISTANCE to the collision
	def apply_bouncy(self):
		for event in self.events:
			# entity-entity collision only
			if not event.has_concrete():
				entity1 = event.party_one
				entity2 = event.party_two
				# Bouncy is from 0 to 1, 1 being super bouncy AKA
				# No resistance
				resist_bouncy = 1 - entity1.bouncy*entity2.bouncy
				
				if event.axis == Axis.Y:
					rel_velocity_y = entity1.vel_y - entity2.vel_y
					entity1.apply_force(0,-resist_bouncy*rel_velocity_y)
					entity2.apply_force(0,resist_bouncy*rel_velocity_y)
				else:
					rel_velocity_x = entity1.vel_x - entity2.vel_x
					entity1.apply_force(-resist_bouncy*rel_velocity_x,0)
					entity2.apply_force(resist_bouncy*rel_velocity_x,0)
	
	# Friction as a force perpendicular to a collision, is NOT proportional to collision force.
	def apply_friction(self):
		# Sort through all events to find collision events and apply friction to the entities
		for event in self.events:
			# concrete-entity collision
			if event.has_concrete():
				entity = event.get_entity()
				friction = event.get_concrete().friction * entity.friction
				concrete = event.get_concrete()
				if event.axis == Axis.X:
					rel_velocity_y = entity.vel_y - concrete.vel_y
					entity.apply_force(0,-entity.mass*friction*rel_velocity_y)
				else: # Axis.Y
					rel_velocity_x = entity.vel_x - concrete.vel_x
					entity.apply_force(-entity.mass*friction*rel_velocity_x,0)
					
			# entity-entity collision
			else:
				# Equal and opposite to entity
				entity1 = event.party_one
				entity2 = event.party_two
				friction = entity1.friction*entity2.friction
				if event.axis == Axis.X:
					rel_velocity_y = entity1.vel_y - entity2.vel_y
					entity1.apply_force(0,-entity1.mass*friction*rel_velocity_y)
					entity2.apply_force(0,entity2.mass*friction*rel_velocity_y)
				else: # Axis.Y
					rel_velocity_x = entity1.vel_x - entity2.vel_x
					entity1.apply_force(-entity1.mass*friction*rel_velocity_x,0)
					entity2.apply_force(entity2.mass*friction*rel_velocity_x,0)
	
	# turn forces into accelerations via an objects mass (F = MA, A = F/M)
	# finallly add the accelerations to the velocities of the ojects
	def resolve_forces(self):
		# forces are only acted on by entities
		for entity in self.entities:
			# While we're here, might as well reset all these states
			entity.hit_down = False
			entity.hit_left = False
			entity.hit_right = False
			entity.hit_up = False
		
			# translate the force
			# =============================================================================== ENFORCE SPEED LIMITS!!! ================================
			# forces applied to object through apply_force()
			entity.vel_x += entity.force_x/entity.mass
			
			# air resistance as a function of the square of the velocity
			
			#air_resistance_vel_change = self.air_resistance*math.fabs(entity.vel_x)*entity.vel_x/entity.mass
			air_resistance_vel_change = entity.drag_coefficient*self.air_resistance*entity.vel_x/entity.mass
			
			# the power of air resistance is too powerful, aka, it would cause the object to fly BACKWARD
			# this is due the drag being to the square
			if math.fabs(entity.vel_x) < math.fabs(air_resistance_vel_change):
				entity.vel_x = 0
			else:
				entity.vel_x -= air_resistance_vel_change
			
			# y axis
			
			# forces applied to object through apply_force()
			entity.vel_y += entity.force_y/entity.mass
			
			# gravity applied to object
			entity.vel_y -= self.gravity
			
			# air resistance as a function of the square of the velocity
			#air_resistance_vel_change = self.air_resistance*math.fabs(entity.vel_y)*entity.vel_y/entity.mass
			air_resistance_vel_change = entity.drag_coefficient*self.air_resistance*entity.vel_y/entity.mass
			
			# the power of air resistance is too powerful, aka, it would cause the object to fly BACKWARD
			# this is due the drag being to the square
			if math.fabs(entity.vel_y) < math.fabs(air_resistance_vel_change):
				entity.vel_y = 0
			else:
				entity.vel_y -= air_resistance_vel_change
			
			speedlimitreached = False
			
			# x speed limit
			if entity.vel_x > self.axis_speed_limit:
				#print(" x force on me: ", entity.force_x, ", y force on me:", entity.force_y)
				#print("positive x speed limit reached : vel_x = ", entity.vel_x, ", after correct it is ", self.axis_speed_limit)
				entity.vel_x = self.axis_speed_limit
				speedlimitreached = True
				
			elif entity.vel_x < -self.axis_speed_limit:
				#print(" x force on me: ", entity.force_x, ", y force on me:", entity.force_y)
				#print("negative x speed limit reached", entity.vel_x, ", after correct it is ", self.axis_speed_limit)
				entity.vel_x = -self.axis_speed_limit
				speedlimitreached = True
				
			# y speed limit
			if entity.vel_y > self.axis_speed_limit:
				#print(" x force on me: ", entity.force_x, ", y force on me:", entity.force_y)
				#print("positive y speed limit reached", entity.vel_y, ", after correct it is ", self.axis_speed_limit)
				entity.vel_y = self.axis_speed_limit
				speedlimitreached = True
				
			elif entity.vel_y < -self.axis_speed_limit:
				#print(" x force on me: ", entity.force_x, ", y force on me:", entity.force_y)
				#print("negative y speed limit reached", entity.vel_y, ", after correct it is ", -self.axis_speed_limit)
				entity.vel_y = -self.axis_speed_limit
				speedlimitreached = True
			
			entity.force_x = entity.force_y = 0 # reset to 0
	
	# useful for sliding mechanics
	def would_collide_with_any_concrete(self, pos, hitbox):
		model_entity = Entity(pos, hitbox, 5)
		return self.check_for_concrete_colliding(model_entity)
	
	# attempt to move all objects in x
	# then resolve any collisions
	def move_all_x(self):
		# first move all concretes
		for concrete in self.concretes:
			concrete.x += concrete.vel_x
			
		for entity in self.entities:
			# move all entities in the x axis
			entity.x += entity.vel_x
			
			# ignore collisions for precollided entites
			if entity.pre_collided:
				continue
			
			# get all collided concretes
			collided_concretes = self.get_collided_concretes(entity)
			
			# no concretes that the entity collided with? great, move on to next entity
			if len(collided_concretes) == 0:
				continue
			
			# get the max overlap in the x
			sig_concrete, collision_rect = self.get_max_collision_rect_x(entity, collided_concretes)
			
			velocity_difference = entity.vel_x - sig_concrete.vel_x
			
			if velocity_difference > 0:
				entity.hit_left = True
			else:
				entity.hit_right = True
		
			# add collision event to list
			self.add_collision_event(entity, sig_concrete, collision_rect, Axis.X)
			
			# move back in opposite direction of the relative velocity of the entity to the collided concrete 
			entity.x -= math.copysign(collision_rect[0] , velocity_difference)
			entity.vel_x = sig_concrete.vel_x
	
	def add_collision_event(self, party_one, party_two, collision_rect, axis):
		self.events.append(CollisionEvent(party_one, party_two, collision_rect, axis))

			
	# attempt to move all objects in y
	# then resolve any collisions
	def move_all_y(self):
		# first move all concretes
		for concrete in self.concretes:
			concrete.y += concrete.vel_y
			
		for entity in self.entities:
			# move all entities in the y axis
			entity.y += entity.vel_y
			
			# ignore collisions for precollided entites
			if entity.pre_collided:
				continue
			
			# get all collided concretes
			collided_concretes = self.get_collided_concretes(entity)
			
			# no concretes that the entity collided with? great, move on
			if len(collided_concretes) == 0:
				continue
			
			# get the max overlap in the x
			sig_concrete, collision_rect = self.get_max_collision_rect_y(entity, collided_concretes)
			
			# ========================== IF YOU WANNA ADD COLLISION EVENT STUFF ADD IT HERE =========================================================
			
			velocity_difference = entity.vel_y - sig_concrete.vel_y
			
			if velocity_difference > 0:
				entity.hit_up = True
			else:
				entity.hit_down = True
			
			# add collision event to list
			self.add_collision_event(entity, sig_concrete, collision_rect, Axis.Y)
			
			# move back in opposite direction of the relative velocity of the entity to the collided concrete 
			entity.y -= math.copysign(collision_rect[1] , velocity_difference)
			entity.vel_y = sig_concrete.vel_y
			
			# apply frictional force
	
	# get a list of all concretes that this entity is collided with
	def get_collided_concretes(self, entity):
		collided_concretes = []
		for concrete in self.concretes:
			if entity.is_collided_with(concrete):
				collided_concretes.append(concrete)
		return collided_concretes
		
	# gets the concrete of largest collision AND the collision rect
	# only considers the x overlap
	# must be given at least one concrete
	# returns (concrete, collision_rect)
	def get_max_collision_rect_x(self, entity, collided_concretes):
		max_x_collision_rect = entity.get_collision_rec(collided_concretes[0])
		max_x_concrete = collided_concretes[0]
		for concrete in collided_concretes:
			collision_rect = entity.get_collision_rec(concrete)
			if collision_rect[0] > max_x_collision_rect[0]:
				max_x_collision_rect = collision_rect
				max_x_concrete = concrete
		return (max_x_concrete, max_x_collision_rect)
			
	# gets the concrete of largest collision AND the collision rect
	# only considers the y overlap
	# must be given at least one concrete
	# returns (concrete, collision_rect)
	def get_max_collision_rect_y(self, entity, collided_concretes):
		max_y_collision_rect = entity.get_collision_rec(collided_concretes[0])
		max_y_concrete = collided_concretes[0]
		for concrete in collided_concretes:
			collision_rect = entity.get_collision_rec(concrete)
			if collision_rect[1] > max_y_collision_rect[1]:
				max_y_collision_rect = collision_rect
				max_y_concrete = concrete
		return (max_y_concrete, max_y_collision_rect)
			
	# returns true if entity collides with any concretes in spcae
	def check_for_concrete_colliding(self, entity):
		for concrete in self.concretes:
			if entity.is_collided_with(concrete):
				return True
		return False
	
	# execute any custom physics scripts during each update
	def custom_updates(self):
		for physObj in self.get_all():
			physObj.custom_script()
	
	def search_for_entity_collisions(self):
		for i in range(len(self.entities)):
			for j in range(i, len(self.entities)):
				entity1 = self.entities[i]
				entity2 = self.entities[j]
				# double check to make sure we're not comparing the SAME entity
				if entity1 is not entity2 and not self.already_compared(entity1, entity2):
					if entity1.is_collided_with(entity2):
						collision_rect = entity1.get_collision_rec(entity2)
						# add collision event to list
						# ternary if statement
						axis = Axis.Y
						if collision_rect[1] > collision_rect[0]:
							axis = Axis.X
						self.add_collision_event(entity1, entity2, collision_rect, axis)
	
	def already_compared(self, entity1, entity2):
		for event in self.events:
			both = (event.party_one, event.party_two)
			if entity1 in both and entity2 in both:
				return True
		return False
	
	# push apart things
	def resolve_entity_collisions(self):
		for event in self.events:
			if event.type() == SpaceEventType.COLLISION:
				if isinstance(event.party_one, Entity) and isinstance(event.party_two, Entity):
					self._resolve_entity_entity(event)
	
	# entities resolve collisions with other entities via forces
	# don't forget equal and opposite!
	def _resolve_entity_entity(self,collision_event):
		# provide a force proportional to the overlap distance
		collision_rect = collision_event.collision_rect
		
		# x axis has a larger collision length
		if collision_rect[0] < collision_rect[1]:
			# apply force on x axis
			left = right = None # establish scope
			if collision_event.party_one.x < collision_event.party_two.x:
				left = collision_event.party_one
				right = collision_event.party_two
			else:
				right = collision_event.party_one
				left = collision_event.party_two
			# apply equal and opposite on x axis square 
			left.apply_force(-1 * (collision_rect[0]**1)*self.collision_coefficient, 0)
			right.apply_force((collision_rect[0]**1)*self.collision_coefficient, 0)
		
		# y axis has larger collision length
		else:
			higher_y = lower_y = None # establish scope
			if collision_event.party_one.y < collision_event.party_two.y:
				lower_y = collision_event.party_one
				higher_y = collision_event.party_two
			else:
				higher_y = collision_event.party_one
				lower_y = collision_event.party_two
			# apply equal and opposite on x axis
			lower_y.apply_force(0, -1*(collision_rect[1]**1)*self.collision_coefficient)
			higher_y.apply_force(0, (collision_rect[1]**1)*self.collision_coefficient)
		
		
class PhysObj:
	def __init__(self,pos,hitbox):
		self._prev_pos = pos#previous updates position, avoid round off errors
		self.x = pos[0]
		self.y = pos[1]
		self.vel_x = 0
		self.vel_y = 0
		self.hitbox = hitbox
		self.coefficient_friction = 0.5# nonzero value
		self.space = None
		
	def set_pos(self, x, y):
		self._prev_pos = (self.x,self.y)
		self.x = x
		self.y = y
		
	
	def get_pos(self):
		return (self.x, self.y)
		
	def get_hitbox(self):
		return self.hitbox
	
	# Returns true if this PhysObj is currently intersecting the other PhysObj
	def is_collided_with(self, other):
		return do_hitboxes_collide(self.get_pos(), self.hitbox, other.get_pos(), other.hitbox)
	
	def get_collision_rec(self, other):
		return get_collision_rect(self.get_pos(), self.hitbox, other.get_pos(), other.hitbox)
		

"""
An entity object interracts in the world and other entities. It may NOT pass through
concrete objects HOWEVER a glitch in physics may allow the Entity to walk through the 
resulting in a precollision.
"""
class Entity(PhysObj):
	def __init__(self,pos,hitbox, mass):
		PhysObj.__init__(self,pos,hitbox)
		self.mass = mass
		self.pre_collided = False
		self.force_x = 0
		self.force_y = 0
		
		# sliding friction
		self.friction = 0.5
		
		# coefficient to represent air resistance of object, from 0 < x < 1
		self.drag_coefficient = 0.5
		
		# 1 means no resistance to bouncing on an entity-entity collision
		self.bouncy = 0
		
		# useful things for setting jump conditions, it describes the state of the entity
		# and whether or not it has hit something
		self.hit_down = False
		self.hit_left = False
		self.hit_right = False
		self.hit_up = False
	
	def grounded(self):
		return self.hit_down
		
	def apply_force(self, x, y):
		self.force_x += x
		self.force_y += y
		
	def custom_script(self):
		pass
		
	
class Concrete(PhysObj):
	def __init__(self,pos,hitbox):
		PhysObj.__init__(self,pos,hitbox)
		self.friction = 0.1
		
	def custom_script(self):
		pass

# Get the dimensions of hitbox at a position overlapping 
# Another hitbox at a position
# ---WARNING--- 
# DUE TO LACK OF PRECISION OF FLOATING POINT NUMBERS, a small value is added on
# This is to ensure that the physics that uses this overlap as a correction, it will apply the correct
# position transformation. In other words, when an entity collides with a concrete, it will be resolved
# by getting the collision rectangle. It will use this collisionrectangle to move the entity back, before the collision.
def get_collision_rect(pos1, hitbox1, pos2, hitbox2):
    hitbox1_width = hitbox1[0]
    hitbox1_height = hitbox1[1]

    hitbox2_width = hitbox2[0]
    hitbox2_height = hitbox2[1]

    minimum_dist_x = hitbox1_width + hitbox2_width
    minimum_dist_y = hitbox1_height + hitbox2_height

    actual_dist_x = (hitbox1_width + hitbox2_width) / 2 + math.fabs(
        (0.5 * hitbox1_width + pos1[0]) - (0.5 * hitbox2_width + pos2[0]))
    actual_dist_y = (hitbox1_height + hitbox2_height) / 2 + math.fabs(
        (0.5 * hitbox1_height + pos1[1]) - (0.5 * hitbox2_height + pos2[1]))

    x_overlap = minimum_dist_x - actual_dist_x
    y_overlap = minimum_dist_y - actual_dist_y
	
    return (x_overlap + 0.01, y_overlap + 0.01)

# takes two objects with the fields:
#	sprite: Surface
# 	pos: (int/float, int/float)
# see ref A in purple book
def do_hitboxes_collide(pos1, hitbox1, pos2, hitbox2):
    # addition of the widths and heights to show the minimum distance they both can be
    # (either can be less but BOTH must be less to show they MUST be overlaping
    width1 = hitbox1[0]
    height1 = hitbox1[1]
    width2 = hitbox2[0]
    height2 = hitbox2[1]

    rec1_x = pos1[0]
    rec1_y = pos1[1]
    rec2_x = pos2[0]
    rec2_y = pos2[1]

    return rec1_x < rec2_x + width2 and \
           rec1_x + width1 > rec2_x and \
           rec1_y < rec2_y + height2 and \
           height1 + rec1_y > rec2_y

def same_sign(num1, num2):
	return (num1 < 0 and num2 < 0) or (num1 > 0 and num2 > 0) or (num1 == 0 and num2 == 0)
