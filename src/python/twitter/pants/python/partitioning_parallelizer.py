__author__ = 'ryan'

import copy

from naive_parallelizer import NaiveParallelizer
from target_sets import TargetSets

class PartitioningParallelizer(NaiveParallelizer):
  "This parallelizer works through a queue of currently eligible-to-build targets, but chunks multiple targets together in each compiler invocation, attempting to reach a number of sources per compile specified by a flag."

  def __init__(self, logger, invalid_target_tree, max_num_parallel_compiles, partition_size_hint, compile_cmd, post_compile_cmd = None):
    NaiveParallelizer.__init__(self, logger, invalid_target_tree, max_num_parallel_compiles, compile_cmd, post_compile_cmd)

    self._partition_size_hint = partition_size_hint

  def _attempt_to_place_target_in_set_and_recurse(self, next_target, current_set, current_sets):
    #print "attempting to insert %s into set %s. sets: %s. frontier: {%s}" % (next_target.id, str(current_set), str(current_sets), ','.join([t.data.id for t in self._frontier_nodes]))
    if current_set.num_sources + next_target.num_sources <= self._partition_size_hint or \
       len(current_set.targets) == 0:
      #print "\tinserting..."

      # Simulate adding the next eligible node to this compile worker's set
      current_set.add_target(next_target)

      # Recurse
      next_best_sets = copy.deepcopy(self._find_best_node_sets(current_sets))
      #print "\tnew sets: %s" % str(next_best_sets)
      # Remove the node from this compile worker's set
      current_set.remove_target(next_target)

      return next_best_sets

    else:
      return current_sets


  def _get_sets_with_dependents_of_node(self, node, sets):

    def node_set_has_dependents_of_next_node(current_set):
      # Determine whether the given set includes any of next_node's dependencies
      children_data = set([child.data for child in node.invalidated_children])
      #print "\t\t\tcurrent set targets: %s. children: %s" % (','.join([t.id for t in current_set.targets]), ','.join([t.id for t in children_data]))
      return len(children_data.intersection(current_set.targets)) > 0

    return filter(node_set_has_dependents_of_next_node, sets.sets)


  def _find_best_node_sets(self, current_sets):
    if len(self._frontier_nodes) == 0:
      return current_sets

    #print "_find_best_node_sets. frontier: {%s}. current: %s" % (','.join([node.data.id for node in self._frontier_nodes]), str(current_sets))

    best_sets = current_sets

    for next_node in self._frontier_nodes:
      # Make a copy that we can manipulate without screwing up our iteration over the list
      #new_frontier = frontier#copy.copy(frontier)

      # Simulate removing a node from the frontier
      self._frontier_nodes.remove(next_node)
      new_frontier_nodes = self._tree.invalidate_leaf(next_node)
      self._frontier_nodes.update(new_frontier_nodes)

      # Filter the existing target sets to just ones that already include dependencies of next_node.
      sets_that_include_next_node_dependents = self._get_sets_with_dependents_of_node(next_node, current_sets)

      if len(sets_that_include_next_node_dependents) == 1:
        # If exactly one target set has dependencies of next_node, next_node can only go in that target.
        next_best_sets = self._attempt_to_place_target_in_set_and_recurse(next_node.data, sets_that_include_next_node_dependents.pop(), current_sets)
        if next_best_sets > best_sets:
          best_sets = next_best_sets

      elif len(sets_that_include_next_node_dependents) == 0:
        # If no existing target sets include any of next_node's dependencies, then next_node can potentially go in
        # any of them; try placing next_node in each one and recursing.
        for current_set in current_sets.sets:
          next_best_sets = self._attempt_to_place_target_in_set_and_recurse(next_node.data, current_set, current_sets)
          if next_best_sets > best_sets:
            best_sets = next_best_sets

      # Undo the simulated node removal from the frontier
      self._frontier_nodes -= new_frontier_nodes
      self._frontier_nodes.add(next_node)
      self._tree.restore_leaf(next_node)

    return best_sets


  def _get_next_node_sets_to_compile(self, num_compile_workers_available):
    """Get a new frontier node, if any is ready to be compiled (i.e. it doesn't depend on any compiling target sets."""
    print "**_get_next_node_sets_to_compile (%d)" % num_compile_workers_available
    self._tree.print_tree()

    best_sets = self._find_best_node_sets(TargetSets(num_compile_workers_available))
    best_node_sets = [set([self._tree._nodes_by_data_map[t] for t in target_set.targets]) for target_set in best_sets.sets]
    print "..got: %s" % str(best_sets)
    return best_node_sets


