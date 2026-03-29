#!/usr/bin/env python3
"""Conflict-free Replicated Data Types: G-Counter, PN-Counter, LWW-Register, OR-Set."""
import sys, time

class GCounter:
    """Grow-only counter."""
    def __init__(self, node_id): self.id = node_id; self.counts = {}
    def increment(self, n=1): self.counts[self.id] = self.counts.get(self.id, 0) + n
    def value(self): return sum(self.counts.values())
    def merge(self, other):
        for k, v in other.counts.items(): self.counts[k] = max(self.counts.get(k, 0), v)
    def __repr__(self): return f"GCounter({self.value()}, {self.counts})"

class PNCounter:
    """Positive-Negative counter."""
    def __init__(self, node_id):
        self.p = GCounter(node_id); self.n = GCounter(node_id); self.id = node_id
    def increment(self, n=1): self.p.increment(n)
    def decrement(self, n=1): self.n.increment(n)
    def value(self): return self.p.value() - self.n.value()
    def merge(self, other): self.p.merge(other.p); self.n.merge(other.n)
    def __repr__(self): return f"PNCounter({self.value()})"

class LWWRegister:
    """Last-Writer-Wins Register."""
    def __init__(self, node_id): self.id = node_id; self.value_ = None; self.ts = 0
    def set(self, value): self.value_ = value; self.ts = time.time()
    def get(self): return self.value_
    def merge(self, other):
        if other.ts > self.ts: self.value_ = other.value_; self.ts = other.ts
    def __repr__(self): return f"LWW({self.value_})"

class ORSet:
    """Observed-Remove Set."""
    def __init__(self, node_id):
        self.id = node_id; self.elements = {}; self.tombstones = set(); self._tag = 0
    def _next_tag(self): self._tag += 1; return f"{self.id}:{self._tag}"
    def add(self, elem):
        tag = self._next_tag(); self.elements.setdefault(elem, set()).add(tag)
    def remove(self, elem):
        if elem in self.elements:
            self.tombstones.update(self.elements[elem]); del self.elements[elem]
    def value(self):
        return {e for e, tags in self.elements.items() if tags - self.tombstones}
    def merge(self, other):
        for elem, tags in other.elements.items():
            self.elements.setdefault(elem, set()).update(tags)
        self.tombstones.update(other.tombstones)
    def __repr__(self): return f"ORSet({self.value()})"

def main():
    print("=== CRDTs Demo ===\n")
    print("G-Counter (likes):")
    a, b = GCounter("A"), GCounter("B")
    a.increment(3); b.increment(5); a.increment(2)
    print(f"  A={a.value()}, B={b.value()}")
    a.merge(b); b.merge(a)
    print(f"  After merge: A={a.value()}, B={b.value()}")

    print("\nPN-Counter (score):")
    p, q = PNCounter("P"), PNCounter("Q")
    p.increment(10); q.increment(5); p.decrement(3); q.decrement(2)
    p.merge(q); q.merge(p)
    print(f"  P={p.value()}, Q={q.value()}")

    print("\nLWW-Register:")
    r1, r2 = LWWRegister("R1"), LWWRegister("R2")
    r1.set("hello"); time.sleep(0.01); r2.set("world")
    r1.merge(r2); print(f"  After merge: {r1.get()}")

    print("\nOR-Set:")
    s1, s2 = ORSet("S1"), ORSet("S2")
    s1.add("apple"); s1.add("banana"); s2.add("cherry")
    s1.merge(s2); s2.merge(s1)
    print(f"  Both see: {s1.value()}")
    s1.remove("banana"); s1.merge(s2)
    print(f"  After S1 removes banana: {s1.value()}")

if __name__ == "__main__": main()
