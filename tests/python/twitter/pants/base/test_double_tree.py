__author__ = 'ryan'

import unittest

from twitter.pants.base import DoubleTree
from twitter.pants.test import MockTarget


class DoubleTreeTest(unittest.TestCase):

  def check_tree_node(self, tree, data, children, parents, descendants = None, ancestors = None, independents = None):
    node = tree.lookup(data)

    self.assertEquals(node.data, data)
    self.assertEquals(node.children, set(map(tree.lookup, children)))
    self.assertEquals(node.parents, set(map(tree.lookup, parents)))
    if descendants:
      self.assertEquals(node.descendants, set(map(tree.lookup, descendants)))
    if ancestors:
      self.assertEquals(node.ancestors, set(map(tree.lookup, ancestors)))
    if independents:
      self.assertEquals(node.independents, set(map(tree.lookup, independents)))

  def test_simple_tree(self):
    a = MockTarget('a')
    b = MockTarget('b', [a])
    c = MockTarget('c', [b])
    d = MockTarget('d', [c, a])
    e = MockTarget('e', [d])

    def test_tree(tree):
      self.assertEquals(tree._roots, set([tree.lookup(e)]))
      self.assertEquals(tree.leaves, set([tree.lookup(a)]))

      self.check_tree_node(tree, e, [d], [], [a, b, c, d], [], [])
      self.check_tree_node(tree, d, [a, c], [e], [a, b, c], [e], [])
      self.check_tree_node(tree, c, [b], [d], [a,b], [d,e], [])
      self.check_tree_node(tree, b, [a], [c], [a], [c,d,e], [])
      self.check_tree_node(tree, a, [], [b, d], [], [b,c,d,e], [])

    test_tree(DoubleTree([e, d, c, b, a], lambda t: t.dependencies))
    test_tree(DoubleTree([a, b, c, d, e], lambda t: t.dependencies))
    test_tree(DoubleTree([a, b, e, d, c], lambda t: t.dependencies))
    test_tree(DoubleTree([d, a, c, e, b], lambda t: t.dependencies))


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

      def t(n):
        return tree.lookup(n)

      self.assertEquals(tree._roots, set([t(root)]))
      self.assertEquals(tree.leaves, set(map(t, [rrr, rrl, rlr, rll, lrr, lrl, llr, lll])))

      self.check_tree_node(tree, root, [r, l], [], [r, l, rr, rl, lr, ll, rrr, rrl, rlr, rll, lrr, lrl, llr, lll], [], [])

      self.check_tree_node(tree, r, [rl, rr], [root], [rr, rl, rrr, rrl, rlr, rll], [root], [l, lr, ll, lrr, lrl, llr, lll])
      self.check_tree_node(tree, l, [ll, lr], [root], [lr, ll, lrr, lrl, llr, lll], [root], [r, rr, rl, rrr, rrl, rlr, rll])

      self.check_tree_node(tree, rr, [rrl, rrr], [r], [rrr, rrl], [root, r], [l, rl, lr, ll, rlr, rll, lrr, lrl, llr, lll])
      self.check_tree_node(tree, rl, [rll, rlr], [r], [rlr, rll], [root, r], [l, rr, lr, ll, rrr, rrl, lrr, lrl, llr, lll])
      self.check_tree_node(tree, lr, [lrl, lrr], [l], [lrr, lrl], [root, l], [r, rr, rl, ll, rrr, rrl, rlr, rll, llr, lll])
      self.check_tree_node(tree, ll, [lll, llr], [l], [llr, lll], [root, l], [r, rr, rl, lr, rrr, rrl, rlr, rll, lrr, lrl])

      self.check_tree_node(tree, rrr, [], [rr], [], [rr, r, root], [l, lr, ll, rl, rrl, rlr, rll, lrr, lrl, llr, lll])
      self.check_tree_node(tree, rrl, [], [rr], [], [rr, r, root], [l, lr, ll, rl, rrr, rlr, rll, lrr, lrl, llr, lll])
      self.check_tree_node(tree, rlr, [], [rl], [], [rl, r, root], [l, lr, ll, rr, rrr, rrl, rll, lrr, lrl, llr, lll])
      self.check_tree_node(tree, rll, [], [rl], [], [rl, r, root], [l, lr, ll, rr, rrr, rrl, rlr, lrr, lrl, llr, lll])
      self.check_tree_node(tree, lrr, [], [lr], [], [lr, l, root], [r, rr, rl, ll, rrr, rrl, rlr, rll, lrl, llr, lll])
      self.check_tree_node(tree, lrl, [], [lr], [], [lr, l, root], [r, rr, rl, ll, rrr, rrl, rlr, rll, lrr, llr, lll])
      self.check_tree_node(tree, llr, [], [ll], [], [ll, l, root], [r, rr, rl, lr, rrr, rrl, rlr, rll, lrr, lrl, lll])
      self.check_tree_node(tree, lll, [], [ll], [], [ll, l, root], [r, rr, rl, lr, rrr, rrl, rlr, rll, lrr, lrl, llr])

    # Test in order
    test_tree(DoubleTree([root, r, l, rr, rl, lr, ll, rrr, rrl, rlr, rll, lrr, lrl, llr, lll], lambda t: t.dependencies))

    # Test a couple of randomly chosen orders
    test_tree(DoubleTree([lrl, r, root, rl, rrr, rll, lr, lrr, ll, lll, l, rr, rrl, rlr, llr], lambda t: t.dependencies))
    test_tree(DoubleTree([ll, rrl, lrl, rl, rlr, lr, root, rrr, rll, r, llr, rr, lrr, l, lll], lambda t: t.dependencies))
    test_tree(DoubleTree([rr, rlr, rl, rrr, rrl, l, root, lr, lrr, llr, r, rll, lrl, ll, lll], lambda t: t.dependencies))
    test_tree(DoubleTree([l, lll, rrr, rll, ll, lrl, llr, rl, root, r, lr, rlr, rr, lrr, rrl], lambda t: t.dependencies))

  def test_diamond_in_different_orders(self):
    a = MockTarget('a')
    b = MockTarget('b', [a])
    c = MockTarget('c', [a])
    d = MockTarget('d', [c, b])

    def test_diamond_tree(tree):
      self.assertEquals(tree._roots, set([tree.lookup(d)]))
      self.assertEquals(tree.leaves, set([tree.lookup(a)]))
      self.check_tree_node(tree, d, [b, c], [])
      self.check_tree_node(tree, c, [a], [d])
      self.check_tree_node(tree, b, [a], [d])
      self.check_tree_node(tree, a, [], [b, c])


    test_diamond_tree(DoubleTree([a, b, c, d], lambda t: t.dependencies))
    test_diamond_tree(DoubleTree([d, c, b, a], lambda t: t.dependencies))
    test_diamond_tree(DoubleTree([b, d, a, c], lambda t: t.dependencies))

  def test_find_children_across_unused_target(self):
    a = MockTarget('a')
    b = MockTarget('b', [a])
    c = MockTarget('c', [b])
    d = MockTarget('d', [c, a])
    e = MockTarget('e', [d])

