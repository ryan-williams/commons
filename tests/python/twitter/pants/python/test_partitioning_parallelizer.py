__author__ = 'ryan'

import unittest

from twitter.pants.base import DoubleTree
from twitter.pants.python.partitioning_parallelizer import PartitioningParallelizer, CompileTargetSets, CompileTargetSet
from twitter.pants.test import MockLogger, MockTarget


class TestTree(object):
  def __init__(self, deps):
    self.deps = deps

    target_ids = set()
    for id, vals in deps.iteritems():
      target_ids.add(id)
      children_ids = vals["children"]
      target_ids.update(children_ids)
      for child_id in children_ids:
        if not child_id in deps:
          raise Exception("Invalid tree. Child id %s not found in deps" % child_id)

    self.targets_by_id = {}
    self.targets = [self._get_target_by_id(id) for id in deps]
    self.tree = DoubleTree(self.targets, lambda t: t.dependencies)

  def _get_target_by_id(self, id):
    if id in self.targets_by_id:
      return self.targets_by_id[id]

    child_ids = self.deps[id]['children']
    child_targets = set([self._get_target_by_id(child_id) for child_id in child_ids])

    target = MockTarget(id, child_targets, self.deps[id]['num'])
    self.targets_by_id[id] = target
    return target

  def __getattr__(self, id):
    return self._get_target_by_id(id)

class PartitioningParallelizerTest(unittest.TestCase):

  def test_single_sets_cmp(self):
    a = MockTarget('a', [], 1)
    b = MockTarget('b', [], 1)
    c = MockTarget('c', [], 2)
    d = MockTarget('d', [], 1)
    e = MockTarget('e', [], 1)

    set1 = CompileTargetSets(1)
    set2 = CompileTargetSets(1)

    self.assertTrue(set1 == set2)
    self.assertFalse(set1 > set2)
    self.assertFalse(set1 < set2)

    set1.sets[0].add_target(a)

    self.assertFalse(set1 == set2)
    self.assertTrue(set1 > set2)
    self.assertTrue(set2 < set1)

    set1.sets[0].add_target(b)

    self.assertFalse(set1 == set2)
    self.assertTrue(set1 > set2)
    self.assertTrue(set2 < set1)

    set2.sets[0].add_target(c)

    self.assertTrue(set1 == set2)
    self.assertFalse(set1 > set2)
    self.assertFalse(set1 < set2)

    set2.sets[0].add_target(d)

    self.assertFalse(set1 == set2)
    self.assertTrue(set2 > set1)
    self.assertTrue(set1 < set2)

    set1.sets[0].add_target(e)

    self.assertTrue(set1 == set2)
    self.assertFalse(set1.__gt__(set2))
    self.assertFalse(set2 < set1)


  def test_multiple_sets_cmp(self):
    a = MockTarget('a', [], 1)
    b = MockTarget('b', [], 1)
    c = MockTarget('c', [], 1)
    d = MockTarget('d', [], 2)
    e = MockTarget('e', [], 1)

    set1 = CompileTargetSets(3)
    set2 = CompileTargetSets(3)

    set1.sets[0].add_target(a)
    set1.sets[1].add_target(b)
    set1.sets[2].add_target(c)

    set2.sets[0].add_target(d)
    set2.sets[1].add_target(e)

    self.assertFalse(set1 == set2)
    self.assertTrue(set1 > set2)
    self.assertTrue(set2 < set1)


  def check_next_node_sets(self, tree, num_sets, partition_size_hint, expected_target_lists):

    pp = PartitioningParallelizer(MockLogger(), tree, 1, partition_size_hint, None, None)

    next_node_sets = pp._get_next_node_sets_to_compile(num_sets)

#    expected_node_sets = []
#    for target_list in expected_target_lists:
#      node_list = []
#      for target in target_list:
#        node = tree._nodes_by_data_map[target]
#        node_list.append(node)
#      expected_node_sets.append(node_list)
#
      #expected_node_sets.append([tree._nodes_by_data_map[t] for t in tl])

    expected_node_sets = [[tree._nodes_by_data_map[t] for t in s] for s in expected_target_lists]

    self.assertEquals(len(expected_node_sets), len(next_node_sets))
    self.assertEquals([set(s) for s in expected_node_sets], next_node_sets)

  def test_get_next_nodes(self):
    a = MockTarget('a', [], 1)
    b = MockTarget('b', [a], 1)
    c = MockTarget('c', [b], 2)
    d = MockTarget('d', [c, a], 1)
    e = MockTarget('e', [d], 1)

    tree = DoubleTree([a,b,c,d,e], lambda t: t.dependencies)

    def test_next_node_sets(num_sets, partition_size_hint, expected_sets):
      self.check_next_node_sets(tree, num_sets, partition_size_hint, expected_sets)

    test_next_node_sets(1, 0, [[a]])
    test_next_node_sets(1, 1, [[a]])
    test_next_node_sets(1, 2, [[a,b]])
    test_next_node_sets(1, 3, [[a,b]])
    test_next_node_sets(1, 4, [[a,b,c]])
    test_next_node_sets(1, 5, [[a,b,c,d]])
    test_next_node_sets(1, 6, [[a,b,c,d,e]])
    test_next_node_sets(1, 10, [[a,b,c,d,e]])

    test_next_node_sets(2, 0, [[a],[]])
    test_next_node_sets(2, 1, [[a],[]])
    test_next_node_sets(2, 2, [[a,b],[]])
    test_next_node_sets(2, 3, [[a,b],[]])
    test_next_node_sets(2, 4, [[a,b,c],[]])

    test_next_node_sets(3, 0, [[a],[],[]])
    test_next_node_sets(3, 1, [[a],[],[]])
    test_next_node_sets(3, 2, [[a,b],[],[]])
    test_next_node_sets(3, 3, [[a,b],[],[]])


  def test_base2(self):
    deps = {}
    deps["config"] = {"num": 5, "children": []}
    deps["recordv2"] = {"num": 12, "children": []}
    deps["reflection"] = {"num": 1, "children": []}
    deps["json"] = {"num": 6, "children": ["recordv2","reflection"]}
    deps["base2"] = {"num": 30, "children": ["config","json"]}

    t = TestTree(deps)

    self.check_next_node_sets(t.tree, 4, 200, [t.targets, [], [], []])
    self.check_next_node_sets(t.tree, 4, 10, [[t.recordv2], [t.config, t.reflection], [], []])
    self.check_next_node_sets(t.tree, 4, 20, [[t.recordv2, t.reflection, t.json], [t.config], [], []])
    self.check_next_node_sets(t.tree, 4, 30, [[t.recordv2, t.reflection, t.json], [t.config], [], []])
    self.check_next_node_sets(t.tree, 4, 60, [[t.recordv2, t.reflection, t.json, t.config, t.base2], [], [], []])





