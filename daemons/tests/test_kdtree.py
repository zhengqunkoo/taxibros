from unittest.mock import patch
from daemons.download import DownloadJson, TaxiAvailability
from daemons.models import Location
import unittest
from daemons.kdtree import *


class TestKdTree(unittest.TestCase):

    def setUp(self):
        self._tree = KdTree()
        nodes = 10
        random.seed(1)
        self._nodes = []
        for _ in range(nodes):
            self._nodes.append(
                KdNode(
                    Location(roadID="test", lat=random.random(), lng=random.random())
                )
            )

    def test_add(self):
        """Tests if nodes added into tree without throwing error."""
        for node in self._nodes:
            self._tree.add(node)
        assert True

    def test_search(self):
        """Tests if added nodes are searchable."""
        self.test_add()
        for node in self._nodes:
            self.assertIsInstance(
                self._tree.search(
                    KdNode(
                        Location(
                            roadID="test2", lat=node.location.lat, lng=node.location.lng
                        )
                    )
                ),
                KdNode,
            )

    def test_search_range(self):
        """Tests if all nodes from search_range are between lo and hi."""
        self.test_add()
        lo = KdNode(
            Location(roadID="lo", lat=0.49543508709194095, lng=0.4494910647887381)
        )
        hi = KdNode(
            Location(roadID="lo", lat=0.8357651039198697, lng=0.43276706790505337)
        )
        subtree = self._tree.search_range(lo, hi)
        for node in subtree:
            self.assertTrue(lo <= node <= hi)
