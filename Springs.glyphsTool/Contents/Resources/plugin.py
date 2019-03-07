# encoding: utf-8

###########################################################################################################
#
#
# Select Tool Plugin
#
# Read the docs:
# https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/SelectTool
#
#
###########################################################################################################

from GlyphsApp import *
from GlyphsApp.plugins import *
from TTSolver import TTSolver, DIAGONAL, PROPORTIONAL_TRIPLE, PROPORTIONAL_QUAD
import sys
import traceback
from singleConstraintViewController import SingleConstraintViewController

GlyphsReporterProtocol = objc.protocolNamed( "GlyphsReporter" )

class Springs(SelectTool):
  constraining = False
  solver = TTSolver()

  def settings(self):
    self.name = "Springs"
    Glyphs.addCallback(self.drawGlyphIntoBackground, DRAWBACKGROUND)

  def start(self):
    pass

  def _rebuild(self):
    try:
      if len(Glyphs.font.selectedLayers) == 0:
        return
      l = Glyphs.font.selectedLayers[0]
      self.__class__.solver.initialSetup(l)
      self.__class__.solver.setConstraintsFromHints(l)
      self.__class__.solver.updateSolverFromGlyph()
    except:
      pass # may happen if tab is closed

  def activate(self):
    NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, objc.selector(self.update,signature='v@:'), "GSUpdateInterface", None)
    self._rebuild()
    pass

  def verifyHint(self,t):
    if t.type != TAG:
      return True # Pass through other people's hints
    if not t.originNode or not t.targetNode:
      return False
    if t.options == PROPORTIONAL_TRIPLE and not t.otherNode1:
      return False
    if t.options == PROPORTIONAL_QUAD and (not t.otherNode1 or not t.valueForKey_("otherNode2")):
      return False
    return True

  def drawGlyphIntoBackground(self, layer, info):
    # Check all hints, delete broken ones
    newhints = filter(lambda h: self.verifyHint(h), layer.hints)
    if len(newhints) != len(layer.hints):
      layer.hints = newhints
      self._rebuild()

    # Display Tag hints
    for t in layer.hints:
      if t.type == TAG:
        bez = NSBezierPath.bezierPath()
        bez.setLineWidth_(2.0)
        bez.moveToPoint_(t.originNode.position)
        if t.options == DIAGONAL:
          NSColor.greenColor().set()
          bez.lineToPoint_(t.targetNode.position)
        elif t.options == PROPORTIONAL_TRIPLE:
          NSColor.brownColor().set()
          bez.lineToPoint_(t.targetNode.position)
          bez.lineToPoint_(t.otherNode1.position)
        elif t.options == PROPORTIONAL_QUAD:
          on2 = t.valueForKey_("otherNode2") # Glyphs bug
          NSColor.yellowColor().set()
          bez.curveToPoint_controlPoint1_controlPoint2_(on2.position, t.targetNode.position, t.otherNode1.position)
        elif t.horizontal:
          NSColor.redColor().set()
          mid1 = NSPoint()
          mid1.x = t.originNode.position.x+5
          mid1.y = t.originNode.position.y-5
          mid2 = NSPoint()
          mid2.x = t.targetNode.position.x-5
          mid2.y = t.targetNode.position.y-5
          bez.curveToPoint_controlPoint1_controlPoint2_(t.targetNode.position,mid1,mid2)
        elif not t.horizontal:
          NSColor.blueColor().set()
          mid1 = NSPoint()
          mid1.x = t.originNode.position.x+5
          mid1.y = t.originNode.position.y+5
          mid2 = NSPoint()
          mid2.x = t.targetNode.position.x+5
          mid2.y = t.targetNode.position.y+5
          bez.curveToPoint_controlPoint1_controlPoint2_(t.targetNode.position,mid1,mid2)
        bez.stroke()

  def deactivate(self):
    NSNotificationCenter.defaultCenter().removeObserver_name_object_(self, "GSUpdateInterface", None)

  def conditionalContextMenus(self):

    # Empty list of context menu items
    contextMenus = []

    # Execute only if layers are actually selected
    if Glyphs.font.selectedLayers:
      layer = Glyphs.font.selectedLayers[0]
      s = filter(lambda x: type(x) == GSNode, layer.selection)
      if len(s) == 2:
        contextMenus.append({'name': "Add horizontal constraint", 'action': self.constrainX})
        contextMenus.append({'name': "Add vertical constraint", 'action': self.constrainY})
        contextMenus.append({'name': "Add diagonal constraint", 'action': self.constrainXY})

      if len(s) == 3:
        contextMenus.append({'name': "Add horizontal proportion constraint", 'action': self.constrainHProportion})
        contextMenus.append({'name': "Add vertical proportion constraint", 'action': self.constrainVProportion})

      if len(s) == 4:
        contextMenus.append({'name': "Add horizontal proportion constraint", 'action': self.constrainHProportion4})
        contextMenus.append({'name': "Add vertical proportion constraint", 'action': self.constrainVProportion4})

    # Return list of context menu items
    return contextMenus

  def _makeHint(self,horizontal,name,options = None):
    try:
      layer = Glyphs.font.selectedLayers[0]
      hint = GSHint()
      hint.type = TAG
      s = filter(lambda x: type(x) == GSNode, layer.selection)
      s = sorted(s, key=lambda l: l.position.x)
      if options:
        hint.setOptions_(options)
      hint.setName_(name)
      hint.horizontal = horizontal
      hint.originNode, hint.targetNode = s[0], s[1]
      if len(s) > 2:
        hint.otherNode1 = s[2]
      if len(s) > 3:
        hint.setOtherNode2_(s[3]) # Work around glyphs bug
      layer.hints.append(hint)
      self._rebuild()
    except Exception, e:
      print traceback.format_exc()

  def constrainX(self, sender):
    self._makeHint(True, "h")

  def constrainY(self, sender):
    self._makeHint(False, "v")

  def constrainXY(self, sender):
    self._makeHint(False, "d", DIAGONAL)

  def constrainHProportion(self, sender):
    self._makeHint(True, "hp", PROPORTIONAL_TRIPLE)

  def constrainVProportion(self, sender):
    self._makeHint(False, "vp", PROPORTIONAL_TRIPLE)

  def constrainHProportion4(self, sender):
    self._makeHint(True, "hp", PROPORTIONAL_QUAD)

  def constrainVProportion4(self, sender):
    self._makeHint(False, "vp", PROPORTIONAL_QUAD)

  def update(self):
    layer = Glyphs.font.selectedLayers[0]
    try:
      if self.__class__.constraining:
        return
      self.__class__.constraining = True
      layer.parent.undoManager().disableUndoRegistration()
      self.__class__.solver.setStayFromNodes(layer)

      self.__class__.solver.updateGlyphWithSolution()
      layer.parent.undoManager().enableUndoRegistration()
      self.__class__.constraining = False
    except:
      print traceback.format_exc()

  def inspectorViewControllers(self):
    Inspectors = []
    try:
      if not hasattr(self, "storedControllers"):
        self.storedControllers = {}
      layer = self.editViewController().graphicView().activeLayer()
      if layer is None:
        return []
      try:
        Inspector = self.storedControllers["GSGlyph"]
      except:
          Inspector = NSClassFromString("InspectorViewGlyphController").alloc().initWithNibName_bundle_("InspectorViewGSGlyph", NSBundle.bundleForClass_(NSClassFromString("GSFont")))
          Inspector.view()
          self.storedControllers["GSGlyph"] = Inspector
      Inspectors.append(Inspector)
      Inspector.setRepresentedObject_(layer)
      
      if len(layer.selection) == 1:
        selectedObject = layer.selection[0]
        if selectedObject.className() == "GSHint" and selectedObject.type == TAG:
          try:
            Inspector = self.storedControllers["Constraint"]
          except:
            Inspector = SingleConstraintViewController.alloc().initWithNibName_bundle_("singleConstraintView", NSBundle.bundleForClass_(NSClassFromString("Springs")))
            Inspector.view()
            self.storedControllers["Constraint"] = Inspector
          
          Inspector.setRepresentedObject_(selectedObject)
          Inspectors.append(Inspector)
    except:
      print traceback.format_exc()
    
    return Inspectors

    