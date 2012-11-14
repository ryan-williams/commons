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

from twitter.pants.base.target import TargetDefinitionException


class AST(object):
  """A wrapper around a tuple representing an ast node (as returned by parser.st2tuple()).

  Provides useful tree navigation ability, and is much more convenient to work with than
  working directly with the tuples (or python's internal ast nodes).
  """
  class Formatter:
    """Settings for formatting an AST back to a string."""
    TOP_LEVEL = '_TOP_LEVEL'

    DEFAULT_SURROUND_WITH_SPACES = set(['-', '+', '='])
    DEFAULT_APPEND_SPACE = set([','])
    DEFAULT_MULTILINE = frozenset(['dependencies', 'artifact'])
    DEFAULT_MULTILINE_COMPACT = frozenset([TOP_LEVEL])
    DEFAULT_ARG_ORDER = ('name', 'provides', 'dependencies', 'sources')
    DEFAULT_SORT_VALUES_FOR = frozenset(['dependencies', 'sources'])

    def __init__(self,
                 surround_with_spaces=DEFAULT_SURROUND_WITH_SPACES,
                 append_space=DEFAULT_APPEND_SPACE,
                 multiline=DEFAULT_MULTILINE,
                 multiline_compact=DEFAULT_MULTILINE_COMPACT,
                 arg_order=DEFAULT_ARG_ORDER,
                 sort_values_for=DEFAULT_SORT_VALUES_FOR):
      self.surround_with_spaces = surround_with_spaces  # Surround these tokens with spaces.
      self.append_space = append_space  # Append a space after these tokens.
      self.multiline = multiline  # Format these lists one item per line.
      self.multiline_compact = multiline_compact  # Same as multiline, but with no whitespace before the first item.
      self.arg_order = arg_order  # Order arglists with these first, in this order.
      self.sort_values_for = sort_values_for  # Sort the value lists of these args alphabetically.
      self.kwarg_order_key = dict()
      for i, arg_name in enumerate(self.arg_order):
        self.kwarg_order_key[arg_name] = 'AAAA%03d' % i

    # This will sort args by the order in self.arg_order first, and then any remaining args
    # in the original order (python's sort is stable).
    # Note that this is a no-op if the list is not an arglist.
    def arglist_key_func(self, str):
      arg_name = str.split('=', 2)[0].strip()
      return self.kwarg_order_key.get(arg_name, 'Z')

    def format_token(self, token):
      if token in self.surround_with_spaces:
        return ' %s ' % token
      elif token in self.append_space:
        return '%s ' % token
      else:
        return token

    def format_list(self, context, nesting_depth, values):
      """Format a list of comma-separated strings."""
      values = filter(lambda x: x.strip() != ',', values)
      if context in self.sort_values_for:
        values = sorted(values)
      else:
        values = sorted(values, key=self.arglist_key_func)
      if context in self.multiline or context in self.multiline_compact:
        indent = (nesting_depth + 1) * '  '
        str = '%s,\n' % (',\n' + indent).join(values)
        if context in self.multiline:
          str = '\n%s%s%s' % (indent, str, nesting_depth * '  ')
      else:
        str = '%s' % ', '.join(values)
      return str

  DEFAULT_FORMATTER=Formatter()

  @staticmethod
  def to_ast(tpl, parent=None, elide=True):
    """Convert an ast tuple (as returned by parser.st2tuple()) into a tree of AST instances.

    If elide is true we elide away all unnecessary singleton nodes. This makes for a
    more useful and readable tree.
    """
    ret = AST(tpl, parent)
    if isinstance(tpl[1], tuple):  # A non-terminal node. All elements apart from the first are tuples.
      ret.children = [AST.to_ast(x, ret) for x in tpl[1:]]
      if elide:
        ret.children = [
        x.children[0]\
        if len(x.children) == 1 and x.production not in (symbol.listmaker, symbol.arglist)
        else x for x in ret.children
        ]
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

  def reconstitute(self, nesting_depth=0, formatter=DEFAULT_FORMATTER):
    """Reconstitutes the AST to a canonical form."""
    if len(self.children) == 0:
      return formatter.format_token(self.tpl[1])
    elif self.production == symbol.arglist or self.production == symbol.listmaker:
      context = None
      reconstituted_list_items = [x.reconstitute(nesting_depth + 1, formatter) for x in self.children]
      if self.production == symbol.arglist:
        context = AST.Formatter.TOP_LEVEL if nesting_depth == 0 else \
          self.parent.left_sibling.reconstitute(nesting_depth + 1, formatter).strip()
      elif self.production == symbol.listmaker:
        ancestor = self.left_sibling  # The left-square-bracket token.
        while ancestor and not ancestor.left_sibling:
          ancestor = ancestor.parent
        if ancestor and ancestor.left_sibling.production == token.EQUAL:
          context = ancestor.left_sibling.left_sibling.reconstitute(nesting_depth + 1, formatter).strip()
      return formatter.format_list(context, nesting_depth, reconstituted_list_items)
    else:
      return ''.join([x.reconstitute(nesting_depth, formatter) for x in self.children])

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
    buildfile_ast = AST.to_ast(parser.st2tuple(st, line_info=True))

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

  def format(self, formatter=AST.DEFAULT_FORMATTER):
    """Returns a string with a nicely-formatted representation of this target definition."""
    return self.target_ast.reconstitute(formatter=formatter)

  def reformat_buildfile(self, formatter=AST.DEFAULT_FORMATTER):
    # Note that line numbers are 1-based.
    new_buildfile_content = \
      '\n'.join(self.buildfile_lines[0:self.target_ast.first_line-1]) + \
      self.format(formatter) + \
      '\n'.join(self.buildfile_lines[self.target_ast.last_line:])
    return new_buildfile_content


