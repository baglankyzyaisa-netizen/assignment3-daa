"""Kruskal vs Prim on identical graphs. Run: python3 tests/benchmark.py
Timer: time.perf_counter. Boundary: only the algorithm call (graph is pre-generated, no JSON
parsing, no output). 1 warm-up run, then 5 timed runs per method; median reported."""
import os, random, statistics, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'Python'))
import algorithms as A

SEED = 2024
for n, m in [(1000, 5000), (10000, 50000), (100000, 250000)]:
    rnd = random.Random(SEED + n)
    edges = [[rnd.randrange(n), rnd.randrange(n), rnd.randint(-10**9, 10**9)] for _ in range(m)]
    req = {'n': n, 'edges': edges}
    rk, rp = A.kruskal(req), A.prim(req)
    assert rk['cost'] == rp['cost'] and rk['components'] == rp['components']
    assert len(rk['edge_ids']) == len(rp['edge_ids']) == n - rk['components']
    line = f'n={n} m={m} cost={rk["cost"]} components={rk["components"]}'
    for f in (A.kruskal, A.prim):
        f(req)  # warm-up
        t = []
        for _ in range(5):
            s = time.perf_counter(); f(req); t.append(time.perf_counter() - s)
        line += f' | {f.__name__}: ' + ', '.join(f'{x*1000:.1f}' for x in t) + f' ms, median {statistics.median(t)*1000:.1f} ms'
    print(line)
