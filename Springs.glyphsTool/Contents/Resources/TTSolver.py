from cassowary import Variable, SimplexSolver, STRONG, WEAK, REQUIRED
from GlyphsApp import GSOFFCURVE, TAG, CURVE

DIAGONAL = 8
PROPORTIONAL_TRIPLE = 16
PROPORTIONAL_QUAD = 32

def safediv(a,b):
  if b == 0:
    return 0
  return a/b

class TTSolver:

  def initialSetup(self, layer):
    self.solver = SimplexSolver()
    self.nodehash = {}
    for p in layer.paths:
      for n in p.nodes:
        nid = n.hash()
        self.nodehash[nid] = {
          "node": n,
          "xvar": Variable("x"+str(nid), n.position.x),
          "yvar": Variable("y"+str(nid), n.position.y),
          "affected": set()
        }
    self.setConstraintsFromHints(layer)

  def yvar(self,n):
    if not n:
      raise ValueError
    if not (n.hash() in self.nodehash):
      raise KeyError(n)
    return self.nodehash[n.hash()]["yvar"]

  def xvar(self,n):
    if not n:
      raise ValueError
    if not (n.hash() in self.nodehash):
      raise KeyError(n)
    return self.nodehash[n.hash()]["xvar"]

  def setConstraintsFromHints(self, layer):
    c = []
    for h in layer.hints:
      if h.type == TAG:
        try:
          if h.options() == DIAGONAL or (h.options() < 8 and not h.horizontal):
            v1 = self.yvar(h.originNode)
            v2 = self.yvar(h.targetNode)
            yValue = v1.value - v2.value
            ystem = v1 - v2
            c.append(ystem == yValue)

          if h.options() == DIAGONAL or (h.options() < 8 and h.horizontal):
            v1 = self.xvar(h.originNode)
            v2 = self.xvar(h.targetNode)
            xValue = v1.value - v2.value
            xstem = v1 - v2
            c.append(xstem == xValue)

          if h.options() == PROPORTIONAL_TRIPLE:
            if h.horizontal:
              v1 = self.xvar(h.originNode)
              v2 = self.xvar(h.targetNode)
              v3 = self.xvar(h.otherNode1)
              proportion = safediv(h.targetNode.position.x - h.originNode.position.x , h.otherNode1.position.x - h.targetNode.position.x)
            else:
              v1 = self.yvar(h.originNode)
              v2 = self.yvar(h.targetNode)
              v3 = self.yvar(h.otherNode1)
              proportion = safediv(h.targetNode.position.y - h.originNode.position.y, h.otherNode1.position.y - h.targetNode.position.y)
            d1 = v2 - v1
            d2 = v3 - v2
            c.append(d2 * proportion == d1)

          if h.options() == PROPORTIONAL_QUAD:
            on2 = h.valueForKey_("otherNode2") # Glyphs bug
            if h.horizontal:
              v1 = self.xvar(h.originNode)
              v2 = self.xvar(h.targetNode)
              v3 = self.xvar(h.otherNode1)
              v4 = self.xvar(on2)
              proportion = safediv(h.targetNode.position.x - h.originNode.position.x, on2.position.x - h.otherNode1.position.x)
            else:
              v1 = self.yvar(h.originNode)
              v2 = self.yvar(h.targetNode)
              v3 = self.yvar(h.otherNode1)
              v4 = self.yvar(on2)
              proportion = safediv(h.targetNode.position.y - h.originNode.position.y, on2.position.y - h.otherNode1.position.y)
            d1 = v2 - v1
            d2 = v4 - v3
            # print(d1,d2,proportion)
            c.append(d2 * proportion == d1)
        except ValueError:
          print("I found a busted constraint. It'll get cleaned up soon.")
    for cs in c:
      self.solver.add_constraint(cs)

  def _diagonalConstraints(self, c, n1,n2):
    v1 = self.xvar(n1)
    v2 = self.xvar(n2)
    xValue = v1.value - v2.value
    xstem = v1 - v2
    v1 = self.yvar(n1)
    v2 = self.yvar(n2)
    yValue = v1.value - v2.value
    ystem = v1 - v2
    c.append(xstem == xValue)
    c.append(ystem == yValue)

  def _makeEditable(self,node):
    n = self.nodehash[node.hash()]
    self.solver.add_edit_var(n["xvar"])
    self.solver.add_edit_var(n["yvar"])

  def _suggest(self,node):
    n = self.nodehash[node.hash()]
    # print("Suggesting ",n["node"].position.x,n["node"].position.y)
    self.solver.suggest_value(n["xvar"], n["node"].position.x)
    self.solver.suggest_value(n["yvar"], n["node"].position.y)

  def setStayFromNodes(self, layer):
    nodes = filter(lambda x:x.hash() in self.nodehash, layer.selection)
    if len(nodes) < 1:
      return

    temporaryConstraints = []
    c = []
    for p in layer.paths:
      for n in p.nodes:
        if n.type != GSOFFCURVE:
          # Constrain left handle and this node
          if n.prevNode.type == GSOFFCURVE and not n.prevNode.selected:
              self._diagonalConstraints(c, n, n.prevNode)
          if n.nextNode.type == GSOFFCURVE and not n.nextNode.selected:
            self._diagonalConstraints(c, n, n.nextNode)

    for cs in c:
      temporaryConstraints.append(self.solver.add_constraint(cs, strength=WEAK))

    # print("Putting stuff into solver")
    for n in nodes:
      self._makeEditable(n)
      if n.type != GSOFFCURVE:
        if n.nextNode.type == GSOFFCURVE:
          self._makeEditable(n.nextNode)
        if n.prevNode.type == GSOFFCURVE:
          self._makeEditable(n.prevNode)
      else:
        if n.nextNode.type == CURVE and n.nextNode.smooth:
          self._makeEditable(n.nextNode)
          self._makeEditable(n.nextNode.nextNode)
        elif n.prevNode.type == CURVE and n.prevNode.smooth:
          self._makeEditable(n.prevNode)
          self._makeEditable(n.prevNode.prevNode)

    with self.solver.edit():
      for n in nodes:
        self._suggest(n)
        if n.type != GSOFFCURVE:
          if n.nextNode.type == GSOFFCURVE:
            self._suggest(n.nextNode)
          if n.prevNode.type == GSOFFCURVE:
            self._suggest(n.prevNode)
        else:
          if n.nextNode.type == CURVE and n.nextNode.smooth:
            self._suggest(n.nextNode)
            self._suggest(n.nextNode.nextNode)
          elif n.prevNode.type == CURVE and n.prevNode.smooth:
            self._suggest(n.prevNode)
            self._suggest(n.prevNode.prevNode)

    for j in nodes:
      n = self.nodehash[j.hash()]
      # print("Got: ",n["xvar"],n["yvar"])

    for c in temporaryConstraints:
      self.solver.remove_constraint(c)

  def updateGlyphWithSolution(self):
    for i in self.nodehash:
      n = self.nodehash[i]
      # print(n["node"], "->", n["xvar"].value, n["yvar"].value)
      n["node"].position = (n["xvar"].value, n["yvar"].value)

  def updateSolverFromGlyph(self):
    for i in self.nodehash:
      n = self.nodehash[i]
      n["xvar"].value = n["node"].position.x
      n["yvar"].value = n["node"].position.y
      n["xstay"] = self.solver.add_stay(n["xvar"], strength=WEAK)
      n["ystay"] = self.solver.add_stay(n["yvar"], strength=WEAK)
      self.solver.add_edit_var(n["xvar"])
      self.solver.add_edit_var(n["yvar"])

    if len(self.nodehash) > 0:
      with self.solver.edit():
        for i in self.nodehash:
          n = self.nodehash[i]
          self.solver.suggest_value(n["xvar"], n["node"].position.x)
          self.solver.suggest_value(n["yvar"], n["node"].position.y)
