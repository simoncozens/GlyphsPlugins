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
from TTSolver import TTSolver
import sys
import traceback
from GlyphsApp import TAG

GlyphsReporterProtocol = objc.protocolNamed( "GlyphsReporter" )

class ContentAwareSelect(SelectTool):
  constraining = False
  solver = TTSolver()

  def settings(self):
    self.name = "ContentAwareSelect"

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
        print(t)

  def deactivate(self):
    NSNotificationCenter.defaultCenter().removeObserver_name_object_(self, "GSUpdateInterface", None)
    pass

  def conditionalContextMenus(self):

    # Empty list of context menu items
    contextMenus = []

    # Execute only if layers are actually selected
    if Glyphs.font.selectedLayers:
      layer = Glyphs.font.selectedLayers[0]

      if len(layer.selection) == 2 and type(layer.selection[0]) == GSNode and type(layer.selection[1]) == GSNode:
        contextMenus.append({'name': "Add horizontal constraint", 'action': self.constrainX})
        contextMenus.append({'name': "Add vertical constraint", 'action': self.constrainY})
        contextMenus.append({'name': "Add distance constraint", 'action': self.constrainXY})

      if len(layer.selection) == 3 and type(layer.selection[0]) == GSNode and type(layer.selection[1]) == GSNode:
        contextMenus.append({'name': "Add proportion constraint", 'action': self.notYet})

    # Return list of context menu items
    return contextMenus

  def _makeTwoHint(self,layer):
    hint = GSHint()
    hint.type = TAG
    hint.originNode, hint.targetNode = layer.selection[0], layer.selection[1]
    return hint

  def constrainX(self, sender):
    layer = Glyphs.font.selectedLayers[0]
    hint = self._makeTwoHint(layer)
    hint.horizontal = True
    hint.setName_("h")
    layer.hints.append(hint)
    self._rebuild()

  def constrainY(self, sender):
    layer = Glyphs.font.selectedLayers[0]
    hint = self._makeTwoHint(layer)
    hint.horizontal = False
    hint.setName_("v")
    layer.hints.append(hint)
    self._rebuild()

  def constrainXY(self, sender):
    return

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