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

import parser
import symbol
import token

from twitter.common.collections.ordereddict import OrderedDict
from twitter.common.collections.orderedset import OrderedSet
from twitter.pants.base.target import TargetDefinitionException


class AST(object):
  """A wrapper around a tuple representing an ast node (as returned by parser.st2tuple()).

  Provides useful tree navigation ability, and is much more convenient to work with than
  working directly with the tuples (or python's internal ast nodes).
  """
  def __init__(self, tpl, parent):
    self.production = tpl[0]  # The production type (a value from symbol or token).
    self.tpl = tpl  # The underlying tuple.
    self.parent = parent
    self.children = []
    self.left_sibling = None
    self.right_sibling = None

    # The (1-based) first and last lines of the text represented by this AST.
    # Note that the AST may not represent the entire line.
    self.first_line = -1
    self.last_line = -1

  def find_first(self, production):
    """Finds the first descendant of the specified production type."""
    if self.production == production:
      return self
    else:
      for i in xrange(len(self.children)):
        res = self.children[i].find_first(production)
        if res:
          return res
    return None

  def find_left(self, production):
    """Finds the first descendant of the specified production type, looking only down the left-most path."""
    if self.production == production:
      return self
    elif len(self.children) > 0:
      return self.children[0].find_left(production)
    else:
      return None

  SURROUND_WITH_SPACES = set(['-', '+'])
  APPEND_SPACE = set([','])

  def reconstitute(self):
    """Reconstitutes the AST to a canonical string form."""
    def transform(str):
      if str in AST.SURROUND_WITH_SPACES:
        return ' %s ' % str
      elif str in AST.APPEND_SPACE:
        return '%s ' % str
      else:
        return str
    if len(self.children) == 0:
      return transform(self.tpl[1])
    else:
      return ''.join([x.reconstitute() for x in self.children])

  def pretty_print(self, newlines=True, indent='  '):
    """Returns a pretty-printed representation of this AST.

    Useful when debugging and examining the AST structure."""
    def do_pretty_print(ast, depth=0):
      production_name = \
        symbol.sym_name.get(ast.production, token.tok_name.get(ast.production, str(ast.production)))
      indent_str = ('\n' if newlines else '') + depth * indent
      if len(ast.children) > 0:
        val = ', '.join([do_pretty_print(x, depth=(depth + 1)) for x in ast.children])
      else:
        val = '"%s"' % ast.tpl[1]
      return '%s[%d:%d] (%s, %s%s)' % (indent_str, ast.first_line, ast.last_line, production_name, val, indent_str)
    return do_pretty_print(self)

  def __repr__(self):
    return self.pretty_print(newlines=False, indent='')

class TargetDefinition(object):
  """The source definition (actual BUILD file text) of a target.

  Useful for things like linting and rewriting BUILD files.
  """

  @staticmethod
  def _to_ast(tpl, parent=None):
    """Convert an ast tuple (as returned by parser.st2tuple()) into a tree of AST instances."""
    ret = AST(tpl, parent)
    if isinstance(tpl[1], tuple):  # A non-terminal node. All elements apart from the first are tuples.
      ret.children = [TargetDefinition._to_ast(x, ret) for x in tpl[1:]]
      for i in xrange(0, len(ret.children)):
        if i > 0:
          ret.children[i - 1].right_sibling = ret.children[i]
        if i + 1 < len(ret.children):
          ret.children[i + 1].left_sibling = ret.children[i]
      ret.first_line = ret.children[0].first_line
      ret.last_line = ret.children[-1].last_line
    elif len(tpl) == 3:  # We have line numbers.
      ret.first_line = ret.last_line = tpl[2]
    return ret

  @staticmethod
  def _split_target_definition(ast):
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
    open_paren = ast.find_first(token.LPAR)

    target_type_decl = open_paren.parent.left_sibling.reconstitute()

    # open_paren.right_sibling is the argument list. Its children are of production type
    # symbol.argument interspersed with token.COMMA. We filter out the commas here.
    arg_asts = filter(lambda x: x.production == symbol.argument, open_paren.right_sibling.children)

    # Each arg AST's children tuple is (token.NAME, token.EQUALS, value AST).
    name_value_ast_pairs = [(x.children[0].reconstitute(), x.children[2]) for x in arg_asts]

    # If value is a list, reconstitute it as a list, otherwise as a string.
    def reconstitute_value(value_ast):
      # Check if arg value is a list.
      left_square_bracket = value_ast.find_left(token.LSQB)
      if left_square_bracket:
        list_parent = left_square_bracket.right_sibling
        value = [x.reconstitute() for x in filter(lambda x: x.production != token.COMMA, list_parent.children)]
      else:
        value = value_ast.reconstitute()
      return value

    # A map of name -> value where value is either a string or a list of strings.
    # Map is in defintion order of args.
    args = OrderedDict([(name, reconstitute_value(value_ast)) for (name, value_ast) in name_value_ast_pairs ])
    return target_type_decl, args

  def __init__(self, tgt):
    with open(tgt.address.buildfile.full_path, 'r') as infile:
      self.buildfile_content = infile.read()
    self.buildfile_lines = self.buildfile_content.split('\n')

    # TODO: If running this on multiple targets in a single BUILD file, we'll parse
    # the same build file multiple times here. In the unlikely event that this becomes a
    # performance issue, we can refactor this to parse each file once only.
    # We could even hook in to the original parse of the BUILD file when it's eval'd, but
    # that's almost certainly overkill, and would complicate the design unnecessarily.
    st = parser.suite(self.buildfile_content)
    buildfile_ast = TargetDefinition._to_ast(parser.st2tuple(st, line_info=True))

    # There can be all sorts of top-level definitions in the BUILD file.
    # Here we find the one corresponding to the target we're interested in, by
    # looking at the one that spans that target's line number.
    self.target_ast = None
    for child in buildfile_ast.children:
      if child.first_line <= tgt.source_lineno and tgt.source_lineno <= child.last_line:
        self.target_ast = child
        break
    if self.target_ast is None:  # Should never happen.
      raise TargetDefinitionException(tgt, 'Could not find target definition in its AST')

    (self.target_type_decl, self.args) = TargetDefinition._split_target_definition(self.target_ast)

  # When reformatting a target definition, enforce that these args come first, in this order.
  DEFAULT_ARG_ORDER = ('name', 'provides', 'dependencies', 'sources')

  # When reformatting a target definition, format these args on multiple lines, if the value is a list.
  DEFAULT_MULTILINE_ARGS = frozenset(['dependencies'])

  # When reformatting a target definition, sort the value of these args alphabetically, if it's a list.
  DEFAULT_SORT_ARGS = frozenset(['dependencies', 'sources'])

  def format(self,
             arg_order=DEFAULT_ARG_ORDER,
             multiline_args=DEFAULT_MULTILINE_ARGS,
             sort_args=DEFAULT_SORT_ARGS):
    """Returns a string with a nicely-formatted representation of this target definition.

    Args are formatted in the order specified in arg_order, if any, followed by any remaining arguments,
    in the original definition order. Args in multiline_args whose values are list are formatted
    one list element per line. Other args whose values are list are formatted all on one line.
    """
    arg_names = OrderedSet(arg_order)  # Note that some of these might not be present in the target.
    for arg_name in self.args.keys():
      arg_names.add(arg_name)
    arg_strs = []
    for arg_name in arg_names:
      val = self.args.get(arg_name, None)
      if val:
        if isinstance(val, list):
          if arg_name in sort_args:
            val.sort()
          if arg_name in multiline_args:
            val_str = '[\n    %s,\n  ]' % ',\n    '.join(val)
          else:
            val_str = '[%s]' % ', '.join(val)
        else:
          val_str = str(val)
        arg_strs.append('%s = %s' % (arg_name, val_str))
    return '%s(%s\n)\n' % (self.target_type_decl, ',\n  '.join(arg_strs))

  def reformat_buildfile(self):
    # Note that line numbers are 1-based.
    new_buildfile_content = \
      '\n'.join(self.buildfile_lines[0:self.target_ast.first_line-1]) + \
      self.format() + \
      '\n'.join(self.buildfile_lines[self.target_ast.last_line:])
    return new_buildfile_content


