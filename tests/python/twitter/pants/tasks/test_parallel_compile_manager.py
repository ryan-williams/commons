__author__ = 'ryan'

import unittest

from twitter.pants.tasks import ParallelCompileManager
from twitter.pants.test import MockLogger, MockProcess, MockTarget
from twitter.pants.base import DoubleTree


class ParallelCompileManagerTest(unittest.TestCase):

  def test_parallel_compile(self):

    a = MockTarget('a', [])
    b = MockTarget('b', [])
    c = MockTarget('c', [a, b])

    d = MockTarget('d', [])
    e = MockTarget('e', [])
    f = MockTarget('f', [])
    g = MockTarget('g', [d, e, f])

    mock_subprocesses_by_target = {}
    def add_mock_subprocess_for_target(target, return_vals):
      mock_subprocesses_by_target[target] = MockProcess(target, return_vals)

    # TODO(ryan): abstract these out
    target_compiles_spawned = []
    target_compiles_finished = []

    def cmd(target):
      target_compiles_spawned.append(target)
      return mock_subprocesses_by_target[target]

    def post_compile_cmd(target):
      target_compiles_finished.append(target)

    tree = DoubleTree([a, b, c, d, e, f, g], lambda x: x.dependencies)

    add_mock_subprocess_for_target(a, [0, None, None, None])
    add_mock_subprocess_for_target(b, [0, None, None, None])
    add_mock_subprocess_for_target(d, [0, None, None, None])
    add_mock_subprocess_for_target(e, [0, None, None, None])
    add_mock_subprocess_for_target(f, [0, None, None, None])

    pcm = ParallelCompileManager(MockLogger(), tree, 4, cmd, post_compile_cmd)

    self.assertEquals(len(pcm._in_flight_target_nodes), 0)
    self.assertEquals(len(pcm._compile_processes), 0)
    self.assertEquals(len(pcm._compiling_nodes_by_process), 0)
    self.assertEquals(pcm._frontier_nodes, set([tree.lookup(t) for t in [a,b,d,e,f]]))
    self.assertEquals(pcm._get_next_frontier_node().data, a)
    self.assertEquals(len(target_compiles_spawned), 0)
    self.assertEquals(len(target_compiles_finished), 0)

    pcm._loop_once()

    first_in_flight_target_to_finish = list(pcm._in_flight_target_nodes)[0]
    mock_subprocesses_by_target[first_in_flight_target_to_finish.data].return_vals = [0, None]

    other_in_flight_targets = pcm._in_flight_target_nodes - set([first_in_flight_target_to_finish])
    self.assertEquals(len(other_in_flight_targets), 3)
    eligible_in_flight_nodes = set([tree.lookup(t) for t in [a,b,d,e,f]])
    odd_node_out = list(eligible_in_flight_nodes - pcm._in_flight_target_nodes)[0]

    copied_in_flight_nodes = pcm._in_flight_target_nodes.copy()

    def check_first_four_targets_in_flight():
      self.assertEquals(len(pcm._in_flight_target_nodes), 4)
      self.assertEquals(len(pcm._in_flight_target_nodes - eligible_in_flight_nodes), 0)
      self.assertEquals(len(pcm._compile_processes), 4)
      self.assertEquals(len(pcm._compiling_nodes_by_process), 4)
      self.assertEquals(pcm._frontier_nodes, set([odd_node_out]))
      self.assertEquals(pcm._get_next_frontier_node(), odd_node_out)
      self.assertEquals(len(target_compiles_spawned), 4)
      self.assertEquals(set([tree.lookup(t) for t in target_compiles_spawned]), pcm._in_flight_target_nodes)
      self.assertEquals(len(target_compiles_finished), 0)

    check_first_four_targets_in_flight()

    pcm._loop_once()

    # Second loop: still no compiles finished
    check_first_four_targets_in_flight()

    pcm._loop_once()

    # Third loop: first compile finished, other three still in flight, parent of first finisher added to frontier.
    parent_of_first_finisher = list(first_in_flight_target_to_finish.parents)[0]

    self.assertEquals(pcm._in_flight_target_nodes, other_in_flight_targets)
    self.assertEquals(len(pcm._compile_processes), 3)
    self.assertEquals(len(pcm._compiling_nodes_by_process), 3)
    self.assertEquals(pcm._frontier_nodes, set([parent_of_first_finisher, odd_node_out]))
    self.assertEquals(pcm._get_next_frontier_node(), odd_node_out)
    self.assertEquals(set([tree.lookup(t) for t in target_compiles_spawned]), copied_in_flight_nodes)
    self.assertEquals(set([tree.lookup(t) for t in target_compiles_finished]), set([first_in_flight_target_to_finish]))

    pcm._loop_once()

    # Fourth loop: the remaining three of the original four compiles all finish. The remaining original leaf begins
    # compiling in the slot that the first finisher vacated last loop. Other parent added to fronter.
    self.assertEquals(pcm._in_flight_target_nodes, set([odd_node_out])) # tree.lookup(t) for t in [b,e,f]
    self.assertEquals(len(pcm._compile_processes), 1)
    self.assertEquals(len(pcm._compiling_nodes_by_process), 1)
    self.assertEquals(pcm._frontier_nodes, set([tree.lookup(c), tree.lookup(g)]))
    self.assertEquals(pcm._get_next_frontier_node().data, c)
    self.assertEquals(set(target_compiles_spawned), set([a,b,e,f,d]))
    self.assertEquals(set([tree.lookup(t) for t in target_compiles_finished]), copied_in_flight_nodes)
