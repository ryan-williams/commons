__author__ = 'ryan'

import unittest

import os
import sys
from twitter.pants.test import ParallelizerTest
from twitter.pants.python.partitioning_parallelizer import PartitioningParallelizer
from twitter.pants.python.target_sets import TargetSets
from twitter.pants.test import MockLogger, MockTarget, TestTree
from twitter.pants.test.sample_trees import *


class PartitioningParallelizerTest(ParallelizerTest):

  def check(self, tree, num_sets, partition_hint, expected_target_lists):

    pp = PartitioningParallelizer(MockLogger(), tree.tree, max_num_parallel, partition_hint, None, None)

    self.check_next_node_sets(pp, tree.tree, num_sets, expected_target_lists)


  def test_single_sets_cmp(self):
    a = MockTarget('a', [], 1)
    b = MockTarget('b', [], 1)
    c = MockTarget('c', [], 2)
    d = MockTarget('d', [], 1)
    e = MockTarget('e', [], 1)

    set1 = TargetSets(1)
    set2 = TargetSets(1)

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

    set1 = TargetSets(3)
    set2 = TargetSets(3)

    set1.sets[0].add_target(a)
    set1.sets[1].add_target(b)
    set1.sets[2].add_target(c)

    set2.sets[0].add_target(d)
    set2.sets[1].add_target(e)

    self.assertFalse(set1 == set2)
    self.assertTrue(set1 > set2)
    self.assertTrue(set2 < set1)



#  def test_get_next_nodes(self):
#    a = MockTarget('a', [], 1)
#    b = MockTarget('b', [a], 1)
#    c = MockTarget('c', [b], 2)
#    d = MockTarget('d', [c, a], 1)
#    e = MockTarget('e', [d], 1)
#
#    tree = DoubleTree([a,b,c,d,e], lambda t: t.dependencies)
#
#    def test_next_node_sets(num_sets, partition_size_hint, expected_sets):
#      self.check(tree, num_sets, partition_size_hint, expected_sets)
#
#    test_next_node_sets(1, 0, [[a]])
#    test_next_node_sets(1, 1, [[a]])
#    test_next_node_sets(1, 2, [[a,b]])
#    test_next_node_sets(1, 3, [[a,b]])
#    test_next_node_sets(1, 4, [[a,b,c]])
#    test_next_node_sets(1, 5, [[a,b,c,d]])
#    test_next_node_sets(1, 6, [[a,b,c,d,e]])
#    test_next_node_sets(1, 10, [[a,b,c,d,e]])
#
#    test_next_node_sets(2, 0, [[a],[]])
#    test_next_node_sets(2, 1, [[a],[]])
#    test_next_node_sets(2, 2, [[a,b],[]])
#    test_next_node_sets(2, 3, [[a,b],[]])
#    test_next_node_sets(2, 4, [[a,b,c],[]])
#
#    test_next_node_sets(3, 0, [[a],[],[]])
#    test_next_node_sets(3, 1, [[a],[],[]])
#    test_next_node_sets(3, 2, [[a,b],[],[]])
#    test_next_node_sets(3, 3, [[a,b],[],[]])
#
#
#  def test_base2(self):
#
#    tree = TestTree(base2)
#
#    self.check(tree, 4, 200, [t.targets, [], [], []])
#    self.check(tree, 4, 10, [[t.recordv2], [t.config, t.reflection], [], []])
#    self.check(tree, 4, 20, [[t.recordv2, t.reflection, t.json], [t.config], [], []])
#    self.check(tree, 4, 30, [[t.recordv2, t.reflection, t.json], [t.config], [], []])
#    self.check(tree, 4, 60, [[t.recordv2, t.reflection, t.json, t.config, t.base2], [], [], []])
#
#
#  def test_record_small(self):
#
#    tree = TestTree(record_small)
#
#    self.check(tree, 4, 200, [[t.acl, t.images, t.temphtml, t["s3-legacy"]], [t.string, t.i18n], [t.record], [t.geo, t["geo-min"]]])
#
#
#  def test_record(self):
#
#    tree = TestTree(record)
#
#    self.check(tree, 4, 200, [t.targets, [], [], []])
#
#
#  def test_boot_small(self):
#
#    tree = TestTree(boot_small)
#
#    self.check(tree, 4, 200, [t.targets, [], [], []])

  def test_boot(self):

    tree = TestTree(boot)

    self.check(tree, 4, 200, [t.targets, [], [], []])

    self.check(tree, 4, 100, [t.targets, [], [], []])


#  def test_frontend_pages(self):
