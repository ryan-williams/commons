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

import os
import shutil
import tempfile
import unittest

from twitter.common.dirutil import safe_mkdir
from twitter.pants.base.build_definition import BuildDefinition


class BuildDefinitionTest(unittest.TestCase):

  def setUp(self):
    self.root = tempfile.mkdtemp()
    self._write_build_content('test/dep1/BUILD', "scala_library(name='dep1', sources=[], dependencies=[])")
    self._write_build_content('test/dep2/BUILD', "scala_library(name='dep2', sources=[], dependencies=[])")
    self._write_build_content('test/dep3/BUILD', "scala_library(name='dep3', sources=[], dependencies=[])")
    self._write_build_content('test/dep4/BUILD', "scala_library(name='dep4', sources=[], dependencies=[])")

  def tearDown(self):
    shutil.rmtree(self.root, ignore_errors=True)

  def _write_build_content(self, relpath, content):
    fullpath = os.path.join(self.root, relpath)
    safe_mkdir(os.path.dirname(fullpath))
    with open(fullpath, 'w') as f:
      f.write(content)
    return fullpath

  def _do_test_reformatting(self, buildfile_path, expected):
    build_def = BuildDefinition(buildfile_path)
    formatted = build_def.reformat_buildfile()
    self.assertEquals(expected.lstrip(), formatted)

  def test_reformatting(self):
    src = \
"""
# A multiline
# comment.

SINGLE_SOURCE_SET = set([ 'Thing1.scala' ])

scala_library(
  name = 'foo', sources=['Foo2.scala', 'Foo1.scala'] + SINGLE_SOURCE_SET,
  dependencies =[pants('test/dep2'),
                pants('test/dep1')],
                )

MULTIPLE_SOURCE_SET = set([
  'Thing2.scala',
  'Thing3.scala'
])

# A comment in

# the middle.

scala_library(name ='bar',  # Comment
  dependencies= [ pants('test/dep3')   ],
  # Note that we won't sort the list below, because it's not the entire definition.
  sources=rglobs('*.scala') -[ 'Something2.scala', 'Something1.scala' ]+  MULTIPLE_SOURCE_SET)

# A comment at the end.
"""

    expected = \
"""
# A multiline
# comment.
scala_library(name = 'foo',
  dependencies = [
    pants('test/dep1'),
    pants('test/dep2'),
  ],
  sources = ['Foo1.scala', 'Foo2.scala'],
)

MULTIPLE_SOURCE_SET = set([
  'Thing2.scala',
  'Thing3.scala'
])

# A comment in

# the middle.

scala_library(name = 'bar',  # Comment
  dependencies = [
    pants('test/dep3'),
  ],
  # Note that we won't sort the list below, because it's not the entire definition.
  sources = rglobs('*.scala') - ['Something2.scala', 'Something1.scala'] + MULTIPLE_SOURCE_SET,
)

# A comment at the end.
"""

    buildfile_path = self._write_build_content('test/foo/BUILD', src)
    self._do_test_reformatting(buildfile_path, expected)
