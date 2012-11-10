__author__ = 'ryan'

import math
import re
from pydot import *
from twitter.pants.targets import *
from twitter.pants.tasks import Task

class GraphDependencies(Task):

  def __init__(self, context):
    Task.__init__(self, context)

  @classmethod
  def setup_parser(cls, option_group, args, mkflag):
    option_group.add_option(mkflag("outfile"),
      dest="outfile", default="",
      action="store", type="string",
      help="Output dependency graph to this path")

  def execute(self, targets):
    g = Dot(graph_type='digraph')

    seen_target_ids = set([])

    targets = self.context.target_roots

    def abbreviated_fs_name(target):
      pieces = target.id.split('.')
      if len(pieces) > 2 and pieces[-2] == pieces[-1]:
        pieces = pieces[:-1]
      return '.'.join(pieces).replace('src.main', '').replace('com.foursquare', '')

    def num_src_files(target):
      if isinstance(target, TargetWithSources):
        return len(target.expand_files(False, False))
      return 0

    def key_fn(target):
      return abbreviated_fs_name(target)
      #return str(num_src_files(target))
      #return target.id.replace('src.main', '').replace('com.foursquare', '')
      #return re.sub("^src/", '', str(target.address).replace('/BUILD:', ' '))

    def get_size_for_node(target):
      num = num_src_files(target)
      return .1 + math.sqrt(num) / 2, .1 + math.sqrt(num)/ 2

    def color_for_target(target):
      if isinstance(target, JavaLibrary):
        return "#ccccff"
      if isinstance(target, ScalaLibrary):
        return "#ccffcc"
      if isinstance(target, JarDependency):
        return "#ffcccc"
      if isinstance(target, JvmTarget):
        return "#ffffcc"
      if isinstance(target, JarDependency):
        return "#ffccff"
      if isinstance(target, InternalTarget):
        return "#ccffff"
      return "#ffffff"

    def node_from_target(target):
      if isinstance(target, JarDependency):
        return None
      print "*** making node: " + key_fn(target)
      width, height = get_size_for_node(target)
      return Node(key_fn(target), style="filled", fillcolor=color_for_target(target), width=width, height=height)

    print "graphing targets: " #+ "\n\t".join([str(t) for t in targets])
    for target in targets:
      print "\t%s\t%s\t%s" % (str(target), target.id, key_fn(target))
      if hasattr(target, 'dependencies'):
        print "\t\t" + "\n\t\t".join([key_fn(t) for t in target.dependencies])
    print ''

    def process_target(target, indent):
      print "%sprocessing target %s \t %s \t %s" % ("    " * indent, key_fn(target), target.id, key_fn(target))
      id = key_fn(target)
      if id not in seen_target_ids:
        seen_target_ids.add(id)

        node = node_from_target(target)
        if node:
          #print "\tadding node %s %s %s" % (node.get_name(), id, target.id)
          g.add_node(node)
        else:
          #print "\tskipping node %s" % id
          return
        #print "\tnodes:"
#        for n in g.get_nodes():
#          print "\t\t%s" % n.get_name()
        if hasattr(target, 'dependencies'):
          print "\t%d deps" % len(target.dependencies)
          for dependency in target.dependencies:
            if node_from_target(dependency):
              g.add_edge(Edge(id, key_fn(dependency)))
              process_target(dependency, indent + 1)
        else:
          print "\tno deps..?"

    for target in targets:
      process_target(target, 0)

    print ''

    print "Created graph. %d nodes, %d edges" % (len(g.get_nodes()), len(g.get_edges()))

    for node in g.get_nodes():
      print "\t%s" % node.get_name()
    print ''

    for edge in sorted(g.get_edges(), key=lambda e: e.get_source()):
      print "\t%s \t-> \t%s" % (edge.get_source(), edge.get_destination())

    if self.context.options.outfile:
      file_parts = self.context.options.outfile.split('.')
      extension = "png"
      if len(file_parts) >=2:
        extension = file_parts[-1]
      print "Writing graph to " + self.context.options.outfile
      if extension == "png":
        g.write_png(self.context.options.outfile)
      elif extension == "gv":
        g.write_xdot(self.context.options.outfile)
