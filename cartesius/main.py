# -*- coding: utf-8 -*-

import Image as mod_image
import ImageDraw as mod_imagedraw

import utils as mod_utils

DEFAULT_AXES_COLOR = ( 150, 150, 150 )
DEFAULT_LABEL_COLOR = ( 150, 150, 150 )
DEFAULT_GRID_COLOR = ( 235, 235, 235 )
DEFAULT_ELEMENT_COLOR = ( 0, 0, 0 )

# Possible label positions:
LEFT_UP       = -1, 1
LEFT_CENTER   = -1, 0
LEFT_DOWN     = -1, -1
CENTER_UP     = 0, 1
CENTER        = 0, 0
CENTER_DOWN   = 0, -1
RIGHT_UP      = 1, 1
RIGHT_CENTER  = 1, 0
RIGHT_DOWN    = 1, -1


class Bounds:
	"""
	Bounds for coordinate system and image size. If the user don't explicitly set hiw own bounds, those
	will be resized with each new element.
	"""

	image_width = None
	image_height = None

	left = None
	right = None
	bottom = None
	top = None

	def __init__( self, left = None, right = None, bottom = None, top = None, image_width = None, image_height = None ):
		self.reset()

		self.left = left
		self.right = right
		self.bottom = bottom
		self.top = top

		if self.bottom != None and self.top != None:
			assert self.bottom < self.top, 'Bottom bound ({0}) greater than top bound ({1})'.format( self.bottom, self.top )
		if self.left != None and self.right != None:
			assert self.left < self.right, 'Left bound ({0}) greater than right bound ({1})'.format( self.left, self.right )

		self.image_width = image_width
		self.image_height = image_height

	def get_width_height( self ):
		assert self.left != None
		assert self.right != None
		assert self.bottom != None
		assert self.top != None
		assert self.right > self.left
		assert self.top > self.bottom

		return self.right - self.left, self.top - self.bottom

	def reset( self ):
		self.left_bound, self.right_bound, self.lower_bound, self.upper_bound = None, None, None, None

	def update_to_image_size( self ):
		assert self.image_width
		assert self.image_height

		width, height = self.get_width_height()

		desired_width_height_ratio = self.image_width / float( self.image_height )

		if desired_width_height_ratio < width / float( height ):
			desired_height = width / desired_width_height_ratio
			self.bottom = self.bottom - ( desired_height - height ) / 2
			self.top = self.top + ( desired_height - height ) / 2
		else:
			desired_width = height * desired_width_height_ratio
			self.left = self.left - ( desired_width - width ) / 2
			self.right = self.right + ( desired_width - width ) / 2

	def update( self, bounds = None, x = None, y = None, point = None ):
		if point != None:
			assert len( point ) == 2
			x = point[ 0 ]
			y = point[ 1 ]

		if x != None:
			self.left, self.right = mod_utils.min_max( x, self.left, self.right )
		if y != None:
			self.bottom, self.top = mod_utils.min_max( y, self.bottom, self.top )

		if bounds:
			self.update( x = bounds.left, y = bounds.top )
			self.update( x = bounds.right, y = bounds.bottom )

		if self.bottom != None and self.top != None:
			assert self.bottom <= self.top
		if self.left != None and self.right != None:
			assert self.left <= self.right

	def is_set( self ):
		return self.left != None and self.right != None and self.bottom != None and self.top != None

	def __str__( self ):
		return '[bounds:{0},{1},{2},{3}, image:{4},{5}]'.format( self.left, self.right, self.bottom, self.top, self.image_width, self.image_height )

class CoordinateSystem:

	elements = None

	bounds = None

	# x axis element:
	x_axis = None

	# y axis element:
	y_axis = None

	resize_bounds = None

	def __init__( self, bounds = None ):
		""" If custom bounds are given, they won't be resized according to new elements. """
		import elements as mod_elements
		self.elements = []

		# Set default bounds
		if bounds:
			if isinstance( bounds, Bounds ):
				self.bounds = bounds
				self.resize_bounds = False
			else:
				assert len( bounds ) == 4, 'Bounds must be a 4 element tuple/list'
				self.bounds = Bounds( left = bounds[ 0 ], right = bounds[ 1 ], bottom = bounds[ 2 ], top = bounds[ 3 ] )
				self.resize_bounds = False
		else:
			self.bounds = Bounds()
			self.resize_bounds = True

		# By default, axes are on:
		self.x_axis = mod_elements.Axis( horizontal = True, points = 1 )
		self.y_axis = mod_elements.Axis( vertical = True, points = 1 )

	def add( self, element ):
		"""
		Add element on coordinate system.

		Note that if you add n default axis, it will remove a previous existing horizontal/vertical axis,
		but the same does not apply for detached axes.
		"""
		import elements as mod_elements
		assert element
		assert isinstance( element, CoordinateSystemElement )

		if isinstance( element, mod_elements.Axis ):
			if element.is_detached():
				self.elements.append( element )
			else:
				if element.is_horizontal():
					self.x_axis = element
				else:
					self.y_axis = element
		else:
			element.reload_bounds()
			self.elements.append( element )
			self.reload_bounds()

	def reload_bounds( self ):
		if not self.resize_bounds:
			return

		if not self.elements:
			self.bounds.left = -1
			self.bounds.right = 1
			self.bounds.bottom = -1
			self.bounds.top = 1
			return

		for element in self.elements:
			self.bounds.update( element.bounds )

		assert self.bounds

	def __draw_elements( self, image, draw, antialiasing_coef = None, hide_x_axis = False, hide_y_axis = False ):
		for element in self.elements:
			element.draw( image = image, antialiasing_coef = antialiasing_coef, draw = draw, bounds = self.bounds )

		if not hide_x_axis and self.x_axis:
			self.x_axis.draw( image = image, antialiasing_coef = antialiasing_coef, draw = draw, bounds = self.bounds )

		if not hide_y_axis and self.y_axis:
			self.y_axis.draw( image = image, antialiasing_coef = antialiasing_coef, draw = draw, bounds = self.bounds )

	def draw( self, width, height, axis_units_equal_length = True, hide_x_axis = False, hide_y_axis = False,
			antialising = None ):
		""" Returns a PIL image """

		antialiasing_coef = 1
		if antialising:
			antialiasing_coef = float( antialising )
			width = int( width * antialiasing_coef )
			height = int( height * antialiasing_coef )

		self.bounds.image_width = width
		self.bounds.image_height = height

		if axis_units_equal_length:
			self.reload_bounds()

		image = mod_image.new( 'RGBA', ( width, height ), ( 255, 255, 255, 255 ) )
		draw = mod_imagedraw.Draw( image )

		if self.resize_bounds:
			self.bounds.update_to_image_size()

		self.__draw_elements( image = image, draw = draw, antialiasing_coef = antialiasing_coef, hide_x_axis = hide_x_axis, hide_y_axis = hide_y_axis )

		if antialising:
			image = image.resize( ( int( width / antialiasing_coef ), int( height / antialiasing_coef ) ), mod_image.ANTIALIAS )

		return image

class CoordinateSystemElement:
	""" Abstract class, every subclass should detect bounds and have the code to draw this item """

	bounds = None
	transparency_mask = None

	def __init__( self, transparency_mask = None ):
		self.bounds = Bounds()

		self.transparency_mask = transparency_mask if transparency_mask else 255

	def reload_bounds( self ):
		""" Will be called after the element is added to the coordinate system """
		raise Error( 'Not implemented in {0}'.format( self.__class__ ) )
	
	def process_image( self, image, draw, bounds, antialiasing_coef ):
		""" Will be called after the element is added to the coordinate system """
		raise Error( 'Not implemented in {0}'.format( self.__class__ ) )

	def get_color_with_transparency( self, color ):
		""" Use this to get color with appropriate transparency taken from this element. """
		if not color:
			return None

		assert len( color ) >= 3

		return ( color[ 0 ], color[ 1 ], color[ 2 ], self.transparency_mask )

	def draw( self, image, draw, bounds, antialiasing_coef ):
		if self.transparency_mask == 255:
			tmp_image, tmp_draw = image, draw
		else:
			tmp_image = mod_image.new( 'RGBA', ( bounds.image_width, bounds.image_height ) )
			tmp_draw = mod_imagedraw.Draw( tmp_image )

		self.process_image( tmp_image, tmp_draw, bounds, antialiasing_coef )

		if tmp_image != image or tmp_draw != draw:
			image.paste( tmp_image, mask = tmp_image )
