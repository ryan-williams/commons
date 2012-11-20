__author__ = 'ryan'

from parallel_compile_manager import ParallelCompileManager

class NaiveParallelizer(ParallelCompileManager):
  """Compiles targets one at a time, popping them from a "frontier" set (the set of targets all of whose dependencies
  have already finished compiling, meaning they can be compiled by the next available worker). When a target finished
  being compiled, """

  def _get_next_node_sets_to_compile(self, num_compile_workers_available):
    """Get new frontier nodes, if any are ready to be compiled (i.e. they doesn't depend on any compiling target sets."""
    node_sets_to_compile = []
    for i in range(num_compile_workers_available):
      if len(self._frontier_nodes) > 0:
        next_node = self._frontier_nodes.pop()
        node_sets_to_compile.append(set([next_node]))
      else:
        break
    return node_sets_to_compile
