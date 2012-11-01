__author__ = 'ryan'

# TODO(ryan): move this inside DoubleTree / make private
class DoubleTreeNode(object):
  def __init__(self, data):
    self.data = data
    self.parents = set()
    self.children = set()
    self.invalidated_children = set()

  # TODO(ryan): remove
  def __repr__(self):
    return self.data.id

  def as_str(self):
    return "%s -> [%s][%s]" % (self.data.id, ','.join([child.data.id for child in self.children]), ','.join([c.data.id for c in self.invalidated_children]))

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
      print node.data.id,
    print ''

    self._init_parent_and_child_relationships()

    self._find_roots_and_leaves()

    print "%d roots:" % len(self._roots)
    for root in self._roots:
      print root.data.id
    print ''

    for node in self.nodes:
      print "%s:" % node.data.id
      print "\tchildren (%d):" % len(node.children)
      for child in node.children:
          print "\t\t" + child.data.id
      print "\tparents (%d):" % len(node.parents)
      for parent in node.parents:
          print "\t\t" + parent.data.id
      print ''

    self.print_tree()

    print "done!"

  def print_tree(self):
    for node in self.nodes:
      print """deps["%s"] = {"num": %d, "children": [%s]}""" % (node.data.id, node.data.num_sources, ','.join(['"%s"' % child.data.id for child in node.children]))
    print ''

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


  def remove_nodes(self, nodes):
    new_leaves = set()
    for node in nodes:
      for parent_node in node.parents:
        if parent_node in nodes:
          continue
        parent_node.children.remove(node)
        if len(parent_node.children) == 0:
          self.leaves.add(parent_node)
          new_leaves.add(parent_node)
    return new_leaves


  def invalidate_leaf(self, node):
    if node not in self.leaves:
      raise Exception("remove_leaf called on non-leaf node: %s" % node.data.id)
    new_leaves = set()
    for parent_node in node.parents:
      parent_node.children.remove(node)
      parent_node.invalidated_children.add(node)
      if len(parent_node.children) == 0:
        self.leaves.add(parent_node)
        new_leaves.add(parent_node)

    #print "invalidating leaf %s. new leaves: %s" % (node.data.id, ','.join([t.as_str() for t in new_leaves]))
    return new_leaves


  def restore_leaf(self, node):
    if len(node.children) != 0:
      raise Exception("add_leaf called on child-having node %s" % node.data.id)
    for parent_node in node.parents:
      if len(parent_node.children) == 0:
        if parent_node not in self.leaves:
          raise Exception("add_leaf called on %s. childless parent %s not in leaves array" % (node.data.id, parent_node.data.id))
        self.leaves.remove(parent_node)
      parent_node.children.add(node)
      parent_node.invalidated_children.remove(node)
    self.leaves.add(node)
