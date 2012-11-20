__author__ = 'ryan'

import copy
import time

from naive_parallelizer import NaiveParallelizer
from target_sets import TargetSets

def p(indent, str):
  "No-op"
  if len(indent) < 3:
    print "%s%s" % (indent, str)


class PartitioningParallelizer(NaiveParallelizer):
  "This parallelizer works through a queue of currently eligible-to-build targets, but chunks multiple targets together in each compiler invocation, attempting to reach a number of sources per compile specified by a flag."

  def __init__(self, logger, invalid_target_tree, max_num_parallel_compiles, partition_size_hint, compile_cmd, post_compile_cmd = None):
    NaiveParallelizer.__init__(self, logger, invalid_target_tree, max_num_parallel_compiles, compile_cmd, post_compile_cmd)

    self._partition_size_hint = partition_size_hint


  def _attempt_to_place_target_in_set_and_recurse(self, next_target, current_set, current_sets, frontier, indent):

    # Simulate adding the next eligible node to this compile worker's set
    current_set.add_target(next_target)

    # Recurse
    next_best_sets = copy.deepcopy(self._find_best_node_sets(current_sets, frontier, indent + '\t'))

    # Remove the node from this compile worker's set
    current_set.remove_target(next_target)

    return next_best_sets


  def _get_sets_with_dependents_of_node(self, node, sets):

    def node_set_has_dependents_of_next_node(current_set):
      # Determine whether the given set includes any of next_node's dependencies
      children_data = set([child.data for child in node.invalidated_children])
      return len(children_data.intersection(current_set.targets)) > 0

    return filter(node_set_has_dependents_of_next_node, sets.sets)


  def _find_best_sets_place_node(self, current_sets, new_frontier, next_node, indent):

    if current_sets.num_sources and current_sets.num_sources + next_node.data.num_sources > self._partition_size_hint:
      return current_sets

    best_sets = current_sets

    #new_frontier.remove(next_node)
    new_frontier_nodes = self._tree.invalidate_leaf(next_node)
    new_frontier.update(new_frontier_nodes)

    # Filter the existing target sets to just ones that already include dependencies of next_node.
    sets_that_include_next_node_dependents = self._get_sets_with_dependents_of_node(next_node, current_sets)

    if len(sets_that_include_next_node_dependents) == 1:
      # If exactly one target set has dependencies of next_node, next_node can only go in that target.
      p(indent, "   must place %s in set: %s" % (next_node.data.id, str(list(sets_that_include_next_node_dependents)[0])))
      next_best_sets = self._attempt_to_place_target_in_set_and_recurse(next_node.data, sets_that_include_next_node_dependents.pop(), current_sets, new_frontier, indent)
      if next_best_sets > best_sets:
        p(indent, "   ****new best! %s" % (str(next_best_sets)))
        best_sets = next_best_sets

    elif not sets_that_include_next_node_dependents:
      # If no existing target sets include any of next_node's dependencies, then next_node can potentially go in
      # any of them; try placing next_node in each one and recursing.
      for current_set in current_sets.non_empty_sets:
        p(indent, "   trying %s in set %s" % (next_node.data.id, str(current_set)))
        next_best_sets = self._attempt_to_place_target_in_set_and_recurse(next_node.data, current_set, current_sets, new_frontier, indent)
        if next_best_sets > best_sets:
          p(indent, "   ****new best! %s" % (str(next_best_sets)))
          best_sets = next_best_sets

      if current_sets.empty_sets:
        current_set = list(current_sets.empty_sets)[0]
        p(indent, "   trying %s in *empty* set" % (next_node.data.id))
        next_best_sets = self._attempt_to_place_target_in_set_and_recurse(next_node.data, current_set, current_sets, new_frontier, indent)
        if next_best_sets > best_sets:
          p(indent, "   ****new best! %s" % (str(next_best_sets)))
          best_sets = next_best_sets

    # Undo the simulated node removal from the frontier
    new_frontier -= new_frontier_nodes
    new_frontier.add(next_node)
    self._tree.restore_leaf(next_node)

    p(indent, "   ----returning: %s" % (str(best_sets)))
    return best_sets


  def _find_best_node_sets(self, current_sets, frontier, indent = ''):
    if not frontier:
      return current_sets

    #time.sleep(.05)

    p(indent, "_find_best_node_sets:")
    p(indent, "   frontier: {%s}" % (','.join([node.data.id for node in frontier])))
    p(indent, "   current: %s" % (str(current_sets)))

    # Make a copy that we can manipulate without screwing up our iteration over the list
    new_frontier = frontier#copy.copy(frontier)

    # Simulate removing a node from the frontier
    next_node = new_frontier.pop()
    #p(indent, "   inspecting %s" % (next_node.data.id))

    p(indent, "   try skipping '%s'" % (next_node.data.id))
    best_without_next_node = self._find_best_node_sets(current_sets, new_frontier, indent + '\t')
    p(indent, "     best without: %s" % str(best_without_next_node))

    p(indent, "   try placing '%s'" % (next_node.data.id))
    best_with_next_node = self._find_best_sets_place_node(current_sets, new_frontier, next_node, indent + '\t')
    p(indent, "     best with: %s" % str(best_with_next_node))

    return max(best_with_next_node, best_without_next_node)


  def _get_next_node_sets_to_compile(self, num_compile_workers_available):
    """Get a new frontier node, if any is ready to be compiled (i.e. it doesn't depend on any compiling target sets."""
    print "**_get_next_node_sets_to_compile (%d)" % num_compile_workers_available
    #self._tree.print_tree()

    best_sets = self._find_best_node_sets(TargetSets(num_compile_workers_available), self._frontier_nodes)
    best_node_sets = [set([self._tree._nodes_by_data_map[t] for t in target_set.targets]) for target_set in best_sets.sets]
    print "..got: %s" % str(best_sets)
    return best_node_sets


