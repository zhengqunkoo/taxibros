#!/usr/bin/env python3

"""Binary search tree.
Search range by union of disjoint canonical subsets.
Fractional cascading maybe.
"""

import unittest
import random
from .models import Location

class KdTree:

    def __init__(self, node=None):
        """Rooted tree.
        Left and right subtrees.
        """
        self.node = node
        self._left = None
        self._right = None

    def add(self, node):
        """Add node to KdTree.
        Split nodes have the lesser value of two children.
        @param node: KdNode with no children. Implements __lt__, __gt__, and __eq__.
        @return tree with added node.
        """
        cur = self
        if not cur.node:
            cur.node = node
            return

        while cur:

            if node <= cur.node:
                if cur._left:
                    cur = cur._left
                else:
                    cur._left = KdTree(node)
                    break

            elif node > cur.node:
                if cur._right:
                    cur = cur._right
                else:
                    cur._right = KdTree(node)
                    break

    def add_many(self, nodes):
        """Add many nodes to KdTree.
        """
        [self.add(node) for node in nodes]

    def search(self, node):
        """Traverse tree by comparing nodes.
        @param node: KdNode.
        @return node if found, else return None.
        """
        cur = self
        if not cur or not cur.node:
            return None
        while cur:
            if node < cur.node:
                cur = cur._left
            elif node > cur.node:
                cur = cur._right
            elif node == cur.node:
                return node
        return None

    def search_range(self, lo, hi):
        """Search subtrees only if contains query rectangle.
        If node is in query rectangle, add to subtree.
        @param lo: node representing lower left of query rectangle.
        @param hi: node representing upper right of query rectangle.
        @return subtree of nodes contained in query rectangle.
        """
        # Make lo always < hi.
        if lo > hi:
            lo, hi = hi, lo
        subtree = KdTree()
        cur_queue = [self]
        if not self.node:
            return subtree
        while cur_queue:
            cur = cur_queue.pop()
            if not cur:
                continue
            # If current node in query rectangle, add to subtree.
            if lo[0] <= cur.node[0] <= hi[0] \
               and lo[1] <= cur.node[1] <= hi[1]:
                subtree.add(cur.node)
            # If query rectangle in left/bottom subtree, do not search right/top subtree.
            if hi < cur.node:
                cur_queue.append(cur._left)
            # Else if query rectangle in right/top subtree, do not search left/bottom subtree.
            elif cur.node < lo:
                cur_queue.append(cur._right)
            # Else search both subtrees.
            else:
                if cur._left:
                    cur_queue.append(cur._left)
                cur_queue.append(cur._right)
        return subtree

    def rebalance(self):
        pass

    def search_nearest_neighbor(self):
        pass

    def __iter__(self):
        """Traverse tree in postorder.
        Yield non-None nodes.
        """
        if self._left:
            yield from iter(self._left)
        if self._right:
            yield from iter(self._right)
        if self.node:
            yield self.node

    def __repr__(self, indent=''):
        str = []
        if self.node:
            str.append(indent + self.node.__repr__() + '\n')
        if self._left:
            str.append(self._left.__repr__(indent + 'l '))
        if self._right:
            str.append(self._right.__repr__(indent + 'r '))
        return ''.join(str)

    def __str__(self):
        return self.__repr__()

    def size(self):
        """Count number of nodes.
        """
        count = 0
        if self.node:
            count += 1
        if self._left:
            count += self._left.size()
        if self._right:
            count += self._right.size()
        return count


class KdNode(Location):
    """Tags must come before location, since locations have unknown length.
    Tag coord with filename payload.
    Used to identify which file coord come from in kdtree.
    """
    def __init__(self, *coord, **kw):
        super().__init__(*coord)
        self.kw = kw

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return ','.join(map(str, self.coord))


class TestKdTree(unittest.TestCase):

    def setUp(self):
        self._tree = KdTree()
        nodes = 10
        random.seed(1)
        self._nodes = []
        for _ in range(nodes):
            self._nodes.append(KdNode(*[random.random() for _ in range(2)]))

    def test_add(self):
        """Tests if nodes added into tree without throwing error."""
        for node in self._nodes:
            self._tree.add(node)
        assert True

    def test_search(self):
        """Tests if added nodes are searchable."""
        self.test_add()
        for x, y in self._nodes:
            self.assertIsInstance(self._tree.search(KdNode(x, y)), KdNode)

    def test_search_range(self):
        """Tests if all nodes from search_range are between lo and hi."""
        self.test_add()
        lo = KdNode(0.49543508709194095, 0.4494910647887381)
        hi = KdNode(0.8357651039198697, 0.43276706790505337)
        subtree = self._tree.search_range(lo, hi)
        for node in subtree:
            self.assertTrue(lo <= node <= hi)


if __name__ == '__main__':
    unittest.main()
