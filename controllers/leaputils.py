"""Utility functions to handle coordinates systems, etc"""

from Leap import Vector

CENTERED_ORIGIN = Vector(0, 200, 0)
MAX_X = 250
MAX_Y = 350
MAX_Z = 150

def rescale_position(old):
	"""
	Fit the given vector back into the centered coordinate system.
	Return a vector with coordinates values in [-1;1]
	"""
	# Translate
	new = old - CENTERED_ORIGIN
	# Scale
	new.x /= MAX_X
	new.y /= MAX_Y
	new.z /= MAX_Z
	return new

def to_color(position):
	"""
	Convert a position in Leap space to a color in the RGB cube.
	We use the subspace (0..250, 0..350, -50..0).
	The RGB components are scaled to [0..1]
	"""
	# Translate
	x = position.x
	y = position.y
	z = -position.z
	# Scale
	r = max(0, x / MAX_X)
	g = max(0, y / MAX_Y)
	b = max(0, z / MAX_Z)
	return r, g, b