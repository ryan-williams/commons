__author__ = 'ryan'

import copy
from twitter.pants.python.parallel_compile_manager import ParallelCompileManager
from target_sets import TargetSets

class LevelingParallelizer(ParallelCompileManager):
  "This parallelizer chunks up the frontier in the most even way it can."

  def __init__(self, logger, invalid_target_tree, max_num_parallel_compiles, compile_cmd, post_compile_cmd = None):
    ParallelCompileManager.__init__(self, logger, invalid_target_tree, max_num_parallel_compiles, compile_cmd, post_compile_cmd)
    self.levels = None
    self.get_full_graph_partition(max_num_parallel_compiles)

    def get_node_set_str(node_set):
      node_set_str = "\t["
      i = 0
      for node in node_set:
        if i > 0:
          node_set_str += ','
        node_set_str += " %s" % node.short_id
        i += 1
      node_set_str += ' ]'
      return node_set_str


  def set_is_better(self, set1, set2):
    return (
      len(set1.non_empty_sets) > len(set2.non_empty_sets) or
      (len(set1.non_empty_sets) == len(set2.non_empty_sets) and
       (set1.min_num_sources > set2.min_num_sources or
        (set1.min_num_sources == set2.min_num_sources and
         set1.max_num_sources < set2.max_num_sources))))


  def _add_target_to_set_and_recurse(self, next_node, frontier, current_set, current_sets, best_sets, indent):

    current_set.add_target(next_node.data)

    next_best_sets = self._find_best_frontier_partition(current_sets, best_sets, frontier, indent + '\t')

    current_set.remove_target(next_node.data)

    return next_best_sets


  def _find_best_frontier_partition(self, current_sets, best_sets, frontier, indent = ''):
    if not frontier:
      if self.set_is_better(current_sets, best_sets):
        print "  ****new best: %s over %s" % (str(current_sets), str(best_sets))
        best_sets = copy.deepcopy(current_sets)
      return best_sets


    next_node = frontier.pop()

    for current_set in current_sets.non_empty_sets:
      best_sets = self._add_target_to_set_and_recurse(next_node, frontier, current_set, current_sets, best_sets, indent)

    if current_sets.empty_sets:
      best_sets = self._add_target_to_set_and_recurse(next_node, frontier, list(current_sets.empty_sets)[0], current_sets, best_sets, indent)

    frontier.add(next_node)

    return best_sets


  def get_full_graph_partition(self, num_compile_workers_available):
    self.levels = []
    node_levels = []
    while self._tree.leaves:
      print "level %d:" % len(self.levels)
      self._frontier_nodes = self._tree.leaves
      node_levels.append(copy.copy(self._frontier_nodes))
      node_sets = self._compute_next_node_sets_to_compile(num_compile_workers_available)
      self._tree.remove_nodes(self._frontier_nodes)
      self.levels.append(node_sets)
      print ''

    while node_levels:
      nodes = node_levels.pop()
      self._tree.restore_nodes(nodes)

    return self.levels

  def _get_next_node_sets_to_compile(self, num_compile_workers_available):
    ""
    if num_compile_workers_available < self._max_num_parallel_compiles:
      return []

    if self.levels:
      return self.levels.pop(0)

    return self._compute_next_node_sets_to_compile(num_compile_workers_available)

  def _compute_next_node_sets_to_compile(self, num_compile_workers_available):

    frontier = sorted(list(self._frontier_nodes), key=lambda x: x.data.num_sources, reverse=True)

    print "\tFrontier: {%s}" % ','.join([str(n.data.num_sources) for n in frontier])

    target_sets = TargetSets(num_compile_workers_available)
    for node in frontier:
      target_sets.min_set.add_target(node.data)

    node_sets = [set([self._tree._nodes_by_data_map[t] for t in target_set.targets]) for target_set in target_sets.sets]
    print "\t**** found sets: %s" % str(target_sets)
    return node_sets
