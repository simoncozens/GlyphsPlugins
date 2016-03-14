# encoding: utf-8
from GlyphsApp.plugins import *
from math import cos, sin
from glyphmonkey import *
from itertools import izip
from GlyphsApp import LINE

class Comb(FilterWithDialog):

	# Definitions of IBOutlets
	
	# The NSView object from the User Interface. Keep this here!
	dialog = objc.IBOutlet()

	# Text field in dialog
	myTextField = objc.IBOutlet()
	
	def settings(self):
		self.menuName = Glyphs.localize({'en': u'Comb Effect', 'de': u'Comb'})

		# Load dialog from .nib (without .extension)
		self.loadNib('IBdialog')

	# On dialog show
	def start(self):

		# Set default setting if not present
		if not Glyphs.defaults['org.simon-cozens.comb.teeth']:
			Glyphs.defaults['org.simon-cozens.comb.teeth'] = "0,0.05,0.1,0.15,0.2,0.3,0.35,0.65,0.7,0.8,0.85,0.9,0.95,1"

		self.myTextField.setStringValue_(Glyphs.defaults['org.simon-cozens.comb.teeth'])
		self.myTextField.becomeFirstResponder()

	# Action triggered by UI
	@objc.IBAction
	def setValue_( self, sender ):

		# Store value coming in from dialog
		Glyphs.defaults['org.simon-cozens.comb.teeth'] = sender.stringValue()

		# Trigger redraw
		self.update()

	# Actual filter
	def filter(self, layer, inEditView, customParameters):
		# Called on font export, get value from customParameters
		if customParameters.has_key('teeth'):
			value = customParameters['teeth']

		# Called through UI, use stored value
		else:
			value = Glyphs.defaults['org.simon-cozens.comb.teeth']

		# Split teeth into array of arrays
		t = map(float,value.split(","))
		teeth = zip(t[::2], t[1::2])
		self.combIt(layer, teeth)

	def combIt(self, layer, teeth):
		pathset = []
		for a in layer.paths:

		  # Find the two smallest "ends"
		  l1, s1, l2, s2 = None, None, None, None

		  for i in range(0,len(a.segments)):
		    s = a.segments[i]
		    if type(s) is GSLineSegment and (not l1 or s.length < l1):
		      s1 = i
		      l1 = s.length

		  for i in range(0,len(a.segments)):
		    s = a.segments[i]
		    if type(s) is GSLineSegment and (s.length >= l1 and (not l2 or s.length < l2) and i != s1):
		      s2 = i
		      l2 = s.length

		  if s1 > s2: s1, s2 = s2, s1
		  print("Identified path end segments:")
		  print(a.segments[s1], a.segments[s2])
		  # Find two edges between segments
		  edge1 = [ a.segments[i] for i in range(s1+1, s2) ]
		  edge2 = [ a.segments[i] for i in range(s2+1, len(a.segments))]
		  edge2.extend([a.segments[i] for i in range(0, s1)])
		  for i in range(0, len(edge2)): edge2[i].reverse()
		  edge2.reverse()
		  print("\nIdentified edges")
		  print("Edge 1:", edge1)
		  print("Edge 2:", edge2)
		  print("Teeth ", teeth)
		  if len(edge1) != len(edge2):
		    print("Edges not compatible in " + str(layer) + " - differing number of points")
		    raise TypeError
		  for tooth in teeth:
		    start, end = tooth[0],tooth[1]

		    segs1 = []
		    segs2 = []
		    for i in range(0, len(edge1)):
		      segs1.append(edge1[i].interpolate(edge2[i],start))
		      segs2.append(edge1[i].interpolate(edge2[i],end))
		    for i in range(0, len(segs2)): segs2[i].reverse()
		    segs2.reverse()
		    segs1.append(GSLineSegment(tuple = (segs1[-1]._seg[-1],segs2[0]._seg[0])))
		    segs1.extend(segs2)
		    segs1.append(GSLineSegment(tuple = (segs2[-1]._seg[-1],segs1[0]._seg[0])))

		    segs = segs1

		    path = GSPath()
		    path.parent = a.parent
		    path.segments = segs
		    print("Adding ", path, " to ",pathset)
		    pathset.append(path)
		    path.closed = True
		print(pathset)
		layer.paths = pathset

	def generateCustomParameter( self ):
		return "%s; teeth:%s;" % (self.__class__.__name__, Glyphs.defaults['org.simon-cozens.comb.teeth'] )
