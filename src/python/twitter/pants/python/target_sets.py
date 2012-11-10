__author__ = 'ryan'

class TargetSet(object):
  def __init__(self, sets):
    self.num_sources = 0
    self.targets = set([])
    self.sets = sets

  def add_target(self, target):
    if target in self.targets:
      raise Exception(
        "Attempting to add target %s to target set {%s}" % (target.id, ','.join([t.id for t in self.targets])))
    self.targets.add(target)
    self.num_sources += target.num_sources
    self.sets.handle_target_added(self, target)

  def remove_target(self, target):
    if target not in self.targets:
      raise Exception(
        "Attempting to remove target %s from target set {%s}" % (target.id, ','.join([t.id for t in self.targets])))
    self.targets.remove(target)
    self.num_sources -= target.num_sources
    self.sets.handle_target_removed(self, target)

  def __repr__(self):
    return "TS(%d%s%s)" % (self.num_sources, ": " if len(self.targets) > 0 else '', ','.join([t.id for t in self.targets]))


class TargetSets(object):
  def __init__(self, num_sets_to_init):
    if num_sets_to_init <= 0:
      raise Exception("TargetSets must init a positive number of sets. Passed %d" % num_sets_to_init)

    self.sets = []
    self.empty_sets = set()
    self.non_empty_sets = set()

    for i in range(num_sets_to_init):
      target_set = TargetSet(self)
      self.sets.append(target_set)
      self.empty_sets.add(target_set)

    self.min_set = self.sets[0]

    self.num_sets = num_sets_to_init

    self.num_sources = 0
    self.num_targets = 0
    self.max_num_sources = 0
    self.min_num_sources = 0

  def _recompute_min_set(self):
    for next_set in self.sets:
      if next_set.num_sources < self.min_set.num_sources:
        self.min_set = next_set

  def differential(self):
    return self.max_num_sources - self.min_num_sources


  def handle_target_added(self, target_set, target):
    self.num_sources += target.num_sources
    self.num_targets += 1
    self.max_num_sources = max([t.num_sources for t in self.sets])
    self.min_num_sources = min([t.num_sources for t in self.sets])
    if target_set in self.empty_sets:
      self.empty_sets.remove(target_set)
      self.non_empty_sets.add(target_set)

    if target_set == self.min_set:
      self._recompute_min_set()


  def handle_target_removed(self, target_set, target):
    self.num_sources -= target.num_sources
    self.num_targets -= 1
    self.max_num_sources = max([t.num_sources for t in self.sets])
    self.min_num_sources = min([t.num_sources for t in self.sets])
    if not target_set.targets:
      self.empty_sets.add(target_set)
      self.non_empty_sets.remove(target_set)

    if target_set.num_sources < self.min_set.num_sources:
      self.min_set = target_set


  def __gt__(self, other):
    if not other:
      raise Exception("TargetSets.__gt__ called with RHS of None")
    return (self.num_sources > other.num_sources or
            (self.num_sources == other.num_sources and
             self.differential() < other.differential()))


  def __lt__(self, other):
    if not other:
      raise Exception("TargetSets.__lt__ called with RHS of None")
    return (self.num_sources < other.num_sources or
            (self.num_sources == other.num_sources and
             self.differential() > other.differential()))


  def __eq__(self, other):
    return self.num_sources == other.num_sources and self.differential() == other.differential()


  def __repr__(self):
    return "Sets(%d(%d): {%s}: {%s})" % (self.num_sources, self.differential(), ','.join([str(s.num_sources) for s in self.sets]), ','.join([str(t) for t in self.sets]))


  # TODO(ryan): push this down to TargetSet (or Target?)
  def __deepcopy__(self, memo):
    newone = TargetSets(self.num_sets)
    for i in range(newone.num_sets):
      for target in self.sets[i].targets:
        newone.sets[i].add_target(target)
    return newone


