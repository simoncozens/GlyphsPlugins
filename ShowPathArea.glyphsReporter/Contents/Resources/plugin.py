# encoding: utf-8
import objc
import sys, os, re
import math

from GlyphsApp import *
from GlyphsApp.plugins import *

class ShowPathArea(ReporterPlugin):
	def settings(self):
		self.menuName = "Path Area"

	def drawPathArea( self, Layer ):
		for thisPath in Layer.paths:
			if thisPath.closed:
				area = 0
				for s in thisPath.segments:
					area += self.segmentArea(s)
				self.drawTextAtPoint( u"%d" % abs(area), (thisPath.nodes[0].position.x - 5, thisPath.nodes[0].position.y + 5), fontColor=NSColor.colorWithCalibratedRed_green_blue_alpha_( 1, 0, .5, 1 ))

	def segmentArea(self, s):
		if len(s) == 4:
			xa, ya = s[0].x, s[0].y/20
			xb, yb = s[1].x, s[1].y/20
			xc, yc = s[2].x, s[2].y/20
			xd, yd = s[3].x, s[3].y/20
		else:
			xa, ya = s[0].x, s[0].y/20
			xb, yb = xa, ya
			xc, yc = s[1].x, s[1].y/20
			xd, yd = xc, yc
		return (xb-xa)*(10*ya + 6*yb + 3*yc +   yd) + (xc-xb)*( 4*ya + 6*yb + 6*yc +  4*yd) +(xd-xc)*(  ya + 3*yb + 6*yc + 10*yd)

	def foreground( self, Layer ):
		try:
			self.drawPathArea( Layer )
		except Exception as e:
			import traceback
			print traceback.format_exc()
	
	def inactiveLayerForeground(self, Layer): # this will only be called in 2.5-1120 and higher
		try:
			self.drawPathArea( Layer )
		except Exception as e:
			import traceback
			print traceback.format_exc()
	
	def needsExtraMainOutlineDrawingForInactiveLayer_( self, Layer ):
		return True

	def getScale( self ):
		"""
		self.getScale() returns the current scale factor of the Edit View UI.
		Divide any scalable size by this value in order to keep the same apparent pixel size.
		"""
		try:
			return self.controller.graphicView().scale()
		except:
			import traceback
			print traceback.format_exc()
			return 1.0
	
	def setController_( self, Controller ):
		"""
		Use self.controller as object for the current view controller.
		"""
		try:
			self.controller = Controller
		except Exception as e:
			self.logToConsole( "Could not set controller" )

