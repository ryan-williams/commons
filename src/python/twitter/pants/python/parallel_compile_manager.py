__author__ = 'ryan'


class ParallelCompileError(Exception):
  "Error that is thrown if something goes wrong in the ParallelCompileManager"

class ParallelCompileManager(object):
  def __init__(self, logger, invalid_target_tree, max_num_parallel_compiles, compile_cmd, post_compile_cmd = None):
    self._logger = logger

    self._tree = invalid_target_tree

    # The maximum number of parallel compiles allowed.
    self._max_num_parallel_compiles = max_num_parallel_compiles

    # Pass a node's VersionedTarget to this function to compile it.
    self._compile_cmd = compile_cmd

    self._post_compile_cmd = post_compile_cmd

    # Tree nodes that are currently compiling
    self._in_flight_target_nodes = set([])

    # Set of nodes that can currently be compiled (i.e. that don't depend on anything that hasn't already been
    # compiled). This should always equal self._tree.leaves - self._in_flight_target_nodes
    self._frontier_nodes = set([leaf for leaf in invalid_target_tree.leaves])

    # Processes that are currently compiling
    self._compile_processes = set([])

    # Map from each compiling process to the node that it is compiling
    self._compiling_nodes_by_process = {}

    self._processed_nodes = []


  def _get_next_node_sets_to_compile(self, num_compile_workers_available):
    "Abstract: subclasses implement different strategies for selecting next nodes to be compiled"

  def _handle_processed_node_set(self, target_node_set, compiled_successfully):
    "Add a node's parents to the frontier set, excepting any that are also ancestors of another of its parents."
    if compiled_successfully and self._post_compile_cmd:
      self._post_compile_cmd(target_node_set)

    self._processed_nodes += target_node_set
    print "Processed %d out of %d targets" % (len(self._processed_nodes), len(self._tree.nodes))
    print "In flight (%d): {%s}" % (len(self._in_flight_target_nodes), ','.join([t.data.id for t in self._in_flight_target_nodes]))
    print "Frontier (%d): {%s}" % (len(self._frontier_nodes), ','.join(t.data.id for t in self._frontier_nodes))

    for target_node in target_node_set:
      new_leaves = self._tree.remove_leaf(target_node)

      print "\tadding newly eligible parents of %s:\n" % target_node.data.target.id
      for new_leaf in new_leaves:
        print "\t%s" % new_leaf.data.target.id

      self._frontier_nodes.update(new_leaves)


  def _spawn_target_compile(self, target_node_set):
    "Start compiling a given VersionedTarget"
    self._logger.info("\n*** Spawning compile: %s\n" % str(target_node_set))
    compile_process = self._compile_cmd(target_node_set)
    self._frontier_nodes -= target_node_set
    if compile_process:
      self._compiling_nodes_by_process[compile_process] = target_node_set
      self._compile_processes.add(compile_process)
      self._in_flight_target_nodes.update(target_node_set)
    else:
      # NOTE(ryan): this can happen if the targets had no sources, therefore compile_cmd did not result in a process
      # being spawned. In that case, mark these nodes as having been "processed".
      self._handle_processed_node_set(target_node_set, False)

  def _handle_compilation_finished(self, compile_process, success):
    "Clean up a finished compilation process."
    self._logger.info(
      "\n*** Finished compiling: {%s}\n" % ','.join(node.data.id for node in self._compiling_nodes_by_process[compile_process]))
    self._compile_processes.remove(compile_process)

    target_node_set = self._compiling_nodes_by_process[compile_process]
    del self._compiling_nodes_by_process[compile_process]

    self._in_flight_target_nodes -= (target_node_set)

    self._handle_processed_node_set(target_node_set, success)


  def _poll_compile_processes(self):
    "Clean up any compiles that have finished. If any have failed, kill all others and return."
    finished_compiles = []
    found_failure = False
    for compile_process in self._compile_processes:
      poll_value = compile_process.poll()
      if poll_value != None:
        finished_compiles.append(compile_process)
        if poll_value != 0:
          # If a compile fails, kill the others and return
          # TODO(ryan): check whether early kills work, particularly before finished compiles are removed.
          # self._kill_running_compiles()
          found_failure = True

    # Do this outside the loop so as to not change the size of the set the loop is iterating over
    # (self._compiling_processes)
    [self._handle_compilation_finished(compile_process, found_failure) for compile_process in finished_compiles]

    return not found_failure


  def _kill_running_compiles(self):
    "Terminate all running compile processes"
    for compile_process in self._compile_processes:
      compile_process.terminate()


  def _loop_once(self):
    "Broke this out as a separate method for ease of testing"

    num_compile_workers_available = self._max_num_parallel_compiles - len(self._compile_processes)

    # NOTE(ryan): a good optimization here might be to start computing what the next-compiled partition should be, while we wait for in-flight compiles to finish.
    if num_compile_workers_available > 0 and len(self._frontier_nodes) > 0:
      # We have room to spawn more compiles
      next_target_node_sets = self._get_next_node_sets_to_compile(num_compile_workers_available)
      for next_target_node_set in next_target_node_sets:
        self._spawn_target_compile(next_target_node_set)

    if not self._poll_compile_processes():
      return False
    return True


  def execute(self):
    """Until we've processed all targets, execute the following loop:
         - spawn a new compile if we're below the limit of concurrently running compiles, and
         - poll the currently running compiles to see if any are done."""

    num_nodes = len(self._tree.nodes)
    while len(self._processed_nodes) < num_nodes:
      if not self._loop_once():
        break

    print "\n%s after compiling %d targets out of %d:" % (
      "Nothing left to spawn" if len(self._processed_nodes) == num_nodes else "Caught failure",
      len(self._processed_nodes),
      len(self._tree.nodes))
    for node in self._processed_nodes:
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
