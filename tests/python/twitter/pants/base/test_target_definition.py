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
    self._write_build_content('test/foo/BUILD', "scala_library(name='foo', sources=[], dependencies=[])")
    self._write_build_content('test/bar/BUILD', "scala_library(name='bar', sources=[], dependencies=[])")

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

  def _do_test_source(self, addr, expected):
    tgt = Target.get(addr)
    definition = TargetDefinition(tgt.source_lines, tgt.source_lineno)
    print 'XXXXXXXXXXXXXXXXXXXXX '

  def test_source(self):
    src1 = "scala_library(name='baz', sources=['Baz1.scala', 'Baz2.scala'], " + \
           "dependencies=[pants('test/foo'), pants('test/bar')])\n"
    src2 = "scala_library(name='qux', dependencies=[], sources=(globs('Qux*.scala') + ['Something.scala']))\n"
    buildfile = self._parse_build_content(src1 + '\n' + src2)

    addr1 = Address(buildfile, 'baz', False)
    addr2 = Address(buildfile, 'qux', False)

    self._do_test_source(addr1, '')
