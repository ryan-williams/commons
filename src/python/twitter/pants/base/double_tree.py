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

  def init_ancestor_and_descendent_level_counts(self, indent = ''):
    visited = set([])
    def _init_ancestor_and_descendent_level_counts(node, indent):
      if node.data.target.id in visited:
        return
      #print "%s%s" % (indent, node.data.target.id)
      visited.add(node.data.target.id)
      node.ancestor_levels = (
        0 if len(node.parents) == 0 else
        max(node.ancestor_levels, 1 + max([parent.ancestor_levels for parent in node.parents])))

      for child in node.children:
        _init_ancestor_and_descendent_level_counts(child, indent + '  ')
      node.descendent_levels = (
        0 if len(node.children) == 0 else
        max(node.descendent_levels, 1 + max([child.descendent_levels for child in node.children]))
        )
    _init_ancestor_and_descendent_level_counts(self, indent)

  def print_node(self, indent = ''):
    print "%s*%s %s" % ("ROOT " if indent == '' else '', indent, self.data.target.id)
    [child.print_node(indent + '  ') for child in self.children]

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

    self._roots = set([])
    self.leaves = set([])

    print "%d nodes:" % len(self.nodes)
    for node in self.nodes:
      print node.data.target.id,
    print ''

    self._init_parent_and_child_relationships()

    self._find_roots_and_leaves()

    print "%d roots:" % len(self._roots)
    for root in self._roots:
      print root.data.target.id

    #[root.print_node() for root in self._roots]
    print "\t init level counts"
    # Recursively initialize nodes' ancestor and descendent level counts, starting from each root node.
    [ root_node.init_ancestor_and_descendent_level_counts() for root_node in self._roots ]

    above_by_level = {}
    below_by_level = {}
    for node in self.nodes:
      if node.ancestor_levels not in above_by_level:
        above_by_level[node.ancestor_levels] = []
      above_by_level[node.ancestor_levels].append(node)

      if node.descendent_levels not in below_by_level:
        below_by_level[node.descendent_levels] = []
      below_by_level[node.descendent_levels].append(node)

      print "%d\t%d\t%s:" % (node.ancestor_levels, node.descendent_levels, node.data.target.id)
      print "\tchildren (%d):" % len(node.children)
      for child in node.children:
        print "\t\t" + child.data.target.id
      print "\tparents (%d):" % len(node.parents)
      for parent in node.parents:
        print "\t\t" + parent.data.target.id
      print ''

    print "ancestor levels:"
    for num in above_by_level:
      print "\t%d: %d" % (num, len(above_by_level[num]))
    print ''

    print "descendent levels:"
    for num in below_by_level:
      print "\t%d: %d" % (num, len(below_by_level[num]))
    print ''

    print "done!"

  def lookup(self, data):
    if data in self._nodes_by_data_map:
      return self._nodes_by_data_map[data]
    return None

  def _init_parent_and_child_relationships(self):
    print "\t _init_parent_and_child_relationships"
    def find_children(original_node, data):
      for child_data in self._child_fn(data):
        # TODO(ryan): this trick may not be necessary since it's also done in VersionedTarget.
        if child_data in self._nodes_by_data_map:
          child_node = self._nodes_by_data_map[child_data]
          original_node.children.add(child_node)
          child_node.parents.add(original_node)
        else:
          #find_children(original_node, child_data)
          raise Exception("child_fn shouldn't yield data objects not in tree:\n %s. child of: %s. original data: %s" % (
            str(child_data),
            str(data),
            str(original_node.data)))

    for node in self.nodes:
      find_children(node, node.data)

  def _find_roots_and_leaves(self):
    print "\t _find_roots_and_leaves"
    for node in self.nodes:
      if len(node.parents) == 0:
        self._roots.add(node)
      if len(node.children) == 0:
        self.leaves.add(node)

