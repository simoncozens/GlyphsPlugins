#!/usr/bin/env python
# encoding: utf-8
import objc
from Foundation import *
from AppKit import *
import sys, os, re
import math

MainBundle = NSBundle.mainBundle()
path = MainBundle.bundlePath() + "/Contents/Scripts"
if not path in sys.path:
	sys.path.append( path )

import GlyphsApp

GlyphsReporterProtocol = objc.protocolNamed( "GlyphsReporter" )

class ShowPathArea ( NSObject, GlyphsReporterProtocol ):
	
	def init( self ):
		return self

	def interfaceVersion( self ):
		return 1

	def title( self ):
		return "Path Area"

	def keyEquivalent( self ):
		return None

	def modifierMask( self ):
		return 0

	def drawForegroundForLayer_( self, Layer ):
		pass

	def drawPathArea( self, Layer ):
		Glyph = Layer.parent
		Font = Glyph.parent
		selectedLayers = Font.selectedLayers

		for thisLayer in selectedLayers:
			for thisPath in thisLayer.paths:
				if thisPath.closed:
					area = 0
					for s in thisPath.segments:
						area += self.segmentArea(s)
					self.drawTextAtPoint( u"%d" % abs(area), (thisPath.nodes[0].position.x - 5, thisPath.nodes[0].position.y + 5) )

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

	def drawBackgroundForLayer_( self, Layer ):
		try:
			self.drawPathArea( Layer )
		except Exception as e:
			self.logToConsole( "drawBackgroundForLayer_: %s" % str(e) )

	def drawBackgroundForInactiveLayer_( self, Layer ):
		pass

	def drawTextAtPoint( self, text, textPosition, fontSize=10.0, fontColor=NSColor.colorWithCalibratedRed_green_blue_alpha_( 1, 0, .5, 1 ) ):
		"""
		Use self.drawTextAtPoint( "blabla", myNSPoint ) to display left-aligned text at myNSPoint.
		"""
		try:
			glyphEditView = self.controller.graphicView()
			currentZoom = self.getScale()
			fontAttributes = { 
				NSFontAttributeName: NSFont.labelFontOfSize_( fontSize/currentZoom ),
				NSForegroundColorAttributeName: fontColor }
			displayText = NSAttributedString.alloc().initWithString_attributes_( text, fontAttributes )
			textAlignment = 2 # top left: 6, top center: 7, top right: 8, center left: 3, center center: 4, center right: 5, bottom left: 0, bottom center: 1, bottom right: 2
			glyphEditView.drawText_atPoint_alignment_( displayText, textPosition, textAlignment )
		except Exception as e:
			self.logToConsole( "drawTextAtPoint: %s" % str(e) )
	
	def needsExtraMainOutlineDrawingForInactiveLayer_( self, Layer ):
		return True

	def getHandleSize( self ):
		"""
		Returns the current handle size as set in user preferences.
		Use: self.getHandleSize() / self.getScale()
		to determine the right size for drawing on the canvas.
		"""
		try:
			Selected = NSUserDefaults.standardUserDefaults().integerForKey_( "GSHandleSize" )
			if Selected == 0:
				return 5.0
			elif Selected == 2:
				return 10.0
			else:
				return 7.0 # Regular
		except Exception as e:
			self.logToConsole( "getHandleSize: HandleSize defaulting to 7.0. %s" % str(e) )
			return 7.0

	def getScale( self ):
		"""
		self.getScale() returns the current scale factor of the Edit View UI.
		Divide any scalable size by this value in order to keep the same apparent pixel size.
		"""
		try:
			return self.controller.graphicView().scale()
		except:
			self.logToConsole( "Scale defaulting to 1.0" )
			return 1.0
	
	def setController_( self, Controller ):
		"""
		Use self.controller as object for the current view controller.
		"""
		try:
			self.controller = Controller
		except Exception as e:
			self.logToConsole( "Could not set controller" )
	
	def logToConsole( self, message ):
		"""
		The variable 'message' will be passed to Console.app.
		Use self.logToConsole( "bla bla" ) for debugging.
		"""
		myLog = "Show %s plugin:\n%s" % ( self.title(), message )
		NSLog( myLog )
