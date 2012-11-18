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
    DEFAULT_ARG_ORDER = ('org', 'name', 'repo', 'provides', 'dependencies', 'sources')
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
    def arglist_key_func(self, key_and_str):
      arg_name = key_and_str[0].split('=', 2)[0].strip()
      return self.kwarg_order_key.get(arg_name, 'Z')

    def format_token(self, token):
      if token in self.surround_with_spaces:
        return ' %s ' % token
      elif token in self.append_space:
        return '%s ' % token
      else:
        return token

    def format_list(self, context, nesting_depth, values):
      """Format a list of strings interspersed with commas."""
      multiline = context in self.multiline or context in self.multiline_compact
      indent = (nesting_depth + 1) * '  '
      values = filter(lambda x: x.strip() != ',', values)  # Ditch the comma tokens.
      sort_key_and_str = []
      i = 0
      while i < len(values):
        value = values[i]
        line_comments = []
        while i < len(values) and value.startswith('\n'):
          line_comments.append(value)
          i += 1
          value = values[i] if i < len(values) else ''
        if value.lstrip(' ').startswith('#'):  # Inline comment. Tack it on the end of the previous str.
          sort_key_and_str[-1][1] = sort_key_and_str[-1][1].rstrip() + '%s\n' % value
        else:
          if len(line_comments):
            # Line comments "belong" to the first non-comment line after them.
            line_comments_str = indent.join(line_comments)
            del line_comments[:]
          else:
            line_comments_str = ''
          if multiline:
            if len(sort_key_and_str) == 0 and context in self.multiline_compact:
              str = '%s,\n' % value
            else:
              str = '%s%s,\n' % (indent, value)
          else:
            str = '%s, ' % value
          if line_comments_str:
            str = '%s%s\n%s' % (indent, line_comments_str.lstrip(), str)
          sort_key_and_str.append([value, str])
        i += 1

      if context in self.sort_values_for:
        sort_key_and_str = sorted(sort_key_and_str)
      else:
        sort_key_and_str = sorted(sort_key_and_str, key=self.arglist_key_func)

      str = ''.join([x[1] for x in sort_key_and_str])
      if not multiline and str.endswith(', '):
        str = str[0:-2]
      if context in self.multiline:
        str = '\n%s%s' % (str, nesting_depth * '  ')
      return str

  DEFAULT_FORMATTER=Formatter()

  # Fake production code for comments. Chosen so it doesn't collide with the codes in token and symbol.
  COMMENT = -1

  @staticmethod
  def to_ast(tpl, orig_src_lines, parent=None, elide=True):
    """Convert an ast tuple (as returned by parser.st2tuple()) into a tree of AST instances.

    If elide is true we elide away all unnecessary singleton nodes. This makes for a
    more useful and readable tree.
    """
    ret = AST(tpl, parent)

    if isinstance(tpl[1], tuple):  # A non-terminal node. All elements apart from the first are tuples.
      children = [AST.to_ast(x, orig_src_lines, parent=ret, elide=elide) for x in tpl[1:]]
      if elide:
        children = [
        x.children[0] \
          if len(x.children) == 1 and x.production not in (symbol.listmaker, symbol.arglist)
          else x
          for x in children
        ]

      # Update the sibling links, and add any comment nodes.
      def append_child(child):
        if child is None:
          return
        if len(ret.children):
          ret.children[-1].right_sibling = child
          child.left_sibling = ret.children[-1]
        ret.children.append(child)

      def append_comment_node(parent, line, col, text):
        if text != '':
          tpl = (AST.COMMENT, text)
          comment = AST(tpl, parent)
          comment.start_line = comment.end_line = line
          comment.start_col = col
          comment.end_col = col + len(text) - 1
          append_child(comment)

      if not parent:
        for i, text in enumerate(orig_src_lines[0:children[0].start_line]):
          append_comment_node(ret, i, 0, text + '\n')

      prev_child = None
      for child in children:
        if prev_child and child.start_line > prev_child.end_line:
          # We've crossed a line boundary.
          if prev_child:
            suffix = orig_src_lines[prev_child.end_line][prev_child.end_col + 1:]
            append_comment_node(ret, prev_child.end_line, prev_child.end_col + 1, suffix)
          for i, text in enumerate(orig_src_lines[prev_child.end_line + 1:child.start_line]):
            append_comment_node(ret, prev_child.end_line + 1 + i, 0, '\n' + text)
        append_child(child)
        prev_child = child

      if not parent:
        for i, text in enumerate(orig_src_lines[prev_child.end_line:]):
          append_comment_node(ret, prev_child.end_line + 1, 0, text + '\n')

      # Propagate the line and col numbers upwards.
      ret.start_line = ret.children[0].start_line
      ret.end_line = ret.children[-1].end_line
      ret.start_col = ret.children[0].start_col
      ret.end_col = ret.children[-1].end_col
    else:  # A terminal node.
      if len(tpl) >= 3:  # We have line numbers.
        ret.start_line = ret.end_line = tpl[2] - 1  # We want 0-based line numbers.
        if len(tpl) >= 4:  # We have column numbers.
          ret.start_col = ret.end_col = tpl[3]
    return ret

  def __init__(self, tpl, parent):
    self.production = tpl[0]  # The production type (a value from symbol or token).
    self.tpl = tpl  # The underlying tuple.
    self.parent = parent
    self.children = []
    self.left_sibling = None
    self.right_sibling = None

    # The (0-based) start and end points of the text represented by this AST.
    # Note the end point line and col are inclusive.
    self.start_line = 0
    self.start_col = 0
    self.end_line = 0
    self.end_col = 0

  def reconstitute(self, recursion_depth=0, nesting_depth=0, formatter=DEFAULT_FORMATTER):
    """Reconstitutes the AST to a canonical form."""
    if len(self.children) == 0:  # A terminal token.
      if self.tpl[1].startswith('\n') and recursion_depth == 1:
        return self.tpl[1].lstrip() + '\n'
      return formatter.format_token(self.tpl[1])

    elif self.production == symbol.arglist or self.production == symbol.listmaker:  # A list or arglist.
      # Find the context.
      context = None
      if self.production == symbol.arglist:
        context = AST.Formatter.TOP_LEVEL if nesting_depth == 0 else \
          self.parent.left_sibling.reconstitute(recursion_depth + 1, nesting_depth + 1, formatter).strip()
      elif self.production == symbol.listmaker:
        ancestor = self.left_sibling  # The left-square-bracket token.
        while ancestor and not ancestor.left_sibling:
          ancestor = ancestor.parent
        if ancestor and ancestor.left_sibling.production == token.EQUAL:
          context = ancestor.left_sibling.left_sibling.reconstitute(
            recursion_depth + 1, nesting_depth + 1, formatter).strip()
      # Format the list in context.
      return formatter.format_list(context, nesting_depth,
        [x.reconstitute(recursion_depth + 1, nesting_depth + 1, formatter) for x in self.children])

    else:  # Some other non-terminal.
      return ''.join([x.reconstitute(recursion_depth + 1, nesting_depth, formatter) for x in self.children]) + \
             ('\n' if recursion_depth == 1 else '')  # Make sure top-level constructs are separated by a newline.

  def production_name(self):
    if self.production == AST.COMMENT:
      return 'COMMENT'
    else:
      return symbol.sym_name.get(self.production, token.tok_name.get(self.production, str(self.production)))

  def pretty_print(self, newlines=True, indent='  '):
    """Returns a pretty-printed representation of this AST.

    Useful when debugging and examining the AST structure."""
    def do_pretty_print(ast, depth=0):
      production_name = ast.production_name()
      indent_str = ('\n' if newlines else '') + depth * indent
      if len(ast.children) > 0:
        val = ', '.join([do_pretty_print(x, depth=(depth + 1)) for x in ast.children])
      else:
        val = '"%s"' % ast.tpl[1]
      return '%s[%d:%d-%d:%d] (%s, %s%s)' % \
        (indent_str, ast.start_line, ast.start_col, ast.end_line, ast.end_col, production_name, val, indent_str)
    return do_pretty_print(self)

  def __repr__(self):
    return self.pretty_print(newlines=False, indent='')

class BuildDefinition(object):
  """The source definition (actual text) of BUILD file.

  Useful for things like linting and rewriting BUILD files.
  """
  def __init__(self, buildfile_path):
    with open(buildfile_path, 'r') as infile:
      self.buildfile_content = infile.read().strip()
    self.buildfile_lines = self.buildfile_content.splitlines()

    st = parser.suite(self.buildfile_content)
    self.buildfile_ast = AST.to_ast(parser.st2tuple(st, line_info=True, col_info=True), self.buildfile_lines)

  def reformat_buildfile(self, formatter=AST.DEFAULT_FORMATTER):
    ret = self.buildfile_ast.reconstitute(formatter=formatter)
    print 'EEEEEEEEEEEEEEEEEE\n' + ret
    return ret
