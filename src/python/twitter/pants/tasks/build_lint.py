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
import re

from twitter.pants.tasks import Task


class BuildLint(Task):
  @classmethod
  def setup_parser(cls, option_group, args, mkflag):
    Task.setup_parser(option_group, args, mkflag)

    option_group.add_option(mkflag("transitive"), mkflag("transitive", negate=True),
      dest="buildlint_transitive", default=False,
      action="callback", callback=mkflag.set_bool,
      help="[%default] apply lint rules transitively to all dependency buildfiles.")

    option_group.add_option(mkflag("action"), dest="buildlint_actions", default=['diff'],
      action="append", type="choice", choices=['diff', 'rewrite'],
      help="diff=print out diffs, rewrite=apply changes to BUILD files directly.")

  def __init__(self, context):
    Task.__init__(self, context)
    self.transitive = context.options.buildlint_transitive
    self.actions = set(context.options.buildlint_actions)

  def execute(self, targets):
    if self.transitive:
      for target in targets:
        self._fix_lint(target)
    else:
      for target in self.context.target_roots:
        self._fix_lint(target)

  DEPS_RE = re.compile(r'dependencies\s*=\s*\[((?:[^,]+),)([^,]+),?\s*\]', flags=re.DOTALL)

  def _fix_lint(self, target):
    def sort_deps(m):
      deps = m.group(1).split(',') + [m.group(2)]
      deps = filter(lambda x: x, [x.strip() for x in deps])
      deps = sorted(deps)
      res = 'dependencies = [\n    %s,\n  ]' % (',\n    '.join(deps))
      return res

    buildfile_path = target.address.buildfile.full_path
    with open(buildfile_path, 'r') as infile:
      old_buildfile_source = infile.read()
    new_buildfile_source = BuildLint.DEPS_RE.sub(sort_deps, old_buildfile_source)
    if new_buildfile_source != old_buildfile_source:
      if 'rewrite' in self.actions:
        with open(buildfile_path, 'w') as outfile:
          outfile.write(new_buildfile_source)
      if 'diff' in self.actions:
        diff = '\n'.join(difflib.unified_diff(old_buildfile_source.split('\n'),
          new_buildfile_source.split('\n'), buildfile_path))
        print diff
