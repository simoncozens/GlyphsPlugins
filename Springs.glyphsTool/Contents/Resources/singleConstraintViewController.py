# encoding: utf-8

from Foundation import *

class SingleConstraintViewController(GSInspectorViewController):
  
  sizeField = objc.IBOutlet()
  
  def setRepresentedObject_(self, aObject):
    if aObject is not None:
      print "__aObject", aObject, aObject.name()
      self.sizeField.setStringValue_(aObject.name())
    else:
      self.sizeField.setStringValue_("")
    self._representedHint = aObject
  
  @objc.IBAction
  def setSize_(self, sender):
    if self._representedHint is not None:
      self._representedHint.name = sender.stringValue()