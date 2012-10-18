__author__ = 'ryan'

import unittest

from twitter.pants.base import DoubleTree
from twitter.pants.test import MockTarget


class DoubleTreeTest(unittest.TestCase):

  def check_tree_node(self, node, data, ancestor_levels, descendent_levels, children, parents):
    self.assertEquals(node.data, data)
    self.assertEquals(node.ancestor_levels, ancestor_levels)
    self.assertEquals(node.descendent_levels, descendent_levels)
    self.assertEquals(set(node.children), set(children))
    self.assertEquals(set(node.parents), set(parents))

  def test_simple_tree(self):
    a = MockTarget('a')
    b = MockTarget('b', [a])
    c = MockTarget('c', [b])
    d = MockTarget('d', [c, a])
    e = MockTarget('e', [d])

    def test_tree(tree):
      A = tree.lookup(a)
      B = tree.lookup(b)
      C = tree.lookup(c)
      D = tree.lookup(d)
      E = tree.lookup(e)

      self.assertEquals(tree._roots, set([E]))
      self.assertEquals(tree.leaves, set([A]))

      self.check_tree_node(E, e, 0, 4, [ D ], [])
      self.check_tree_node(D, d, 1, 3, [ A, C ], [ E ])
      self.check_tree_node(C, c, 2, 2, [ B ], [ D ])
      self.check_tree_node(B, b, 3, 1, [ A ], [ C ])
      self.check_tree_node(A, a, 4, 0, [], [ B, D ])

    test_tree(DoubleTree([ e, d, c, b, a ], lambda t: t.dependencies))
    test_tree(DoubleTree([ a, b, c, d, e ], lambda t: t.dependencies))
    test_tree(DoubleTree([ a, b, e, d, c ], lambda t: t.dependencies))
    test_tree(DoubleTree([ d, a, c, e, b ], lambda t: t.dependencies))


  def test_binary_search_tree(self):
    rrr = MockTarget('rrr')
    rrl = MockTarget('rrl')
    rlr = MockTarget('rlr')
    rll = MockTarget('rll')
    lrr = MockTarget('lrr')
    lrl = MockTarget('lrl')
    llr = MockTarget('llr')
    lll = MockTarget('lll')

    rr = MockTarget('rr', [rrr, rrl])
    rl = MockTarget('rl', [rlr, rll])
    lr = MockTarget('lr', [lrr, lrl])
    ll = MockTarget('ll', [llr, lll])

    r = MockTarget('r', [rr, rl])
    l = MockTarget('l', [lr, ll])

    root = MockTarget('root', [r, l])

    def test_tree(tree):

      self.assertEquals(tree._roots, set([tree.lookup(root)]))
      self.assertEquals(tree.leaves,
        set([ tree.lookup(id) for id in [rrr, rrl, rlr, rll, lrr, lrl, llr, lll] ]))

      self.check_tree_node(tree.lookup(root), root, 0, 3, [tree.lookup(r), tree.lookup(l)], [])

      self.check_tree_node(tree.lookup(r), r, 1, 2, [tree.lookup(rl), tree.lookup(rr)], [ tree.lookup(root)])
      self.check_tree_node(tree.lookup(l), l, 1, 2, [tree.lookup(ll), tree.lookup(lr)], [ tree.lookup(root)])

      self.check_tree_node(tree.lookup(rr), rr, 2, 1, [tree.lookup(rrl), tree.lookup(rrr)], [ tree.lookup(r)])
      self.check_tree_node(tree.lookup(rl), rl, 2, 1, [tree.lookup(rll), tree.lookup(rlr)], [ tree.lookup(r)])
      self.check_tree_node(tree.lookup(lr), lr, 2, 1, [tree.lookup(lrl), tree.lookup(lrr)], [ tree.lookup(l)])
      self.check_tree_node(tree.lookup(ll), ll, 2, 1, [tree.lookup(lll), tree.lookup(llr)], [ tree.lookup(l)])

      self.check_tree_node(tree.lookup(rrr), rrr, 3, 0, [], [ tree.lookup(rr)])
      self.check_tree_node(tree.lookup(rrl), rrl, 3, 0, [], [ tree.lookup(rr)])
      self.check_tree_node(tree.lookup(rlr), rlr, 3, 0, [], [ tree.lookup(rl)])
      self.check_tree_node(tree.lookup(rll), rll, 3, 0, [], [ tree.lookup(rl)])
      self.check_tree_node(tree.lookup(lrr), lrr, 3, 0, [], [ tree.lookup(lr)])
      self.check_tree_node(tree.lookup(lrl), lrl, 3, 0, [], [ tree.lookup(lr)])
      self.check_tree_node(tree.lookup(llr), llr, 3, 0, [], [ tree.lookup(ll)])
      self.check_tree_node(tree.lookup(lll), lll, 3, 0, [], [ tree.lookup(ll)])

    # Test in order
    test_tree(DoubleTree([ root, r, l, rr, rl, lr, ll, rrr, rrl, rlr, rll, lrr, lrl, llr, lll ], lambda t: t.dependencies))

    # Test a couple of randomly chosen orders
    test_tree(DoubleTree([ lrl, r, root, rl, rrr, rll, lr, lrr, ll, lll, l, rr, rrl, rlr, llr ], lambda t: t.dependencies))
    test_tree(DoubleTree([ ll, rrl, lrl, rl, rlr, lr, root, rrr, rll, r, llr, rr, lrr, l, lll ], lambda t: t.dependencies))
    test_tree(DoubleTree([ rr, rlr, rl, rrr, rrl, l, root, lr, lrr, llr, r, rll, lrl, ll, lll ], lambda t: t.dependencies))
    test_tree(DoubleTree([ l, lll, rrr, rll, ll, lrl, llr, rl, root, r, lr, rlr, rr, lrr, rrl ], lambda t: t.dependencies))

  def test_diamond_in_different_orders(self):
    a = MockTarget('a')
    b = MockTarget('b', [a])
    c = MockTarget('c', [a])
    d = MockTarget('d', [c, b])

    def test_diamond_tree(tree):
      self.assertEquals(tree._roots, set([tree.lookup(d)]))
      self.assertEquals(tree.leaves, set([tree.lookup(a)]))
      self.check_tree_node(tree.lookup(d), d, 0, 2, [tree.lookup(b), tree.lookup(c)], [])
      self.check_tree_node(tree.lookup(c), c, 1, 1, [tree.lookup(a)], [tree.lookup(d)])
      self.check_tree_node(tree.lookup(b), b, 1, 1, [tree.lookup(a)], [tree.lookup(d)])
      self.check_tree_node(tree.lookup(a), a, 2, 0, [], [tree.lookup(b), tree.lookup(c)])


    test_diamond_tree(DoubleTree([ a, b, c, d ], lambda t: t.dependencies))
    test_diamond_tree(DoubleTree([ d, c, b, a ], lambda t: t.dependencies))
    test_diamond_tree(DoubleTree([ b, d, a, c ], lambda t: t.dependencies))

  def test_find_children_across_unused_target(self):
    a = MockTarget('a')
    b = MockTarget('b', [a])
    c = MockTarget('c', [b])
    d = MockTarget('d', [c, a])
    e = MockTarget('e', [d])

