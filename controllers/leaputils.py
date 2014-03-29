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