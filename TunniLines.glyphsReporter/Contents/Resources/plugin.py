# encoding: utf-8
import objc
import sys, os, re
import math

from GlyphsApp import *
from GlyphsApp.plugins import *
import glyphmonkey

def _halfway(p1, p2):
  return NSPoint((p1.x+p2.x)/2, (p1.y+p2.y)/2)

class TunniLines (ReporterPlugin):
  def settings(self):
    self.menuName = "Tunni Lines"

  def foreground(self, Layer):
    try:
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
            if s.tunni_point:
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
            if px:
              displayText = NSAttributedString.alloc().initWithString_attributes_( '%0.1f%%' % (100*px), fontAttributes )
              displayText.drawAtPoint_alignment_( displayText, _halfway(s.start, s.handle1), 4 )
            if py:
              displayText = NSAttributedString.alloc().initWithString_attributes_( '%0.1f%%' % (100*py), fontAttributes )
              displayText.drawAtPoint_alignment_( displayText, _halfway(s.handle2, s.end), 4 )


    except Exception as e:
      import traceback
      print traceback.format_exc()
