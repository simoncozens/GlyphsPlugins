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
import glyphmonkey

GlyphsReporterProtocol = objc.protocolNamed( "GlyphsReporter" )

def _halfway(p1, p2):
  return NSPoint((p1.x+p2.x)/2, (p1.y+p2.y)/2)

class TunniLines ( NSObject, GlyphsReporterProtocol ):
  
  def init( self ):
    if glyphmonkey.__file__ and not hasattr(glyphmonkey.GSCurveSegment, "tunni_point"):
      print("Tunni Lines plugin will not work without Glyphmonkey library version 1.1")
      print("Ensure library in " + glyphmonkey.__file__ + " is updated to latest")
      return None
    return self

  def interfaceVersion( self ):
    return 1

  def title( self ):
    return "Tunni Lines"

  def keyEquivalent( self ):
    return None

  def modifierMask( self ):
    return 0

  def drawForegroundForLayer_( self, Layer ):
    try:
      glyphEditView = self.controller.graphicView()
      currentZoom = self.getScale()
      if currentZoom < 2.0:
        col = NSColor.colorWithCalibratedRed_green_blue_alpha_(0,0,1.0,currentZoom-1.0)
      else:
        col = NSColor.blueColor()
      col.set()
      fontAttributes = {
        NSFontAttributeName: NSFont.labelFontOfSize_( 10/currentZoom ),
        NSForegroundColorAttributeName: col
      }

      for p in Layer.paths:
        for s in p.segments:
          if len(s) == 4 and currentZoom > 1.0:
            bez = NSBezierPath.bezierPath()
            bez.setLineWidth_(0)
            bez.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_(s.tunni_point, self.getHandleSize() / (2*self.getScale()),0,359)
            bez.stroke()
            bez.closePath()

            bez.setLineDash_count_phase_([1.0,1.0], 2,0)
            bez.moveToPoint_(s.handle1)
            bez.lineToPoint_(s.handle2)
            bez.stroke()

            px, py = s.curvature_percentages
            displayText = NSAttributedString.alloc().initWithString_attributes_( '%0.1f%%' % (100*px), fontAttributes )
            glyphEditView.drawText_atPoint_alignment_( displayText, _halfway(s.start, s.handle1), 4 )
            displayText = NSAttributedString.alloc().initWithString_attributes_( '%0.1f%%' % (100*py), fontAttributes )
            glyphEditView.drawText_atPoint_alignment_( displayText, _halfway(s.handle2, s.end), 4 )


    except Exception as e:
      self.logToConsole( "drawForegroundForLayer_: %s" % str(e) )

  def drawBackgroundForLayer_( self, Layer ):
        pass

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
