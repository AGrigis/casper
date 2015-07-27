#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import unittest

# Casper import
from casper.lib.base import Graph
from casper.lib.base import GraphNode


class TestGraph(unittest.TestCase):
    """ Test sort on graph.
    """

    def setUp(self):
        """ Initialize the TestGraph class.
        """
        self.objects = ["chaussures", "chaussettes", "slip", "pantalon",
                        "ceinture", "chemise", "veste", "cravate"]
        self.dependancies = [
            ("slip", "pantalon"),
            ("chemise", "cravate"),
            ("chemise", "pantalon"),
            ("pantalon", "ceinture"),
            ("chaussettes", "chaussures"),
            ("pantalon", "chaussures"),
            ("ceinture", "chaussures"),
            ("chemise", "veste"),
        ]
        self.sorted_objects = ["slip", "chaussettes", "chemise", "veste",
                               "pantalon", "ceinture", "chaussures", "cravate"]
        self.graph = Graph()
        for o in self.objects:
            self.graph.add_node(GraphNode(o, None))
        for d in self.dependancies:
            self.graph.add_link(d[0], d[1])

    def test_raises(self):
        """ Method to test the raises.
        """
        self.assertRaises(Exception, self.graph.add_node, object())
        self.assertRaises(ValueError, self.graph.add_node,
                          self.graph._nodes[self.objects[0]])

    def test_static_sort(self):
        """ Method to test the static node sort.
        """
        static_sort = [node[0] for node in self.graph.topological_sort()]
        self.assertEqual(static_sort, self.sorted_objects)

    def test_dynamic_sort(self):
        """ Method to test the dynamic node sort.
        """
        nnil = sorted([node.name for node in self.graph.available_nodes()])
        self.assertEqual(nnil, ["chaussettes", "chemise", "slip"])
        self.graph.remove_node("slip")
        nnil = sorted([node.name for node in self.graph.available_nodes()])
        self.assertEqual(nnil, ["chaussettes", "chemise"])
        self.graph.remove_node("chemise")
        nnil = sorted([node.name for node in self.graph.available_nodes()])
        self.assertEqual(nnil, ["chaussettes", "cravate", "pantalon", "veste"])
        self.graph.remove_node("ceinture")

    def test_layout(self):
        """ Method to test the layout creation.
        """
        graph = Graph()
        self.assertEqual(sorted(graph.layout().keys()), [])
        graph.add_node(GraphNode("node1", None))
        self.assertEqual(sorted(graph.layout().keys()), ["node1"])
        graph.add_node(GraphNode("node2", None))
        self.assertEqual(sorted(graph.layout().keys()), ["node1", "node2"])


def test():
    """ Function to execute unitests.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGraph)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
