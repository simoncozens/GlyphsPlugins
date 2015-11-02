#!/usr/bin/env python
# encoding: utf-8
import objc
from Foundation import *
from AppKit import *
import sys, os, re
from Quartz import CGContextGetCTM, CGAffineTransformInvert, CGContextConcatCTM, CGContextRestoreGState, CGContextSaveGState

MainBundle = NSBundle.mainBundle()
path = MainBundle.bundlePath() + "/Contents/Scripts"
if not path in sys.path:
	sys.path.append( path )

import GlyphsApp
import glyphmonkey
from glyphmonkey import GSNodeSet

GlyphsReporterProtocol = objc.protocolNamed( "GlyphsReporter" )

class ShowSymmetries ( NSObject, GlyphsReporterProtocol ):
	
	def init( self ):
		bundle = NSBundle.bundleForClass_(ShowSymmetries)
		self.rotational = bundle.imageForResource_("rotational")
		self.reflectional = bundle.imageForResource_("reflectional")
		self.reflecty = bundle.imageForResource_("reflecty")
		return self

	def interfaceVersion( self ):
		return 1

	def title( self ):
		return "Symmetries"

	def keyEquivalent( self ):
		return None

	def modifierMask( self ):
		return 0

	def drawForegroundForLayer_( self, Layer ):
		pass

	def drawSymmetries( self, Layer ):
		currentZoom = self.getScale()
		l = Layer.copy()
		if l.pathCount() > 1:
			l.removeOverlap()
		ns = l.selectedNodeSet()
		if len(ns) == 1: return
		if len(ns) == 0:
			sel = []
			for p in Layer.paths:
				for n in p.nodes:
					sel.append(n)
			ns = GSNodeSet(sel)

		ox, oy = ns.center

		height = self.controller.view().bounds().size.height
		width = self.controller.view().bounds().size.width
		context = NSGraphicsContext.currentContext().CGContext()
		oldat = CGContextGetCTM(context)
		CGContextSaveGState(context)
		inverted = CGAffineTransformInvert(oldat)
		CGContextConcatCTM(context, inverted)

		if ns.equal(ns.copy().rotate(angle=180, ox=ox, oy=oy)):
			self.rotational.drawInRect_(NSMakeRect(width-125,height-(15+25),25,25))

		if ns.equal(ns.copy().reflect()):
			self.reflectional.drawInRect_(NSMakeRect(width-95,height-(15+25),25,25))

		if ns.equal(ns.copy().reflect(NSMakePoint(ox,oy), NSMakePoint(ox+100,oy))):
			self.reflecty.drawInRect_(NSMakeRect(width-65,height-(15+25),25,25))

		CGContextConcatCTM(context, oldat)
		CGContextRestoreGState(context)

	def drawBackgroundForLayer_( self, Layer ):
		try:
			self.drawSymmetries( Layer )
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
