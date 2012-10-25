__author__ = 'ryan'

from twitter.pants.targets.internal import InternalTarget

class DependenciesWrapper(InternalTarget):
  "Simple target that allows us to bundle together a group of downstream dependencies"

  def resolve(self):
    for dependency in self.dependencies:
      for resolved_dependency in dependency.resolve():
        yield resolved_dependency

