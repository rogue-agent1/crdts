#!/usr/bin/env python3
"""CRDTs — Conflict-free Replicated Data Types for distributed systems."""
import sys

class GCounter:
    """Grow-only counter — always converges via max merge."""
    def __init__(self, node):
        self.node = node; self.counts = {}
    def increment(self, n=1):
        self.counts[self.node] = self.counts.get(self.node, 0) + n
    def value(self): return sum(self.counts.values())
    def merge(self, other):
        for k, v in other.counts.items():
            self.counts[k] = max(self.counts.get(k, 0), v)

class PNCounter:
    """Positive-Negative counter — supports increment and decrement."""
    def __init__(self, node):
        self.p = GCounter(node); self.n = GCounter(node)
    def increment(self, n=1): self.p.increment(n)
    def decrement(self, n=1): self.n.increment(n)
    def value(self): return self.p.value() - self.n.value()
    def merge(self, other): self.p.merge(other.p); self.n.merge(other.n)

class LWWRegister:
    """Last-Writer-Wins register — timestamp-based conflict resolution."""
    def __init__(self):
        self.val = None; self.ts = 0
    def set(self, value, ts):
        if ts > self.ts: self.val = value; self.ts = ts
    def get(self): return self.val
    def merge(self, other):
        if other.ts > self.ts: self.val = other.val; self.ts = other.ts

class GSet:
    """Grow-only set — elements can only be added."""
    def __init__(self): self.items = set()
    def add(self, item): self.items.add(item)
    def __contains__(self, item): return item in self.items
    def merge(self, other): self.items |= other.items
    def value(self): return sorted(self.items)

class ORSet:
    """Observed-Remove set — add and remove with unique tags."""
    def __init__(self, node):
        self.node = node; self.elements = {}; self.tombstones = set(); self._tag = 0
    def add(self, item):
        self._tag += 1
        tag = f"{self.node}:{self._tag}"
        self.elements[tag] = item
    def remove(self, item):
        for tag, val in list(self.elements.items()):
            if val == item: self.tombstones.add(tag)
    def value(self):
        return sorted(set(v for t, v in self.elements.items() if t not in self.tombstones))
    def merge(self, other):
        self.elements.update(other.elements)
        self.tombstones |= other.tombstones

if __name__ == "__main__":
    print("=== G-Counter ===")
    a, b = GCounter("A"), GCounter("B")
    a.increment(3); b.increment(5); a.increment(2)
    print(f"A={a.value()}, B={b.value()}")
    a.merge(b); b.merge(a)
    print(f"After merge: A={a.value()}, B={b.value()}")

    print("\n=== PN-Counter ===")
    c, d = PNCounter("C"), PNCounter("D")
    c.increment(10); d.increment(3); c.decrement(4)
    c.merge(d); d.merge(c)
    print(f"C={c.value()}, D={d.value()}")

    print("\n=== LWW-Register ===")
    r1, r2 = LWWRegister(), LWWRegister()
    r1.set("hello", 1); r2.set("world", 2)
    r1.merge(r2)
    print(f"Winner: {r1.get()} (latest ts wins)")

    print("\n=== OR-Set ===")
    s1, s2 = ORSet("X"), ORSet("Y")
    s1.add("a"); s1.add("b"); s2.add("b"); s2.add("c")
    s1.merge(s2)
    print(f"Before remove: {s1.value()}")
    s1.remove("b")
    print(f"After remove b: {s1.value()}")
