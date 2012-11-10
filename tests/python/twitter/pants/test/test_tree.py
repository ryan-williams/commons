__author__ = 'ryan'

from twitter.pants.base import DoubleTree
from twitter.pants.test import MockTarget

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

  def __getitem__(self, id):
    return self._get_target_by_id(id)


