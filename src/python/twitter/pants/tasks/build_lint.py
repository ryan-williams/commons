# ==================================================================================================
# Copyright 2012 Twitter, Inc.
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

__author__ = 'Benjy Weinberger'

import difflib

from twitter.pants.base.build_definition import BuildDefinition
from twitter.pants.tasks import Task


class BuildLint(Task):
  def __init__(self, context):
    Task.__init__(self, context)

  def execute(self, targets):
    for target in targets:
      self._fix_lint(target)

  def _fix_lint(self, target):
    buildfile_path = target.address.buildfile.full_path
    target_def = BuildDefinition(buildfile_path)
    old_buildfile_lines = target_def.buildfile_lines
    new_buildfile_lines = target_def.reformat_buildfile().split('\n')
    if new_buildfile_lines != old_buildfile_lines:
      with open(buildfile_path, 'w') as outfile:
        outfile.write('\n'.join(new_buildfile_lines))
    #  diff = '\n'.join(difflib.unified_diff(old_buildfile_lines, new_buildfile_lines, buildfile_path))
    #else:
    #  diff = "no diff for " + buildfile_path
    #print diff
