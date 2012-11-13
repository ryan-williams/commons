# ==================================================================================================
# Copyright 2011 Twitter, Inc.
# --------------------------------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==================================================================================================

__author__ = 'Mark C. Chu-Carroll'

import os

from collections import defaultdict

from twitter.common.java.class_file import ClassFile
from twitter.pants.base.target import Target

class JvmDependencyCache(object):
  """
  Class which computes and stores information about the dependencies of targets.
  """

  def __init__(self, compile_task, targets):
    self.task = compile_task
    self.targets = targets
    # Combined mappings for all targets from target to the set of classes it depends on.
    self.deps_by_target = defaultdict(set)
    # Combined mappings for all targets from class to target that provides it.
    self.targets_by_class = defaultdict(set)
    # per source file mappings from source file to a list of classes they depend on.
    self.deps_by_source = defaultdict(set)
    self.computed_deps = None


  def get_compilation_dependencies(self):
    """
    Computes a map from the source files in a target to class files that the source file
    depends on.

    Parameters:
      targets: a list of the targets from the current compile run whose
         dependencies should be analyzed.
    Returns: a target-to-target mapping from targets to targets that they depend on.
       If this was already computed, return the already computed result.
    """
    if self.computed_deps is not None:
      return self.computed_deps

    # Get the class products from the compiler. This provides us with all the info we
    # need about what source file/target produces what class.
    class_products = self.task.context.products.get('classes')
    for target in self.targets:
      # for each target, compute a mapping from classes that the target generates to the target
      # this mapping is self.targets_by_class
      if target not in class_products.by_target:
        # If the target isn't in the products map, that means that it had no products - which
        # only happens if the target has no source files. This occurs when a target is created
        # as a placeholder.
        continue

      for outdir in class_products.by_target[target]:
        for cl in class_products.by_target[target][outdir]:
          self.targets_by_class[cl].add(target)

      # For each source in the current target, compute a mapping from source files to the classes that they
      # really depend on. (Done by parsing class files.)

      for source in target.sources:
        # we can get the set of classes from a source file by going into the same class_products object
        source_file_deps = set()
        class_files = set()
        for dir in class_products.by_target[source]:
          class_files |= set([ ( clfile, dir) for clfile in class_products.by_target[source][dir] ])

        # for each class file, get the set of referenced classes - these
        # are the classes that it depends on.
        for (cname, cdir) in class_files:
          cf = ClassFile.from_file(os.path.join(cdir, cname), False)
          dep_set = cf.get_external_class_references()
          dep_classfiles = [ "%s.class" % s for s in dep_set ]
          source_file_deps = source_file_deps.union(dep_classfiles)

        self.deps_by_source[source] = source_file_deps
        # add data from these classes to the target data in the map.
        self.deps_by_target[target].update(source_file_deps)

    # Now, we have a map from target to the classes they depend on,
    # and a map from classes to the targets that provide them.
    # combining the two, we can get a map from target to targets that it really depends on.

    self.computed_deps = defaultdict(set)
    for target in self.deps_by_target:
      target_dep_classes = self.deps_by_target[target]
      for cl in target_dep_classes:
        if cl not in self.targets_by_class:
          # We should probably provide a parameter for this filter here, to
          # allow users to specify packages which shouldn't be flagged
          # any class which isn't in any
          # target, but which is in something clearly library-based, like "scala."
          # shouldn't even generate a warning.
          FILTER_PREFIXES = [ "scala", "java" ]
          if self.task.check_all_deps and not reduce(lambda x, y: x or y,
                [ cl.startswith(pre) for pre in FILTER_PREFIXES]):
            print "Warning: Target %s depends on class %s which is not a compiler output" % (target, cl)
          continue
        target_dep_targets = self.targets_by_class[cl]
        if target in self.computed_deps:
          self.computed_deps[target] = self.computed_deps[target].union(target_dep_targets)
        else:
          self.computed_deps[target] = set(target_dep_targets)
    return self.computed_deps

  def get_dependency_blame(self, from_target, to_target):
    """
    Figures out why target "from" depends on target "to".
     Target "A" depends on "B" because "A"s class "X" depends on "Y" which is in "B"s source file "Z".
     Returns: a pair of (source1, class) where:
       source1 is the name of a source file in "from" that depends on something
          in "to".
       class is the name of the class that source1 depends on.
    """
    # iterate over the sources in the from target.
    for source in from_target.sources:
      # for each class that the source depends on:
      for cl in self.deps_by_source[source]:
        # if that's in the target, then call it the culprit.
        if cl in self.targets_by_class and to_target in self.targets_by_class[cl]:
          return (source, cl)
    return ("none", "none")
