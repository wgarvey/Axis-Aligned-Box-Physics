"""
	Author: William Garvey
	Showcase the Space Module using Pygame
"""
import pygame
import math
from Space import *

pygame.init()
pygame.display.init()

window = pygame.display.set_mode((1200, 800))
clock = pygame.time.Clock()
open_window = True

# Create Space and configure
space = Space()
space.gravity = -0.25
space.collision_coefficient = 2

# Create physics objects 
player_entity = Entity((200,250), (50,50), 5)
space.entities.append(player_entity)

# Create concrete map
space.add_physObj(Concrete((100,500),(900,100)))
space.add_physObj(Concrete((900,100),(100,400)))

# Add moving concrete
moving_concrete = Concrete((300,100),(100,100))
moving_concrete.vel_x = 1
moving_concrete.friction = 1
space.add_physObj(moving_concrete)

# Concrete pyramid
space.add_physObj(Entity((500,300),(50,50),10)) # Bottom
space.add_physObj(Entity((570,300),(50,50),10)) # Bottom
space.add_physObj(Entity((640,300),(50,50),10)) # Bottom
space.add_physObj(Entity((530,230),(50,50),10)) # Mid Row
space.add_physObj(Entity((610,230),(50,50),10)) # Mid Row
space.add_physObj(Entity((560,170),(50,50),10)) # Top

# Create 
entity2 = Entity((200,250), (30,30), 5)
entity2.vel_x = -1.5

entity3 = Entity((200,100), (30,30), 5)
entity3.vel_x = -1.5

entity4 = Entity((200,0), (30,30), 5)
entity4.vel_x = -1.5


def draw_rect(physObj):
	rect_pos = physObj.get_pos()
	rect_dimensions = physObj.get_hitbox()

	rect = pygame.Rect(rect_pos, rect_dimensions)
	
	# rect(Surface, color, Rect, width=0) -> Rect
	if type(physObj) == Concrete:
		pygame.draw.rect(window,(255,0,0), rect, 2)
	else:
		pygame.draw.rect(window,(0,0,255), rect, 2)


# ^^^ ======= SPACE CODE ========== ^^^
frame_rate = 60
while open_window:
	window.fill((0,0,0))
	# All pygame events
	for event in pygame.event.get():
		# Check for quitting
		if event.type == pygame.QUIT:
			open_window = False
			
	# Control player entity movement
	keys = pygame.key.get_pressed()
	if keys[pygame.K_UP]:
		player_entity.apply_force(0,-4)
	if keys[pygame.K_LEFT]:
		player_entity.apply_force(-2,0)
	if keys[pygame.K_RIGHT]:
		player_entity.apply_force(2, 0)
	
	# Modify frame rate
	if keys[pygame.K_w]:
		frame_rate+=5
	if keys[pygame.K_s]:
		frame_rate-=5
	
	# Move concrete object back and forth
	if (moving_concrete.x > 600):
		moving_concrete.vel_x = -1
	elif (moving_concrete.x < 200):
		moving_concrete.vel_x = 1
	
	# Draw all physObjs
	for physObj in space.get_all():
		draw_rect(physObj)
	
	# Update physics, screen and clock delay
	space.update()
	pygame.display.update()
	clock.tick(frame_rate)
	
	
	
	