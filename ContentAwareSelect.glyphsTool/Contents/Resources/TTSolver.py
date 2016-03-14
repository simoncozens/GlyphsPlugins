from cassowary import Variable, SimplexSolver, STRONG, WEAK, REQUIRED
from GlyphsApp import GSOFFCURVE, TAG

DISTANCE = 4
PROPORTIONAL_TRIPLE = 8

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
    if not (n.hash() in self.nodehash):
      raise KeyError(n)
    return self.nodehash[n.hash()]["yvar"]

  def xvar(self,n):
    if not (n.hash() in self.nodehash):
      raise KeyError(n)
    return self.nodehash[n.hash()]["xvar"]

  def setConstraintsFromHints(self, layer):
    c = []
    for h in layer.hints:
      if h.type == TAG:
        if h.options() < 8 and not h.horizontal:
          v1 = self.yvar(h.originNode)
          v2 = self.yvar(h.targetNode)
          yValue = v1.value - v2.value
          ystem = v1 - v2
          c.append(ystem == yValue)

        if h.options() < 8 and h.horizontal:
          v1 = self.xvar(h.originNode)
          v2 = self.xvar(h.targetNode)
          xValue = v1.value - v2.value
          xstem = v1 - v2
          c.append(xstem == xValue)

    for cs in c:
      self.solver.add_constraint(cs)

  def setStayFromNodes(self, nl):
    nodes = filter(lambda x:x.hash() in self.nodehash, nl)
    if len(nodes) < 1:
      return

    for n in nodes:
      self.solver.add_edit_var(self.xvar(n))
      self.solver.add_edit_var(self.yvar(n))

    with self.solver.edit():
      for j in nodes:
        n = self.nodehash[j.hash()]
        print("Suggesting ",n["node"].position.x,n["node"].position.y)
        self.solver.suggest_value(n["xvar"], n["node"].position.x)
        self.solver.suggest_value(n["yvar"], n["node"].position.y)

    for j in nodes:
      n = self.nodehash[j.hash()]
      print("Got: ",n["xvar"],n["yvar"])

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

    with self.solver.edit():
      for i in self.nodehash:
        n = self.nodehash[i]
        self.solver.suggest_value(n["xvar"], n["node"].position.x)
        self.solver.suggest_value(n["yvar"], n["node"].position.y)