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

import parser
import symbol
import token

__author__ = 'Benjy Weinberger'


class TargetDefinitionException(Exception):
  """Thrown on errors in target definitions."""
  def __init__(self, target, msg):
    Exception.__init__(self, 'Error in target %s: %s' % (target.address, msg))


class AST(object):
  def __init__(self, tpl, parent):
    self.production = tpl[0]
    self.tpl = tpl
    self.parent = parent
    self.children = []
    self.left_sibling = None
    self.right_sibling = None

  def reconstitute(self):
    if len(self.children) == 0:
      return self.tpl[1]
    else:
      return ''.join([x.reconstitute() for x in self.children])

  def pretty_print(self, newlines=True, indent='  '):
    def do_pretty_print(ast, depth=0):
      production_name = \
        symbol.sym_name.get(ast.production, token.tok_name.get(ast.production, str(ast.production)))
      indent_str = ('\n' if newlines else '') + depth * indent
      if len(ast.children) > 0:
        val = ', '.join([do_pretty_print(x, depth=(depth + 1)) for x in ast.children])
      else:
        val = '"%s"' % ast.tpl[1]
      return '%s(%s, %s%s)' % (indent_str, production_name, val, indent_str)
    return do_pretty_print(self)

  def __repr__(self):
    return self.pretty_print(newlines=False, indent='')

class TargetDefinition(object):
  """The source definition (actual BUILD file text) of a target.

  Useful for things like linting and rewriting BUILD files."""

  @staticmethod
  def to_ast(tpl, parent=None):
    ret = AST(tpl, parent)
    if isinstance(tpl[1], tuple):  # A non-terminal node. All elements apart from the first are tuples.
      ret.children = [TargetDefinition.to_ast(x, ret) for x in tpl[1:]]
      for i in xrange(0, len(ret.children)):
        if i > 0:
          ret.children[i - 1].right_sibling = ret.children[i]
        if i + 1 < len(ret.children):
          ret.children[i + 1].left_sibling = ret.children[i]
    return ret

  @staticmethod
  def find_first(ast, name):
    if ast.production == name:
      return ast
    else:
      for i in xrange(len(ast.children)):
        res = TargetDefinition.find_first(ast.children[i], name)
        if res:
          return res
    return None

#  @staticmethod
#  def find_all(ast, name, at_depth=-1):
#    if ast.production == name and at_depth <= 0:
#      return [ ast ]
#    elif at_depth:
#      return [item for list in
#              (TargetDefinition.find_all(child, name, at_depth - 1) for child in ast.children)
#                for item in list]
#    return []

  def __init__(self, source_lines, source_lineno):
    self.source_lines = source_lines
    self.source_lineno = source_lineno
    source = ''.join(self.source_lines)
    self.ast = TargetDefinition.to_ast(parser.st2tuple(parser.expr(source)))
    self._split(self.ast)

    print '66666666666666666666666 %s' % self.ast.pretty_print()
    arg_strs = [ '%s===%s' % (arg.children[0].reconstitute(), arg.children[2].reconstitute()) for arg in self.args ]
    print '77777777777777777777777 %s(\n  %s\n)' % (self.target_type_decl, ',\n  '.join(arg_strs))

  def _split(self, ast):
    """A heuristic to split the target type and the args out of the textual definition.

    Assumes that the definition is more or less of the form

    target_type_decl(arg1=value1, arg2=value2)

    E.g.,

    java_library(name='foo',
                 dependencies=[
                   pants('src/java/bar'),
                   pants('src/java/baz')
                ],
                sources=globs('*.java))

    Because we're using the python AST, and not naive regex matching, we can handle a wide variety
    of cases. See the unit test for examples.
    """
    open_paren = TargetDefinition.find_first(ast, token.LPAR)
    self.target_type_decl = open_paren.parent.left_sibling.reconstitute()
    self.args = filter(lambda x: x.production == symbol.argument, open_paren.right_sibling.children)
