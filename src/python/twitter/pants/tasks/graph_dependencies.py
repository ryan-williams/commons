__author__ = 'ryan'

from pydot import *
from twitter.pants.targets import JavaLibrary, JarDependency, ScalaLibrary, JvmTarget
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

    def key_fn(target):
      return target.id

    def color_for_target(target):
      if isinstance(target, JavaLibrary):
        return "#ccccff"
      if isinstance(target, ScalaLibrary):
        return "#ccffcc"
      if isinstance(target, JarDependency):
        return "#ffcccc"
      if isinstance(target, JvmTarget):
        return "#ffffcc"
      return "#ffffff"

    def node_from_target(target):
      return Node(key_fn(target), style="filled", fillcolor=color_for_target(target))

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
        #print "\tadding node %s %s %s" % (node.get_name(), id, target.id)
        g.add_node(node)
        #print "\tnodes:"
#        for n in g.get_nodes():
#          print "\t\t%s" % n.get_name()
        if hasattr(target, 'dependencies'):
          for dependency in target.dependencies:
            g.add_edge(Edge(id, key_fn(dependency)))
            process_target(dependency, indent + 1)

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
      print "Writing graph to " + self.context.options.outfile
      g.write_png(self.context.options.outfile)


    print "targets: "
    for t in self.context.targets():
      print "\t" + str(t)

    print "root targets: "
    for t in self.context.target_roots:
      print "\t" + str(t)
