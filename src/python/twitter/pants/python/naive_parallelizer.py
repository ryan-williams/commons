__author__ = 'ryan'

from parallel_compile_manager import ParallelCompileManager

class NaiveParallelizer(ParallelCompileManager):
  """Compiles targets one at a time, popping them from a "frontier" set (the set of targets all of whose dependencies
  have already finished compiling, meaning they can be compiled by the next available worker). When a target finished
  being compiled, """

  def __init__(self, logger, invalid_target_tree, max_num_parallel_compiles, compile_cmd, post_compile_cmd = None):
    ParallelCompileManager.__init__(self, logger, invalid_target_tree, max_num_parallel_compiles, compile_cmd, post_compile_cmd)

    # Set of nodes that can currently be compiled (i.e. that don't depend on anything that hasn't already been
    # compiled).
    self._frontier_nodes = set([leaf for leaf in invalid_target_tree.leaves])


  def _get_next_node_set_to_compile(self):
    """Get a new frontier node, if any is ready to be compiled (i.e. it doesn't depend on any compiling target sets."""
    if len(self._frontier_nodes) > 0:
      return set([self._frontier_nodes.pop()])
    return set([])

  def _handle_processed_node_set(self, target_node_set, success):
    "Add a node's parents to the frontier set, excepting any that are also ancestors of another of its parents."
    ParallelCompileManager._handle_processed_node_set(self, target_node_set, success)

    print "Frontier (%d): {%s}" % (len(self._frontier_nodes), ','.join(t.data.id for t in self._frontier_nodes))
    for target_node in target_node_set:
      for parent_node in target_node.parents:
        if (parent_node in self._processed_nodes or
            parent_node in self._in_flight_target_nodes or
            parent_node in self._frontier_nodes):
          continue
        parent_is_eligible = True
        for sibling_node in parent_node.children:
          if sibling_node not in self._processed_nodes:
            parent_is_eligible = False
            break
        if parent_is_eligible:
          print "\tadding newly eligible parent of %s: %s" % (target_node.data.target.id, parent_node.data.target.id)
          self._frontier_nodes.add(parent_node)


