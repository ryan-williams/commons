__author__ = 'ryan'

# TODO(ryan): move this inside DoubleTree / make private
class DoubleTreeNode(object):
  def __init__(self, data):
    self.data = data
    self.parents = set([])
    self.children = set([])
    self.ancestor_levels = 0
    self.descendent_levels = 0

  def register_parent(self, parent):
    self.parents.add(parent)
    self.ancestor_levels = max(self.ancestor_levels, 1 + parent.ancestor_levels)

  def register_child(self, child):
    self.children.add(child)
    self.descendent_levels = max(self.descendent_levels, 1 + child.descendent_levels)

  def init_ancestor_and_descendent_level_counts(self):
    self.ancestor_levels = (
      0 if len(self.parents) == 0 else
      max(self.ancestor_levels, 1 + max([parent.ancestor_levels for parent in self.parents])))
    [ child.init_ancestor_and_descendent_level_counts() for child in self.children ]
    self.descendent_levels = (
      0 if len(self.children) == 0 else
      max(self.descendent_levels, 1 + max([child.descendent_levels for child in self.children]))
      )

  # TODO(ryan): remove
  def __repr__(self):
    return self.data.id

class DoubleTree(object):
  def __init__(self, objects, child_fn):
    self._child_fn = child_fn

    self.nodes = [ DoubleTreeNode(object) for object in objects ]
    self._nodes_by_data_map = {}
    for node in self.nodes:
      self._nodes_by_data_map[node.data] = node

    self._init_parent_and_child_relationships()

    self._roots = set([])
    self.leaves = set([])
    self._find_roots_and_leaves()

    # Recursively initialize nodes' ancestor and descendent level counts, starting from each root node.
    [ root_node.init_ancestor_and_descendent_level_counts() for root_node in self._roots ]

  def lookup(self, data):
    if data in self._nodes_by_data_map:
      return self._nodes_by_data_map[data]
    return None

  def _init_parent_and_child_relationships(self):
    def find_children(original_node, data):
      for child_data in self._child_fn(data):
        if child_data in self._nodes_by_data_map:
          child_node = self._nodes_by_data_map[child_data]
          original_node.children.add(child_node)
          child_node.parents.add(original_node)
        else:
          find_children(original_node, child_data)

    for node in self.nodes:
      find_children(node, node.data)

  def _find_roots_and_leaves(self):
    for node in self.nodes:
      if len(node.parents) == 0:
        self._roots.add(node)
      if len(node.children) == 0:
        self.leaves.add(node)

