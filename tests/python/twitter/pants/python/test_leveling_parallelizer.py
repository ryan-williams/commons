__author__ = 'ryan'

import unittest
from twitter.pants.python.leveling_parallelizer import LevelingParallelizer
from twitter.pants.test import ParallelizerTest, TestTree, MockLogger
from twitter.pants.test.sample_trees import *

class LevelingParallelizerTest(ParallelizerTest):

  def check(self, tree, max_num_parallel_compiles, expected_max, expected_min):
    lp = LevelingParallelizer(MockLogger(), tree.tree, max_num_parallel_compiles, None, None)

    node_sets = lp._get_next_node_sets_to_compile(max_num_parallel_compiles)

    sizes = [sum([n.data.num_sources for n in node_set]) for node_set in node_sets]

    self.assertEquals(max(sizes), expected_max)
    self.assertEquals(min(sizes), expected_min)

    #self.check_next_node_sets(lp, tree.tree, max_num_parallel_compiles, expected_lists)

#  def test_boot(self):
#    t = TestTree(boot)
#
#    self.check(t, 1, 24, 24)  # {12,5,2,1,1,1,1,1}
#    self.check(t, 2, 12, 12)  # {12}, {5,2,1,1,1,1,1}
#    self.check(t, 3, 12, 6)   # {12}, {5,1}, {2,1,1,1,1}
#    self.check(t, 4, 12, 3)   # {12}, {5}, {2,1,1}, {1,1,1}
#    self.check(t, 5, 12, 2)   # {12}, {5}, {2,1}, {1,1,1}, {1,1}
#    self.check(t, 6, 12, 1)   # {12}, {5}, {2}, {1,1}, {1,1}, {1}
#    self.check(t, 7, 12, 1)   # {12}, {5}, {2}, {1,1}, {1}, {1}, {1}
#    self.check(t, 8, 12, 1)   # {12}, {5}, {2}, {1}, {1}, {1}, {1}, {1}
#    self.check(t, 9, 12, 0)   # {12}, {5}, {2}, {1}, {1}, {1}, {1}, {1}, {}


  def test_boot_full(self):
    t = TestTree(boot)

    lp = LevelingParallelizer(MockLogger(), t.tree, 4, None, None)

    levels = lp.get_full_graph_partition(4)

    self.assertEquals(len(levels), 11)


  def test_pages_full(self):
    t = TestTree(frontend_pages)

    lp = LevelingParallelizer(MockLogger(), t.tree, 4, None, None)

    levels = lp.get_full_graph_partition(4)

    self.assertEquals(len(levels), 0)

#  def test_pages(self):
#    t = TestTree(frontend_pages)
#
#    self.check(t, 2, 36, 35)  # {27,6,3}, {5,4,2*6,1*14}
#    self.check(t, 3, 27, 22)  # {27}, {6,5,4,3,2,2}, {2*4,1*14}
#    self.check(t, 4, 27, 14)  # {27}, {6,5,4}, {3,2*6}, {1*14}
#    self.check(t, 5, 27, 11)  # {27}, {6,5}, {4,3,2,2}, {2*4,1*3}, {1*11}
#    self.check(t, 6, 27, 8)   # {27}, {6,3}, {5,4}, {2*4,1}, {2*2,1*5}, {1*8}
#    self.check(t, 7, 27, 7)
#    self.check(t, 8, 27, 6)
#    self.check(t, 9, 27, 5)
#    self.check(t, 10, 27, 4)
#
#    self.check(t, 25, 27, 1)
#    self.check(t, 26, 27, 0)
