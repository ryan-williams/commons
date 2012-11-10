__author__ = 'ryan'

# TODO(ryan): move this inside DoubleTree / make private
class DoubleTreeNode(object):
  def __init__(self, data):
    self.data = data
    self.parents = set()
    self.children = set()
    self.invalidated_children = set()

    self.descendants = set()
    self.ancestors = set()
    self.independents = set()

  # TODO(ryan): remove
  def __repr__(self):
    return self.data.id

  #def __deepcopy__(self, memo):


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

    self._init_ancestor_and_dependent_relationships()

    print "%d roots:" % len(self._roots)
    for root in self._roots:
      print root.data.id
    print ''

#    for node in self.nodes:
#      print "%s:" % node.data.id
#      print "\tchildren (%d):" % len(node.children)
#      for child in node.children:
#          print "\t\t" + child.data.id
#      print "\tparents (%d):" % len(node.parents)
#      for parent in node.parents:
#          print "\t\t" + parent.data.id
#      print ''

    self.print_tree()

    print "done!"

  def print_tree(self):
    print "deps = {"
    for node in self.nodes:
      print """  "%s": {"num": %d, "children": [%s]},""" % (node.data.id, node.data.num_sources, ','.join(['"%s"' % child.data.id for child in node.children]))
    print '}'
    print ''

  def lookup(self, data):
    if data in self._nodes_by_data_map:
      return self._nodes_by_data_map[data]
    return None

  def _init_parent_and_child_relationships(self):
    print "\t _init_parent_and_child_relationships"
    def find_children(original_node, data):
      for child_data in self._child_fn(data):
        if child_data in self._nodes_by_data_map:
          child_node = self._nodes_by_data_map[child_data]
          original_node.children.add(child_node)
          child_node.parents.add(original_node)
        else:
          raise Exception("child_fn shouldn't yield data objects not in tree:\n %s. child of: %s. original data: %s" % (
            str(child_data),
            str(data),
            str(original_node.data)))

    for node in self.nodes:
      find_children(node, node.data)


  def _init_ancestor_and_dependent_relationships(self):
    print "\t _init_ancestor_and_dependent_relationships"

    if not self._roots and self.nodes:
      raise Exception("Non-empty tree calling _init_ancestor_and_dependent_relationships before initializing roots")

    def init_descendants_for_node(node):
      if node.descendants:
        return node.descendants

      node.descendants.update(node.children)
      for child in node.children:
        init_descendants_for_node(child)
        node.descendants.update(child.descendants)

    map(init_descendants_for_node, self._roots)

    for node in self.nodes:
      for descendant in node.descendants:
        descendant.ancestors.add(node)

    for node1 in self.nodes:
      for node2 in self.nodes:
        if (not node1.descendants & node2.descendants and
            node1 != node2 and
            node1 not in node2.descendants and
            node2 not in node1.descendants):
          node1.independents.add(node2)
          node2.independents.add(node1)


  def _find_roots_and_leaves(self):
    print "\t _find_roots_and_leaves"
    for node in self.nodes:
      if not node.parents:
        self._roots.add(node)
      if not node.children:
        self.leaves.add(node)


  def restore_nodes(self, nodes):
    for node in nodes:
      for parent_node in node.parents:
        if parent_node in nodes:
          continue
        if not parent_node.children:
          self.leaves.remove(parent_node)
        parent_node.children.add(node)
    self.leaves.update(nodes)

  def remove_nodes(self, nodes):
    print "\tRemoving nodes: {%s}" % ','.join([n.data.id for n in nodes])
    new_leaves = set()
    for node in nodes:
      #print "\t\t%s" % node.data.id
      if node not in self.nodes:
        raise Exception("Attempting to remove invalid node: %s" % node.data.id)
      for parent_node in node.parents:
        #print "\t\t\tparent: %s" % parent_node.data.id
        if parent_node in nodes:
          continue
        parent_node.children.remove(node)
        if not parent_node.children:
          new_leaves.add(parent_node)

    # Do these outside in case 'nodes' is in fact self.leaves, so that we don't change the set we're iterating over.
    self.leaves -= nodes
    self.leaves.update(new_leaves)
    print "\tnew leaves: {%s}. all leaves: {%s}" % (','.join([n.data.id for n in new_leaves]), ','.join([n.data.id for n in self.leaves]))
    return new_leaves


  def invalidate_leaf(self, node):
    if node not in self.leaves:
      raise Exception("remove_leaf called on non-leaf node: %s" % node.data.id)
    new_leaves = set()
    for parent_node in node.parents:
      parent_node.children.remove(node)
      parent_node.invalidated_children.add(node)
      if not len(parent_node.children):
        self.leaves.add(parent_node)
        new_leaves.add(parent_node)

    #print "invalidating leaf %s. new leaves: %s" % (node.data.id, ','.join([t.as_str() for t in new_leaves]))
    return new_leaves


  def restore_leaf(self, node):
    if len(node.children) != 0:
      raise Exception("add_leaf called on child-having node %s" % node.data.id)
    for parent_node in node.parents:
      if not parent_node.children:
        if parent_node not in self.leaves:
          raise Exception("add_leaf called on %s. childless parent %s not in leaves array" % (node.data.id, parent_node.data.id))
        self.leaves.remove(parent_node)
      parent_node.children.add(node)
      parent_node.invalidated_children.remove(node)
    self.leaves.add(node)
