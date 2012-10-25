__author__ = 'ryan'


class ParallelCompileError(Exception):
  "Error that is thrown if something goes wrong in the ParallelCompileManager"

class ParallelCompileManager(object):
  def __init__(self, logger, invalid_target_tree, max_num_parallel_compiles, compile_cmd, post_compile_cmd = None):
    self._logger = logger

    # The maximum number of parallel compiles allowed.
    self._max_num_parallel_compiles = max_num_parallel_compiles

    # Pass a node's VersionedTarget to this function to compile it.
    self._compile_cmd = compile_cmd

    self._post_compile_cmd = post_compile_cmd

    # Tree nodes that are currently compiling
    self._in_flight_target_nodes = set([])

    # Processes that are currently compiling
    self._compile_processes = set([])

    # Map from each compiling process to the node that it is compiling
    self._compiling_nodes_by_process = {}

    # Set of nodes that can currently be compiled (i.e. that don't depend on anything that hasn't already been
    # compiled).
    self._frontier_nodes = set([leaf for leaf in invalid_target_tree.leaves])

    self._tree = invalid_target_tree

    self._completed_compiles = set([])

  def _get_next_frontier_node(self):
    """Get a new frontier node, if any is ready to be compiled (i.e. it doesn't depend on any compiling target sets."""
    if len(self._frontier_nodes) > 0:
      return list(self._frontier_nodes)[0]
    return None


  def _assert_target_in_frontier(self, target_node):
    "Raise an exception if the given node is not in the frontier set."
    if target_node not in self._frontier_nodes:
      raise ParallelCompileError(
        ("Next target %s is not in frontier set {%s}" % target_node.id, ','.join(t.id for t in self._frontier_nodes)))


  def _add_eligible_parents_to_frontier(self, target_node):
    "Add a node's parents to the frontier set, excepting any that are also ancestors of another of its parents."
    for parent_node in target_node.parents:
      if (parent_node in self._completed_compiles or
          parent_node in self._in_flight_target_nodes or
          parent_node in self._frontier_nodes):
        continue
      parent_is_eligible = True
      for sibling_node in parent_node.children:
        if sibling_node not in self._completed_compiles:
          parent_is_eligible = False
          break
      if parent_is_eligible:
        print "\tadding newly eligible parent of %s: %s" % (target_node.data.target.id, parent_node.data.target.id)
        self._frontier_nodes.add(parent_node)


  def _remove_from_frontier(self, target_node):
    """Remove a "frontier" (leaf) target from our set of leaves and add its parents to the new frontier"""
    self._assert_target_in_frontier(target_node)
    self._frontier_nodes.remove(target_node)


  def _spawn_target_compile(self, target_node):
    "Start compiling a given VersionedTarget"
    self._logger.info("\n*** Spawning compile: %s\n" % target_node.data.id)
    compile_process = self._compile_cmd(target_node.data)
    if compile_process:
      # NOTE(ryan): this can happen if the target had no sources, therefore compile_cmd did not result in a process
      # being spawned
      self._compiling_nodes_by_process[compile_process] = target_node
      self._compile_processes.add(compile_process)
      self._in_flight_target_nodes.add(target_node)

    # Remove from the frontier either way.
    self._remove_from_frontier(target_node)


  def _handle_compilation_finished(self, compile_process):
    "Clean up a finished compilation process."
    self._logger.info(
      "\n*** Finished compiling: %s\n" % self._compiling_nodes_by_process[compile_process].data.id)
    self._compile_processes.remove(compile_process)

    target_node = self._compiling_nodes_by_process[compile_process]

    if self._post_compile_cmd:
      self._post_compile_cmd(target_node.data)

    self._in_flight_target_nodes.remove(target_node)
    self._completed_compiles.add(target_node)
    self._add_eligible_parents_to_frontier(target_node)

    del self._compiling_nodes_by_process[compile_process]


  def _poll_compile_processes(self):
    "Clean up any compiles that have finished. If any have failed, kill all others and return."
    finished_compiles = []
    for compile_process in self._compile_processes:
      if compile_process == None:
        print "\n******\nwtf? got None compile process\n*******\n"
        #self._compile_processes.remove(None)
        if None in self._compiling_nodes_by_process:
          print "target: %s" % self._compiling_nodes_by_process[None].data.target.id
          #del self._compiling_nodes_by_process[None]
        finished_compiles.append(compile_process)
        continue
      poll_value = compile_process.poll()
      if poll_value != None:
        finished_compiles.append(compile_process)
        if poll_value != 0:
          # If a compile fails, kill the others and return
          # TODO(ryan): check whether early kills work, particularly before finished compiles are removed.
          # self._kill_running_compiles()
          return False

    # Do this outside the loop so as to not change the size of the set the loop is iterating over
    # (self._compiling_processes)
    [self._handle_compilation_finished(compile_process) for compile_process in finished_compiles]

    return True


  def _kill_running_compiles(self):
    "Terminate all running compile processes"
    for compile_process in self._compile_processes:
      compile_process.terminate()


  def _loop_once(self):
    while len(self._compile_processes) < self._max_num_parallel_compiles:
      # We have room to spawn another compile
      next_target_node = self._get_next_frontier_node()
      if next_target_node:
        self._spawn_target_compile(next_target_node)
      else:
        break


    if not self._poll_compile_processes():
      return False
    return True


  def execute(self):
    """As long as there are "frontier" targets to compile, execute the following loop:
         - spawn a new compile if we're below the limit, and
         - poll the currently running compiles to see if any are done."""

    while len(self._frontier_nodes) > 0 or len(self._in_flight_target_nodes) > 0:
      if not self._loop_once():
        break

    print "\nFrontier is empty after compiling %d targets out of %d:" % (len(self._completed_compiles), len(self._tree.nodes))
    for node in self._completed_compiles:
      print "\t%s" % node.data.target.id
    print ''

    print "%d still in flight:" % len(self._in_flight_target_nodes)
    for node in self._in_flight_target_nodes:
      print "\t%s" % node.data.target.id
    print ''

    # Once the last of the targets has been sent off to compile, wait around for those last compiles to finish.
    success = True
    for compile_process in self._compile_processes:
      compile_process.wait()
      if compile_process.returncode != 0:
        success = False

    return success
#    while len(self._in_flight_target_nodes) > 0:
#      if not self._poll_compile_processes():
#        return False
#
#    return True
