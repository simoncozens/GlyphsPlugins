#MenuTitle: 
# -*- coding: utf-8 -*-
__doc__=""
import GlyphsApp
from GlyphsApp import Proxy
from math import atan2, sqrt, cos, sin, radians, degrees
from Foundation import NSMakePoint, NSValue, NSMakeRect

def _ptDist(p1, p2):
  dx = p1.x - p2.x
  dy = p1.y - p2.y
  return sqrt(dx*dx+dy*dy)

# Make GSNodes hashable
class GSLineSegment(object):
  def __init__(self, tuple = None, owner = None, idx = 0):
    self._seg = tuple
    if not self._seg: self._seg = owner._segments[idx]
    self._owner = owner
    self._owneridx = idx

  def __repr__(self):
    """Return list-lookalike of representation string of objects"""
    return "<GSSegment (%s, %s)--(%s, %s)>" % (self.start.x,self.start.y,self.end.x,self.end.y)

  def _seg(self): return self._seg
  @property
  def start(self): return self._seg[0].position
  @property
  def end(self): return self._seg[-1].position

  # For backward compatibility
  def __getitem__(self, Key):
    if Key < 0:
      Key = self.__len__() + Key
    # There is a horribly subtle distinction between an NSValue and
    # an NSPoint. SpeedPunk expects to see an NSValue here and dies
    # if it doesn't have one.
    return NSValue.valueWithPoint_(self._seg[Key].position)

  @property
  def area(self):
    xa, ya = self.start.x, self.start.y/20
    xb, yb = xa, ya
    xc, yc = self.end.x, self.end.y/20
    xd, yd = xc, yc
    return (xb-xa)*(10*ya + 6*yb + 3*yc +   yd) + (xc-xb)*( 4*ya + 6*yb + 6*yc +  4*yd) +(xd-xc)*(  ya + 3*yb + 6*yc + 10*yd)

  @property
  def length(self):
    l1 = self.start.x - self.end.x
    l2 = self.start.y - self.end.y
    return sqrt(l1 * l1 + l2 * l2)

  @property
  def angle(self):
    e = self.end
    s = self.start
    return degrees(atan2(e.y - s.y, e.x - s.x))

  @property
  def selected(self):
    return self.start.selected and self.end.selected

  def reverse(self):
    self._seg = self._seg[::-1]

  def _interpolatenspoint(self, p1, p2, t):
    dx = (p2.x - p1.x) * t
    dy = (p2.y - p1.y) * t
    return NSMakePoint(p1.x + dx, p1.y + dy)

  def interpolate(self, other, t):
    if type(other) != type(self): raise TypeError
    l = []
    for i in range(0, len(self)):
      newnode = self._seg[i].copy() # Urgh
      newnode.position = self._interpolatenspoint(self._seg[i].position, other._seg[i].position, t)
      l.append(newnode)
    return type(self)(l)

  def __len__(self):
    return 2

class GSCurveSegment(GSLineSegment):
  def __repr__(self):
    return "<GSSegment (%s, %s)..[%s,%s]..[%s,%s]..(%s, %s)>" % (
      self.start.x, self.start.y,
      self.handle1.x, self.handle1.y,
      self.handle2.x, self.handle2.y,
      self.end.x,self.end.y
    )

  @property
  def handle1(self): return self._seg[1].position
  @property
  def handle2(self): return self._seg[2].position

  @property
  def area(self):
    xa, ya = self.start.x, self.start.y/20
    xb, yb = self.handle1.x, self.handle1.y/20
    xc, yc = self.handle2.x, self.handle2.y/20
    xd, yd = self.end.x, self.end.y/20
    return (xb-xa)*(10*ya + 6*yb + 3*yc +   yd) + (xc-xb)*( 4*ya + 6*yb + 6*yc +  4*yd) +(xd-xc)*(  ya + 3*yb + 6*yc + 10*yd)

  def angle(self): # XXX This is wrong
    e = self.end
    s = self.start
    return degrees(atan2(e.y - s.y, e.x - s.x))

  def interpolate_at_fraction(self, t):
    if t < 0 or t > 1:
      raise Exception("interpolate_at_fraction should be called with a number between 0 and 1")
    t1 = 1.0 - t;
    t1_3 = t1*t1*t1
    t1_3a = (3*t)*(t1*t1)
    t1_3b = (3*(t*t))*t1;
    t1_3c = (t * t * t )
    x = (self.start.x * t1_3) + (t1_3a * self.handle1.x) + (t1_3b * self.handle2.x) + (t1_3c * self.end.x)
    y = (self.start.y * t1_3) + (t1_3a * self.handle1.y) + (t1_3b * self.handle2.y) + (t1_3c * self.end.y)
    return (x,y)

  @property
  def length(self):
    steps = 50
    t = 0.0
    length = 0
    previous = ()
    while t < 1.0:
      this = self.interpolate_at_fraction(t)
      if t > 0:
        dx = previous[0] - this[0]
        dy = previous[1] - this[1]
        length = length + sqrt(dx*dx+dy*dy)
      t = t + 1.0/steps
      previous = this
    return length

  @property
  def tunni_point(self):
    p0 = self.start
    p1 = self.handle1
    p2 = self.handle2
    p3 = self.end
    s1_x = p1.x - p0.x
    s1_y = p1.y - p0.y
    s2_x = p3.x - p2.x
    s2_y = p3.y - p2.y

    s = (-s1_y * (p0.x - p2.x) + s1_x * (p0.y - p2.y)) / (-s2_x * s1_y + s1_x * s2_y)
    t = ( s2_x * (p0.y - p2.y) - s2_y * (p0.x - p2.x)) / (-s2_x * s1_y + s1_x * s2_y)
    return NSMakePoint(p0.x + (t * s1_x), p0.y + (t * s1_y))

  @property
  def curvature_percentages(self):
    p = self.tunni_point
    return (_ptDist(self.start,self.handle1) / _ptDist(self.start, p),
      _ptDist(self.handle2,self.end) / _ptDist(self.end, p))

  def __len__(self):
    return 4

class PathSegmentsProxy (Proxy):
  # Actually we're not going to use .segments at all, because we
  # want to be able to access things like GSNode.selected
  def toSegments(p):
    segList = []
    nodeList = p._owner.nodes
    thisSeg = (nodeList[-1],)
    for i in range(0,len(nodeList)):
      thisSeg = thisSeg + (nodeList[i],)
      if nodeList[i].type != GlyphsApp.GSOFFCURVE:
        segList.append(thisSeg)
        thisSeg = (nodeList[i],)
    return segList
  def __getitem__(self, Key):
    if Key < 0:
      Key = self.__len__() + Key
    segs = self.toSegments()
    if len(segs[Key]) == 2:
      return GSLineSegment( owner = self._owner, idx = Key, tuple = segs[Key])
    else:
      return GSCurveSegment( owner = self._owner, idx = Key, tuple = segs[Key])
  def __setitem__(self, Key, Layer):
    if Key < 0:
      Key = self.__len__() + Key
    # XXX
  def __len__(self):
    return len(self.toSegments())
  def values(self):
    return map(self.__getitem__, range(0,self.__len__()))

# Unfortunately working with segments doesn't always *work*. So we
# map a segment list to a node list
GSNode = GlyphsApp.GSNode

def toNodeList(segments):
  nodelist = []
  closed = (segments[-1].end.x == segments[0].start.x and segments[-1].end.y == segments[0].start.y)
  nodelist.append( GSNode((segments[0].start.x, segments[0].start.y), GlyphsApp.GSLINE) )
  for i in range(0,len(segments)):
    s = segments[i]
    t = GlyphsApp.GSCURVE
    c = GlyphsApp.GSSMOOTH
    if type(s) is GSLineSegment:
      t = GlyphsApp.GSLINE
    else:
      s1 = s.handle1
      nodelist.append(GSNode((s1.x,s1.y), type = GlyphsApp.GSOFFCURVE))
      s2 = s.handle2
      nodelist.append(GSNode((s2.x,s2.y), type = GlyphsApp.GSOFFCURVE))

    ns = i+1
    if ns >= len(segments): ns = 0
    if type(segments[ns]) is GSLineSegment:
      c = GlyphsApp.GSSHARP
    e = s.end
    node = GSNode((e.x, e.y), t)
    node.connection = c
    nodelist.append(node)

  n = segments[0].start

  return nodelist

GlyphsApp.GSPath.segments =  property( lambda self: PathSegmentsProxy(self),
  lambda self, value:
    self.setNodes_(toNodeList(value))
)

def nodeRotate(self, ox, oy, angle):
  angle = radians(angle)
  newX = ox + (self.position.x-ox)*cos(angle) - (self.position.y-oy)*sin(angle)
  newY = oy + (self.position.x-ox)*sin(angle) + (self.position.y-oy)*cos(angle)
  self.position = (round(newX,2), round(newY,2))

def nodeReflect(self, p0, p1):
  dx = p1.x - p0.x
  dy = p1.y - p0.y
  a = (dx * dx - dy * dy) / (dx * dx + dy * dy)
  b = 2 * dx * dy / (dx * dx + dy * dy)
  x = a * (self.position.x - p0.x) + b * (self.position.y - p0.y) + p0.x
  y = b * (self.position.x - p0.x) - a * (self.position.y - p0.y) + p0.y
  self.position =(round(x,2), round(y,2))

def nodeInterpolate(self, other, t):
  dx = (other.position.x - self.position.x) * t
  dy = (other.position.y - self.position.y) * t
  new = self.copy()
  new.position = (self.position.x + dx, self.position.y + dy)
  return new

GlyphsApp.GSNode.rotate = nodeRotate
GlyphsApp.GSNode.reflect = nodeReflect
GlyphsApp.GSNode.interpolate = nodeInterpolate

def _layerCenter(self):
  bounds = self.bounds
  ox = bounds.origin.x + bounds.size.width / 2
  oy = bounds.origin.y + bounds.size.height / 2
  return NSMakePoint(ox, oy)
GlyphsApp.GSLayer.center = _layerCenter

def horizontalCenterOfWeight(self):
  sampleX = self.bounds.origin.x
  sampleHeight = 5
  stripAreas = []
  totalArea = 0
  p = self.bezierPath()

  # This is slow and stupid but it works
  while sampleX < self.bounds.origin.x + self.bounds.size.width:
    sampleY = self.bounds.origin.y
    thisArea = 0
    while sampleY < self.bounds.origin.y + self.bounds.size.height:
      if p.containsPoint_([sampleX, sampleY]):
        thisArea = thisArea + 1
      sampleY = sampleY + sampleHeight
    stripAreas.append(thisArea)
    totalArea = totalArea + thisArea
    sampleX = sampleX + 1

  area = 0
  for i, v in enumerate(stripAreas):
    area = area + v
    if area > totalArea /2 :
      return i

GlyphsApp.GSLayer.horizontalCenterOfWeight = horizontalCenterOfWeight

def horizontalOpticalCenter(self):
  cw = self.horizontalCenterOfWeight()
  tc = self.center()[0]
  return tc + (cw-tc) / 3 # This is an approximation, obviously...
GlyphsApp.GSLayer.horizontalOpticalCenter = horizontalOpticalCenter

### additional GSPath methods

def layerCenter(self):
  return self.parent.center()

def pathCenter(self):
  bounds = self.bounds
  ox = bounds.origin.x + bounds.size.width / 2
  oy = bounds.origin.y + bounds.size.height / 2
  return NSMakePoint(ox, oy)

def pathRotate(self, angle=-1, ox=-1, oy=-1):
  if angle == -1: angle = 180
  if ox == -1 and oy == -1:
    if self.parent: # Almost always
      ox, oy = self.layerCenter().x, self.layerCenter().y
    else:
      ox, oy = self.center().x, self.center().y

  for n in self.nodes:
    n.rotate(ox, oy, angle)
  return self

def pathReflect(self, p0 = -1, p1 = -1):
  if p0 == -1 and p1 == -1:
    if self.parent: # Almost always
      p0 = self.layerCenter()
      p1 = self.layerCenter()
    else:
      p0 = self.center()
      p1 = self.center()
    p1.y = p1.y + 100

  for n in self.nodes:
    n.reflect(p0, p1)
  return self

def pathDiff(p1, p2):
  nodes1 = set((n.position.x,n.position.y) for n in p1.nodes)
  nodes2 = set((n.position.x,n.position.y) for n in p2.nodes)
  return nodes1 - nodes2

def pathEqual(p1, p2):
  pd = pathDiff(p1, p2)
  return len(pd) == 0

def pathToNodeSet(self):
  return GSNodeSet(self.nodes)

GlyphsApp.GSPath.layerCenter = layerCenter
GlyphsApp.GSPath.center = pathCenter
GlyphsApp.GSPath.rotate = pathRotate
GlyphsApp.GSPath.reflect = pathReflect
GlyphsApp.GSPath.equal = pathEqual
GlyphsApp.GSPath.diff = pathDiff
GlyphsApp.GSPath.toNodeSet = pathToNodeSet

class GSNodeSet(object):
  def toKey(self,n):
    return "%s %s %s" % (n.position.x, n.position.y, n.type)

  def __init__(self, nodes):
    self._dict = {}
    for n in nodes:
      self._dict[self.toKey(n)] = n

  def __repr__(self):
    return "<GSNodeSet (%s nodes)>" % (len(self))

  def __len__(self):
    return len(self._dict)

  @property
  def nodes(self):
      return self._dict.values()

  @property
  def bounds(self):
    minx, maxx, miny, maxy = None, None, None, None
    if len(self) < 1: return None
    for p in self.nodes:
      pos = p.position
      if minx == None or pos.x < minx: minx = pos.x
      if maxx == None or pos.x > maxx: maxx = pos.x
      if miny == None or pos.y < minx: miny = pos.y
      if maxy == None or pos.y > maxx: maxy = pos.y

    return NSMakeRect(minx, miny, maxx-minx, maxy-miny)

  @property
  def center(self):
    if len(self) < 1: return None
    b = self.bounds
    return NSMakePoint(b.origin.x + b.size.width / 2, b.origin.y + b.size.height / 2, )

  def copy(self):
    return GSNodeSet(n.copy() for n in self.nodes)

  def diff(ns1, ns2):
    nodes1 = set((n.position.x,n.position.y) for n in ns1.nodes)
    nodes2 = set((n.position.x,n.position.y) for n in ns2.nodes)
    return nodes1 - nodes2

  def equal(p1, p2):
    pd = p1.diff(p2)
    return len(pd) == 0

  def rotate(self, angle=-1, ox=-1, oy=-1):
    if angle == -1: angle = 180
    if ox == -1 and oy == -1:
        ox, oy = self.center.x, self.center.y

    for n in self.nodes:
      n.rotate(ox, oy, angle)
    return self

  def reflect(self, p0 = -1, p1 = -1):
    if p0 == -1 and p1 == -1:
      p0 = self.center
      p1 = self.center
      p1.y = p1.y + 100

    for n in self.nodes:
      n.reflect(p0, p1)
    return self

def selectedNodeSet(layer):
  sel = []
  for n in layer.selection:
    if isinstance(n, GSNode):
      sel.append(n)
  return GSNodeSet(sel)

GlyphsApp.GSLayer.selectedNodeSet = selectedNodeSet

# Does p have rotational symmetry?
#   ox, oy = p.layerCenter()
#   p.equal(p.copy().rotate(angle=180, ox=ox, oy=oy))
