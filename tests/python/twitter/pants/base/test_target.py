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

from twitter.common.contextutil import temporary_dir
from twitter.pants.base import BuildFile, ParseContext
from twitter.pants.base.address import Address
from twitter.pants.base.target import Target


def parse_build_content(content):
  with temporary_dir() as root:
    relpath = 'test/BUILD'
    fullpath = os.path.join(root, relpath)
    os.makedirs(os.path.dirname(fullpath))
    with open(fullpath, 'a') as f:
      f.write(content)
    buildfile = BuildFile(root, relpath)
    ParseContext(buildfile).parse()
    return buildfile


def test_source():
  src1 = "scala_library(name='foo', sources=['Foo1.scala', 'Foo2.scala'], dependencies=[])\n"
  src2 = "scala_library(name='bar', dependencies=[], sources=globs('Bar*.scala'))\n"
  buildfile = parse_build_content(src1 + '\n' + src2)

  addr1 = Address(buildfile, 'foo', False)
  target1 = Target.get(addr1)

  addr2 = Address(buildfile, 'bar', False)
  target2 = Target.get(addr2)

  assert src1 == target1.source()
  assert src2 == target2.source()
