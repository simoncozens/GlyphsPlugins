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


from GlyphsApp.plugins import *
from TTSolver import TTSolver, DIAGONAL, PROPORTIONAL_TRIPLE, PROPORTIONAL_QUAD
import sys
import traceback
from GlyphsApp import TAG

GlyphsReporterProtocol = objc.protocolNamed( "GlyphsReporter" )

class Springs(SelectTool):
  constraining = False
  solver = TTSolver()

  def settings(self):
    self.name = "Springs"

  def start(self):
    pass

  def _rebuild(self):
    l = Glyphs.font.selectedLayers[0]
    self.__class__.solver.initialSetup(l)
    self.__class__.solver.setConstraintsFromHints(l)
    self.__class__.solver.updateSolverFromGlyph()

  def activate(self):
    NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, objc.selector(self.update,signature='v@:'), "GSUpdateInterface", None)
    self._rebuild()
    pass

  def background(self, layer):
    pass

  def foreground(self, layer):
    # Display Tag hints
    for t in layer.hints:
      if t.type == TAG:
        if t.options() == DIAGONAL:
          NSColor.greenColor().set()
          bez = NSBezierPath.bezierPath()
          bez.setLineWidth_(2.0)
          bez.moveToPoint_(t.originNode.position)
          bez.lineToPoint_(t.targetNode.position)
          bez.stroke()
        elif t.options() == PROPORTIONAL_TRIPLE:
          NSColor.brownColor().set()
          bez = NSBezierPath.bezierPath()
          bez.setLineWidth_(2.0)
          bez.moveToPoint_(t.originNode.position)

          bez.lineToPoint_(t.targetNode.position)
          bez.lineToPoint_(t.otherNode1.position)
          bez.stroke()
        elif t.options() == PROPORTIONAL_QUAD:
          NSColor.yellowColor().set()
          bez = NSBezierPath.bezierPath()
          bez.setLineWidth_(2.0)
          bez.moveToPoint_(t.originNode.position)
          bez.curveToPoint_controlPoint1_controlPoint2_(t.targetNode.position, t.otherNode1.position, t.otherNode2.position)
          bez.stroke()
        elif t.horizontal:
          NSColor.redColor().set()
          bez = NSBezierPath.bezierPath()
          bez.setLineWidth_(2.0)
          mid1 = NSPoint()
          mid1.x = t.originNode.position.x+5
          mid1.y = t.originNode.position.y-5
          mid2 = NSPoint()
          mid2.x = t.targetNode.position.x-5
          mid2.y = t.targetNode.position.y-5

          bez.moveToPoint_(t.originNode.position)
          bez.curveToPoint_controlPoint1_controlPoint2_(t.targetNode.position,mid1,mid2)
          bez.stroke()
        elif not t.horizontal:
          NSColor.blueColor().set()
          bez = NSBezierPath.bezierPath()
          bez.setLineWidth_(2.0)
          mid1 = NSPoint()
          mid1.x = t.originNode.position.x+5
          mid1.y = t.originNode.position.y+5
          mid2 = NSPoint()
          mid2.x = t.targetNode.position.x+5
          mid2.y = t.targetNode.position.y+5

          bez.moveToPoint_(t.originNode.position)
          bez.curveToPoint_controlPoint1_controlPoint2_(t.targetNode.position,mid1,mid2)
          bez.stroke()

  def deactivate(self):
    NSNotificationCenter.defaultCenter().removeObserver_name_object_(self, "GSUpdateInterface", None)
    pass

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

    # Return list of context menu items
    return contextMenus

  def _makeHint(self,layer):
    hint = GSHint()
    hint.type = TAG
    s = filter(lambda x: type(x) == GSNode, layer.selection)
    s = sorted(s, key=lambda l: l.position.x)
    print(s)
    hint.originNode, hint.targetNode = s[0], s[1]
    if len(s) > 2:
      hint.otherNode1 = s[2]
      print("ON1: ", s[2])
    if len(s) > 3:
      hint.setOtherNode2_(s[3]) # Work around glyphs bug
      print("ON2: ", s[3])
    return hint

  def constrainX(self, sender):
    layer = Glyphs.font.selectedLayers[0]
    hint = self._makeHint(layer)
    hint.horizontal = True
    hint.setName_("h")
    layer.hints.append(hint)
    self._rebuild()

  def constrainY(self, sender):
    layer = Glyphs.font.selectedLayers[0]
    hint = self._makeHint(layer)
    hint.horizontal = False
    hint.setName_("v")
    layer.hints.append(hint)
    self._rebuild()

  def constrainXY(self, sender):
    layer = Glyphs.font.selectedLayers[0]
    hint = self._makeHint(layer)
    hint.setOptions_(DIAGONAL)
    hint.setName_("d")
    layer.hints.append(hint)
    self._rebuild()

  def constrainHProportion(self, sender):
    layer = Glyphs.font.selectedLayers[0]
    hint = self._makeHint(layer)
    hint.horizontal = True
    hint.setOptions_(PROPORTIONAL_TRIPLE)
    hint.setName_("hp")
    layer.hints.append(hint)
    self._rebuild()

  def constrainVProportion(self, sender):
    layer = Glyphs.font.selectedLayers[0]
    hint = self._makeHint(layer)
    hint.horizontal = False
    hint.setOptions_(PROPORTIONAL_TRIPLE)
    hint.setName_("vp")
    layer.hints.append(hint)
    self._rebuild()

  def constrainHProportion4(self, sender):
    layer = Glyphs.font.selectedLayers[0]
    hint = self._makeHint(layer)
    hint.horizontal = True
    hint.setOptions_(PROPORTIONAL_QUAD)
    hint.setName_("hp")
    layer.hints.append(hint)
    self._rebuild()

  def update(self):
    try:
      if self.__class__.constraining:
        return
      self.__class__.constraining = True
      print("I saw it change!", self.__class__.solver)
      layer = Glyphs.font.selectedLayers[0]
      self.__class__.solver.setStayFromNodes(layer.selection)

      self.__class__.solver.updateGlyphWithSolution()
      self.__class__.constraining = False
    except Exception, e:
      _, _, tb = sys.exc_info()
      traceback.print_tb(tb) # Fixed format
      tb_info = traceback.extract_tb(tb)
      filename, line, func, text = tb_info[-1]

      print('An error occurred on line {} in statement {}'.format(line, text))