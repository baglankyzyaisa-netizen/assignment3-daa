# Assignment 3 – Analysis

Language: **Python 3** (`submission.json` = `{"language":"Python"}`). Code: `src/Python/algorithms.py`.

## Commands

```sh
python3 tools/run.py --setup                       # launch check
python3 tools/run.py --check                       # 36 public cases + state reset (all PASS)
python3 tools/run.py --input tests/my_cases.jsonl  # own requests, prints actual answers
python3 tests/test_all.py                          # own tests (2673 checks, ~2 s)
python3 tests/benchmark.py                         # Kruskal vs Prim benchmark
```

Notation: `n` vertices, `m` edges, `q` union operations. All graph traversals are iterative (explicit stacks with a per-vertex neighbour pointer), so a 100 000-vertex chain causes no recursion failure. Python integers are unbounded, so sums and distances cannot overflow.

## State reset and deep DFS

Every function builds all its data (parent arrays, adjacency lists, visited/state arrays, heaps) as **local variables** of that call; there are no module-level mutable structures. Two requests in one process therefore cannot influence each other. This is checked by `tools/run.py --check` (two batches in one process) and by `tests/test_all.py` (10 mixed requests, the 5 distinct ones repeated, outputs identical).

Deep DFS: each DFS keeps a stack of vertices and `pos[u]`, the index of the next unexplored neighbour of `u`. A vertex is resumed where it stopped, so adjacency lists are never rescanned: total work is `O(n+m)`. Stack depth is bounded by `n` and lives on the heap, not the call stack.

## Methods

### dsu
- **Steps:** `parent[i]=i`, `size[i]=1`. `find` walks to the root, then compresses the path (second pass points every node at the root). `union` links the smaller tree under the larger. After each operation append `[components, largest]`.
- **Invariant:** `parent` forms a forest whose trees are the components; `size[root]` is the exact vertex count of its tree; `components` = number of roots; `largest` = max of root sizes.
- **Correctness:** `components` decreases by one only when `union` merges two different roots; `largest` can only change on a merge, and then only the merged root's size can exceed it. Size (not rank) is maintained, so `largest` is exact.
- **Edge cases:** repeated unions and self-unions return `False` and change nothing; `n=0` gives `states=[]` and `largest=0`; `n=1` starts with `largest=1`; no initial state is emitted.
- **Complexity:** `O(n + q α(n))` time, `O(n+q)` memory (the `states` list is `O(q)`).

### kruskal
- **Steps:** sort edge IDs by weight (IDs are sorted, edges are not copied, so original IDs are preserved); scan; accept an edge iff `union(u,v)` succeeds.
- **Invariant:** the chosen edges form a forest that is contained in some minimum spanning forest (cut property: the lightest edge crossing a cut between two current components is safe).
- **Correctness:** self-loops never merge anything and are rejected; parallel edges – only the first one scanned is accepted. At the end each input component is connected, so `components = n - len(chosen)` (isolated vertices count). `n=0` gives `cost=0`, empty IDs, `components=0`. Negative weights need no special handling because only the order matters.
- **Complexity:** `O(n + m log(m+1))` time, `O(n+m)` memory.

### prim
- **Steps:** adjacency lists store `(weight, edge_id, neighbour)` (self-loops skipped). For each unvisited start vertex, count a new component, mark it visited, push its edges to a heap; repeatedly pop the lightest edge; if its endpoint is unvisited, mark it, add weight and ID, push its edges to unvisited vertices (lazy heap).
- **Invariant:** the visited part of the current component is a tree, and the popped edge is the lightest edge leaving it (cut property).
- **Correctness:** restarting from every unvisited vertex gives a spanning forest; the number of restarts is the number of components, isolated vertices included. Tuple ordering `(weight, id, vertex)` breaks ties deterministically.
- **Complexity:** `O(n + m log(m+1))` time, `O(n+m)` memory.

### scc (Kosaraju)
- **Steps:** (1) iterative DFS on the graph over all vertices, recording finish order; (2) build the transpose; (3) process vertices in decreasing finish order, each unlabelled vertex starts a DFS on the transpose, labelling everything it reaches with a new label; (4) for each edge with different labels add `(label_u,label_v)` to a hash set.
- **Invariant/correctness:** the vertex with the largest finish time lies in a source SCC of the condensation; on the transpose it can reach only its own SCC, so each second-pass DFS labels exactly one SCC and the rest follow by induction. The set removes duplicate condensation pairs; internal edges and self-loops are skipped.
- **Edge cases:** isolated vertices are their own SCC; duplicates/self-loops fine; `n=0` gives two empty arrays.
- **Complexity:** `O(n+m)` expected time (hash set), `O(n+m)` memory.

### topo
- **Steps:** three-state DFS (0 unvisited, 1 active = on the stack, 2 finished). An edge to a state-1 vertex means a cycle -> return `acyclic=false, order=[]` immediately. A vertex is marked 2 and appended to `finish` when its neighbours are exhausted. Without a cycle, the order is `finish` reversed.
- **Invariant:** state-1 vertices are exactly the current DFS path, so an edge into one closes a directed cycle; an edge into a state-2 vertex is a forward/cross edge and is not a cycle.
- **Correctness:** if `u -> v` and no cycle, `v` finishes before `u`, so after reversal `u` precedes `v`. Self-loop: `v == u` is active, so it is detected. All components are covered by the outer loop over all vertices.
- **Complexity:** `O(n+m)` time and memory.

### dag
- **Steps:** build adjacency with `(v, w, edge_id)`; run the same topological DFS over the **whole** graph (cycles unreachable from the source also give `acyclic=false`); then `distance[source]=0` and, walking the order, relax edges only from vertices with `distance != None`.
- **Invariant:** when `u` is taken from the order, all its predecessors were already processed, so `distance[u]` is final; `parent_edge[v]` is the ID of the edge that last improved `v`.
- **Correctness:** distances are exact for DAGs, also with negative weights (no Dijkstra assumption). Unreachable vertices keep `None`/`-1`, and are never relaxed from (so `None` is never added to a number). `parent_edge` stores edge IDs; the strict `<` keeps the first of tied/parallel edges.
- **Complexity:** `O(n+m)` time and memory.

### Route helper `reconstruct_path(source, target, parent_edge, edges)`
Returns `[source]` for the source, **`[]`** for an unreachable target (documented choice), otherwise follows `edges[parent_edge[v]][0]` back to the source and reverses. `O(L)` time and output space.

Actual calls (`tests/test_all.py`, also verified there):

| Case | Input | Result | Check |
|---|---|---|---|
| reachable | example graph `[[0,1,3],[0,2,8],[1,2,-7],[2,3,4]]`, target 3 | `parent_edge=[-1,0,2,3,-1]`, route `[0,1,2,3]` | edges 0,2,3 = 0→1,1→2,2→3, direction correct, cost 3-7+4 = 0 = `distance[3]` |
| source | same, target 0 | `[0]` | |
| unreachable | same, target 4 | `[]` (`distance[4]=null`) | |
| tied/parallel | n=3, `[[0,1,5],[0,1,5],[0,2,10],[1,2,5]]`, target 2 | `parent_edge=[-1,0,2]`, route `[0,2]` | selected edge IDs 2; cost 10; the alternative `0→1→2` (edges 0 or 1, then 3) also costs 10; parallel edges 0 and 1 are tied, the first (ID 0) is kept |
| long | chain of 100 000 vertices, weights -10^9 | route length 100 000 | distance `-10^9·99999` (beyond 32 bit) |

## Tests (`tests/`)

| File | Content |
|---|---|
| `test_all.py` / `test_all_output.txt` | all tests below; output `ALL 2673 CHECKS PASSED` |
| `my_cases.jsonl` / `my_cases_output.txt` | input and actual output of the sample requests, run through `tools/run.py --input` |
| `benchmark.py` / `benchmark_output.txt` | benchmark script and its actual output |

Expected answers are justified independently of the solution: brute force over all edge subsets (MST, ≤6 vertices), Floyd–Warshall style transitive closure (SCC membership, cycle detection), Bellman–Ford (DAG distances), and hand-computed values for fixed cases.

- **Boundary cases:** `n=0` for every task; `n=1`; repeated and self unions; self-loops, parallel edges and negative weights in MST; MST total `3·10^9` (beyond 32 bit); topo self-loop; DAG with a cycle unreachable from the source; unreachable vertices.
- **Randomized:** 300 small random graphs (seeded, `random.seed(12345)`) compared with the independent checkers for all tasks, including mixed cyclic/acyclic DAG inputs; DSU component counts checked against recomputation.
- **Scale:** chains of 100 000 vertices (topo, scc, scc with one big cycle, dag, route helper), random graph `n=100000, m=250000` for Kruskal/Prim (costs equal, both forests valid), 250 000 DSU operations.
- **Non-unique answers** are checked semantically: forest feasibility and cost (and optimum vs brute force), SCC membership and exact condensation, topological precedence, valid parent path with matching distances. The checkers accept an alternative valid answer (Kruskal and Prim return different edge ID orders for the same graph in `my_cases_output.txt`) and **reject invalid witnesses**: forest with a cycle, wrong cost, wrong SCC labels, wrong topological order, wrong `parent_edge`.
- **State reset:** mixed requests twice in one process.
- Public checks: `python3 tools/run.py --check` -> all 36 cases and the state-reset batch PASS.

## Benchmark: Kruskal vs Prim

- **Inputs:** random graphs from `random.Random(2024 + n)` with `u,v` uniform (loops and parallel edges possible), `w` uniform in `[-10^9, 10^9]`. The same graph object is given to both methods. Correctness was verified first (equal cost and component count, `n - components` edges in both).
- **Method:** `time.perf_counter`; 1 warm-up call, then 5 timed calls per method; only the algorithm call is timed (graph generation, JSON parsing and output are excluded for both). No compilation (Python).
- **Environment:** Apple A18 Pro, macOS 26.6.2 (arm64), CPython 3.13.13. Command: `python3 tests/benchmark.py`.

| n | m | Kruskal timings (ms) | Kruskal median | Prim timings (ms) | Prim median |
|---:|---:|---|---:|---|---:|
| 1 000 | 5 000 | 2.4, 2.4, 2.2, 2.1, 2.1 | 2.2 | 2.8, 2.9, 2.7, 2.6, 2.7 | 2.7 |
| 10 000 | 50 000 | 19.4, 19.3, 19.0, 19.0, 19.9 | 19.3 | 32.5, 35.4, 31.8, 32.8, 34.7 | 32.8 |
| 100 000 | 250 000 | 192.3, 195.1, 191.5, 199.7, 191.4 | 192.3 | 420.8, 418.7, 395.2, 390.7, 389.7 | 395.2 |

(The largest graph is sparse enough to have 656 components, so Prim also exercises restarts.)

**Observations.** Both grow roughly linearly-with-log factor, as `O(m log m)` predicts. Kruskal was about 1.2–2.1× faster here. **Limitations:** this is a constant-factor result for CPython only: Kruskal's sort runs in C (`sorted`), while Prim builds adjacency tuples and does many Python-level heap operations. It does not show that Kruskal is asymptotically better. One machine, one random graph per size, 5 runs, no density variation; other languages or denser graphs may rank them differently.

## Sources and AI use

 None
