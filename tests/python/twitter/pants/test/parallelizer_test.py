__author__ = 'ryan'

import unittest

class ParallelizerTest(unittest.TestCase):

  def check_next_node_sets(self, parallelizer, tree, num_sets, expected_target_lists):

    next_node_sets = parallelizer._get_next_node_sets_to_compile(num_sets)

    expected_node_sets = sorted([sorted([tree._nodes_by_data_map[t] for t in s]) for s in expected_target_lists])

    next_node_sets = sorted([sorted(list(s)) for s in next_node_sets])

    #    from pprint import pprint
    #
    #    pprint(expected_node_sets)
    #    pprint(next_node_sets)

    self.assertEquals(len(expected_node_sets), len(next_node_sets))
    self.assertEquals(expected_node_sets, next_node_sets)

