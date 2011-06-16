# -*- coding: utf-8 -*-
"""
Lattice topology in which each node is connected with each of its 8 neighbors
(Moore Neighborhood).  The radius of interactions can be defined, which means
all nodes within this many hops will be considered a neighbor.

This topology was originally presented and used used in the publication:

    B.D. Connelly, L. Zaman, C. Ofria, and P.K. McKinley, "Social structure and
    the maintenance of biodiversity," in Proceedings of the 12th International
    Conference on the Synthesis and Simulation of Living Systems (ALIFE), pp.
    461-468, 2010.

"""

__author__ = "Brian Connelly <bdc@msu.edu>"
__credits__ = "Brian Connelly, Luis Zaman, Philip McKinley, Charles Ofria"


import networkx as nx

from seeds.Topology import *


class MooreTopology(Topology):
    """
    Lattice topology with Moore Neighborhoods with configurable radius

    Nodes are organized on a lattice.  A node's neighbors reside to the
    left, right, above, below, and on the diagonals.  With radius 1, this
    neighborhood will contain 8 nodes.  With radius 2, the 24 nodes within
    a 2-hop distance are included.

    Configuration: All configuration options should be specified in the
        MooreTopology block (unless otherwise specified by the config_section
        parameter).

        size: Width/height, in number of nodes, of the Experiment.  With size
            10, there would be 100 nodes. (no default)
        periodic: Whether or not the Experiment should form a torus.
            This means that nodes on the left border are neighbors with
            nodes on the right border. (default: False)
        radius: Number of hops within a focal node's neighborhood
            (default: 1)

    Example:
        [MooreTopology]
        size = 100
        periodic = True
        radius = 4


    """
    def __init__(self, experiment, config_section='MooreTopology'):
        """Initialize a MooreTopology object"""
        super(MooreTopology, self).__init__(experiment, config_section=config_section)

        self.size = self.experiment.config.getint(self.config_section, 'size')
        self.periodic = self.experiment.config.getboolean(self.config_section, 'periodic', default=False)
        self.radius = self.experiment.config.getint(self.config_section, 'radius', default=1)

        if self.radius >= self.size:
            print 'Error: Radius cannot be bigger than experiment!'

        self.graph = self.moore_2d_graph(self.size, self.size,
                                         radius=self.radius,
                                         periodic=self.periodic)

        for n in self.graph.nodes():
            self.graph.node[n]['coords'] = (self.row(n)/float(self.size), self.column(n)/float(self.size))

    def __str__(self):
        """Produce a string to be used when an object is printed"""
        return 'Moore Topology (%d nodes, %d radius)' % (self.size * self.size, self.radius)

    def row(self, nodeid):
        """Get the number of the row in which the given node is located

        Parameters:

        *nodeid*
            The ID of the node in question

        """
        return (nodeid/self.size)

    def column(self, nodeid):
        """Get the number of the column in which the given node is located

        Parameters:

        *nodeid*
            The ID of the node in question

        """
        return nodeid % self.size

    def node_id(self, row, col):
        """Get the ID of the node at the given row and column

        Parameters:

        *row*
            The row in which the node is located
        *col*
            The column in which the node is located

        """
        return row * self.size + col

    def moore_2d_graph(self, rows=0, columns=0, radius=0,
                       periodic=False):
        """ Return the 2d grid graph of rows x columns nodes,
            each connected to its nearest Moore neighbors within
            a given radius.
            Optional argument periodic=True will connect
            boundary nodes via periodic boundary conditions.

        Parameters:

        *rows*
            The number of rows to be in the graph
        *columns*
            The number of columns to be in the graph
        *radius*
            The radius of interactions in the graph (there will be an edge
            between a node and all other nodes within N hops)
        *periodic*
            Prevent edge effects using periodic boundaries

        """
        G = nx.empty_graph()
        G.name = "moore_2d_radius_graph"
        G.add_nodes_from(range(rows * columns))

        for n in G.nodes():
            myrow = self.row(n)
            mycol = self.column(n)

            for r in xrange(myrow - radius, myrow + radius + 1):
                if periodic == False and (r < 0 or r >= rows):
                    continue

                for c in xrange(mycol - radius, mycol + radius + 1):
                    if periodic == False and (c < 0 or c >= columns):
                        continue

                    nid = self.node_id(r % rows, c % columns)

                    if nid != n:
                        neighbor_id = ((r % rows) * self.size) + (c % columns)
                        G.add_edge(n, neighbor_id)

        return G

