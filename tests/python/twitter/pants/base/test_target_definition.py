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
from twitter.pants.base import BuildFile, ParseContext
from twitter.pants.base.address import Address
from twitter.pants.base.target import Target
from twitter.pants.base.target_definition import TargetDefinition


class TargetDefinitionTest(unittest.TestCase):

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
    with open(fullpath, 'a') as f:
      f.write(content)

  def _parse_build_content(self, content):
    relpath = 'test/BUILD'
    self._write_build_content(relpath, content)
    buildfile = BuildFile(self.root, relpath)
    ParseContext(buildfile).parse()
    return buildfile

  def _do_test_source(self, buildfile, tgt_name, expected):
    addr = Address(buildfile, tgt_name, False)
    tgt = Target.get(addr)
    target_def = TargetDefinition(tgt)
    formatted = target_def.format()
    self.assertEquals(expected.strip(), formatted)

  def test_source(self):
    src1 = \
"""
scala_library(
  name = 'foo', sources=['Foo2.scala', 'Foo1.scala'],
  dependencies =[pants('test/dep2'),
                pants('test/dep1')],
                )
"""
    expected1 = \
"""
scala_library(name = 'foo',
  dependencies = [
    pants('test/dep1'),
    pants('test/dep2'),
  ],
  sources = ['Foo1.scala', 'Foo2.scala'],
)
"""
    src2 = \
"""
scala_library(name ='bar',
  dependencies= [ pants('test/dep3')   ],
  sources=rglobs('*.scala') -[ 'Something2.scala', 'Something1.scala' ])
"""
    # Note that we won't sort the list in the definition of sources, because it's not the entire definition.
    expected2 = \
"""
scala_library(name = 'bar',
  dependencies = [
    pants('test/dep3'),
  ],
  sources = rglobs('*.scala') - ['Something2.scala', 'Something1.scala'],
)
"""
    buildfile_content = src1 + '\n' + src2
    buildfile = self._parse_build_content(buildfile_content)

    self._do_test_source(buildfile, 'foo', expected1)
    self._do_test_source(buildfile, 'bar', expected2)
