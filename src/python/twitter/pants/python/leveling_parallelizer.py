__author__ = 'ryan'

import copy
from twitter.pants.python.parallel_compile_manager import ParallelCompileManager
from target_sets import TargetSets

def p(indent, str):
  "No-op"
  if len(indent) < 3:
    print "%s%s" % (indent, str)

class LevelingParallelizer(ParallelCompileManager):
  "This parallelizer chunks up the frontier in the most even way it can."

  def set_is_better(self, set1, set2):
    return (
      len(set1.non_empty_sets) > len(set2.non_empty_sets) or
      (len(set1.non_empty_sets) == len(set2.non_empty_sets) and
       (set1.min_num_sources > set2.min_num_sources or
        (set1.min_num_sources == set2.min_num_sources and
         set1.max_num_sources < set2.max_num_sources))))

  def _add_target_to_set_and_recurse(self, next_node, frontier, current_set, current_sets, best_sets, indent):

    p(indent, "  adding %s to set %s" % (next_node.data.id, str(current_set)))

    current_set.add_target(next_node.data)

#    p(indent, "  added: %s. %d empty, %d not" % (str(current_sets), len(current_sets.empty_sets), len(current_sets.non_empty_sets)))

    next_best_sets = self._find_best_frontier_partition(current_sets, best_sets, frontier, indent + '\t')

#    if next_best_sets.min_num_sources > best_sets.min_num_sources:
#      p(indent, "  ****new best: %s over %s" % (str(next_best_sets), str(best_sets)))
#      best_sets = copy.deepcopy(next_best_sets)
#
#    p(indent, "  removing: %s" % str(current_sets))

    current_set.remove_target(next_node.data)

    return next_best_sets


  def _find_best_frontier_partition(self, current_sets, best_sets, frontier, indent = ''):
    if not frontier:
      if self.set_is_better(current_sets, best_sets):
#        p(indent, "  ****new best: %s over %s" % (str(current_sets), str(best_sets)))
        print "  ****new best: %s over %s" % (str(current_sets), str(best_sets))
        best_sets = copy.deepcopy(current_sets)
      return best_sets


    p(indent, "Searching from: {%s}, %s. %d non-empty, %d empty" % (
      ','.join([t.data.id for t in frontier]),
      str(current_sets),
      len(current_sets.non_empty_sets),
      len(current_sets.empty_sets)))

    next_node = frontier.pop()

    for current_set in current_sets.non_empty_sets:
      #p(indent, " non-empty:")
      best_sets = self._add_target_to_set_and_recurse(next_node, frontier, current_set, current_sets, best_sets, indent)

    if current_sets.empty_sets:
      #p(indent, " empty:")
      best_sets = self._add_target_to_set_and_recurse(next_node, frontier, list(current_sets.empty_sets)[0], current_sets, best_sets, indent)

    frontier.add(next_node)

    return best_sets


  def get_full_graph_partition(self, num_compile_workers_available):
    levels = []
    node_levels = []
    while self._tree.leaves:
      print "level %d:" % len(levels)
      self._frontier_nodes = self._tree.leaves
      node_levels.append(copy.copy(self._frontier_nodes))
      node_sets = self._get_next_node_sets_to_compile(num_compile_workers_available)
      #nodes = [node for node_set in node_sets for node in node_set]
      self._tree.remove_nodes(self._frontier_nodes)
      levels.append(node_sets)

    print "Restoring tree:"
    while node_levels:
      nodes = node_levels.pop()
      print "\t{%s}" % ','.join([n.data.id for n in nodes])
      self._tree.restore_nodes(nodes)

    self._tree.print_tree()
    return levels

  def _get_next_node_sets_to_compile(self, num_compile_workers_available):
    ""
    if num_compile_workers_available < self._max_num_parallel_compiles:
      return []

    frontier = sorted(list(self._frontier_nodes), key=lambda x: x.data.num_sources, reverse=True)

#    print "Frontier: "
#    for node in frontier:
#      print "\t%d\t%s" % (node.data.num_sources, node.data.id)
#    print ''

    print "Frontier: {%s}" % ','.join([str(n.data.num_sources) for n in frontier])

    target_sets = TargetSets(num_compile_workers_available)
    for node in frontier:
      target_sets.min_set.add_target(node.data)

    node_sets = [set([self._tree._nodes_by_data_map[t] for t in target_set.targets]) for target_set in target_sets.sets]
    print " ** found sets: %s" % str(target_sets)
    return node_sets
    #best_sets = self._find_best_frontier_partition(TargetSets(num_compile_workers_available), TargetSets(num_compile_workers_available), self._frontier_nodes)
    #best_node_sets = [set([self._tree._nodes_by_data_map[t] for t in target_set.targets]) for target_set in best_sets.sets]
    #return best_node_sets
