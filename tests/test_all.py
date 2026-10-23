"""Own tests. Run from repo root: python3 tests/test_all.py
Non-unique answers are checked semantically (feasibility/optimum, precedence, parent paths)."""
import itertools, json, os, random, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'Python'))
import algorithms as A

ROOT = os.path.join(os.path.dirname(__file__), '..')
passed = 0

def ok(cond, name):
    global passed
    if not cond:
        print('FAIL', name); sys.exit(1)
    passed += 1

# ---------- independent checkers ----------
def comps_count(n, edges):
    p = list(range(n))
    def f(x):
        while p[x] != x:
            p[x] = p[p[x]]; x = p[x]
        return x
    for e in edges:
        p[f(e[0])] = f(e[1])
    return len({f(i) for i in range(n)})

def brute_mst(n, edges):
    """Min cost over all edge subsets that form a spanning forest (tiny graphs only)."""
    c = comps_count(n, edges); k = n - c; best = None
    for sub in itertools.combinations(range(len(edges)), k):
        if comps_count(n, [edges[i] for i in sub]) == c:
            s = sum(edges[i][2] for i in sub)
            best = s if best is None or s < best else best
    return best if k else 0

def valid_forest(n, edges, res):
    ids = res['edge_ids']
    if len(set(ids)) != len(ids) or len(ids) != n - res['components']: return False
    sub = [edges[i] for i in ids]
    if comps_count(n, sub) != res['components'] or comps_count(n, edges) != res['components']: return False
    return sum(e[2] for e in sub) == res['cost'] and all(edges[i][0] != edges[i][1] for i in ids)

def reach(n, edges):
    r = [[i == j for j in range(n)] for i in range(n)]
    for u, v in edges: r[u][v] = True
    for k in range(n):
        for i in range(n):
            if r[i][k]:
                for j in range(n): r[i][j] = r[i][j] or r[k][j]
    return r

def valid_scc(n, edges, res):
    r = reach(n, edges); c = res['component']
    for i in range(n):
        for j in range(n):
            if (c[i] == c[j]) != (r[i][j] and r[j][i]): return False
    exp = {(c[u], c[v]) for u, v in edges if c[u] != c[v]}
    got = [tuple(p) for p in res['condensation']]
    return len(got) == len(set(got)) and set(got) == exp

def valid_topo(n, edges, res):
    r = reach(n, edges)
    cyclic = any(r[i][j] and r[j][i] for i in range(n) for j in range(n) if i != j) or any(u == v for u, v in edges)
    if res['acyclic'] == cyclic: return False
    if cyclic: return res['order'] == []
    pos = {v: i for i, v in enumerate(res['order'])}
    return sorted(res['order']) == list(range(n)) and all(pos[u] < pos[v] for u, v in edges)

def bellman(n, edges, s):
    d = [None] * n; d[s] = 0
    for _ in range(n):
        for u, v, w in edges:
            if d[u] is not None and (d[v] is None or d[u] + w < d[v]): d[v] = d[u] + w
    return d

def valid_dag(req, res):
    n, edges, s = req['n'], req['edges'], req['source']
    r = reach(n, [(u, v) for u, v, _ in edges])
    cyclic = any(r[i][j] and r[j][i] for i in range(n) for j in range(n) if i != j) or any(e[0] == e[1] for e in edges)
    if res['acyclic'] == cyclic: return False
    if cyclic: return res['distance'] == [] and res['parent_edge'] == []
    if res['distance'] != bellman(n, edges, s): return False
    for v in range(n):
        pe = res['parent_edge'][v]
        if v == s or res['distance'][v] is None:
            if pe != -1: return False
        else:
            if not 0 <= pe < len(edges): return False
            u, t, w = edges[pe]
            if t != v or res['distance'][u] is None or res['distance'][u] + w != res['distance'][v]: return False
    return True

# ---------- checkers must reject bad witnesses ----------
g = [[0,1,4],[1,2,2],[0,2,3]]
ok(valid_forest(4, g, {'cost':5,'edge_ids':[1,2],'components':2}), 'accept good forest')
ok(brute_mst(4, g) == 5, 'brute optimum')
ok(valid_forest(4, g, {'cost':6,'edge_ids':[0,1],'components':2}) and 6 != brute_mst(4, g), 'feasible but non-optimal forest is caught by the optimum comparison')
ok(not valid_forest(4, g, {'cost':5,'edge_ids':[0,1],'components':2}), 'reject cost not matching ids')
ok(not valid_forest(4, g, {'cost':7,'edge_ids':[0,1,2],'components':2}), 'reject cycle witness')
ok(not valid_scc(3, [[0,1],[1,0],[1,2]], {'component':[0,1,2],'condensation':[[0,1],[1,2]]}), 'reject wrong scc')
ok(not valid_topo(3, [[0,1],[1,2]], {'acyclic':True,'order':[2,1,0]}), 'reject bad topo order')
ok(not valid_dag({'n':2,'edges':[[0,1,5]],'source':0}, {'acyclic':True,'distance':[0,5],'parent_edge':[-1,-1]}), 'reject bad parent')

# ---------- fixed edge cases ----------
ok(A.dsu({'n':0,'operations':[]}) == {'states':[]}, 'dsu n=0')
ok(A.dsu({'n':4,'operations':[[0,1],[1,2],[0,2],[3,3]]})['states'] == [[3,2],[2,3],[2,3],[2,3]], 'dsu example/repeat/self')
ok(A.dsu({'n':1,'operations':[[0,0]]})['states'] == [[1,1]], 'dsu n=1')
ok(A.kruskal({'n':0,'edges':[]}) == {'cost':0,'edge_ids':[],'components':0}, 'kruskal n=0')
ok(A.prim({'n':0,'edges':[]}) == {'cost':0,'edge_ids':[],'components':0}, 'prim n=0')
big = [[0,1,10**9],[1,2,10**9],[2,3,10**9],[3,0,10**9],[0,2,10**9]]
for f in (A.kruskal, A.prim):
    ok(f({'n':4,'edges':big})['cost'] == 3*10**9, 'MST total beyond 32 bit')
    r = f({'n':3,'edges':[[0,0,-5],[0,1,-3],[0,1,-4],[1,2,2],[1,2,2]]})
    ok(r['cost'] == -2 and r['components'] == 1 and 0 not in r['edge_ids'], 'loops/parallel/negative')
ok(A.scc({'n':0,'edges':[]}) == {'component':[], 'condensation':[]}, 'scc n=0')
ok(A.topo({'n':0,'edges':[]}) == {'acyclic':True,'order':[]}, 'topo n=0')
ok(A.topo({'n':2,'edges':[[1,1]]}) == {'acyclic':False,'order':[]}, 'topo self-loop')
ok(A.dag({'n':3,'source':0,'edges':[[1,2,1],[2,1,1]]}) == {'acyclic':False,'distance':[],'parent_edge':[]}, 'dag cycle unreachable from source')

# ---------- route helper ----------
req = {'n':5,'source':0,'edges':[[0,1,3],[0,2,8],[1,2,-7],[2,3,4]]}
res = A.dag(req)
ok(res == {'acyclic':True,'distance':[0,3,-4,0,None],'parent_edge':[-1,0,2,3,-1]}, 'dag example')
ok(A.reconstruct_path(0, 3, res['parent_edge'], req['edges']) == [0,1,2,3], 'route reachable')
ok(A.reconstruct_path(0, 0, res['parent_edge'], req['edges']) == [0], 'route to source')
ok(A.reconstruct_path(0, 4, res['parent_edge'], req['edges']) == [], 'route unreachable -> []')
treq = {'n':3,'source':0,'edges':[[0,1,5],[0,1,5],[0,2,10],[1,2,5]]}  # parallel + tied
tres = A.dag(treq)
p = A.reconstruct_path(0, 2, tres['parent_edge'], treq['edges'])
ok(tres['distance'] == [0,5,10] and p[0] == 0 and p[-1] == 2 and
   sum(treq['edges'][tres['parent_edge'][v]][2] for v in p[1:]) == 10, 'route tied/parallel')

# ---------- randomized small vs brute force ----------
random.seed(12345)
for _ in range(300):
    n = random.randint(0, 6); m = random.randint(0, 7) if n else 0
    we = [[random.randrange(n), random.randrange(n), random.randint(-5, 5)] for _ in range(m)]
    de = [e[:2] for e in we]
    for f in (A.kruskal, A.prim):
        r = f({'n':n,'edges':we})
        ok(valid_forest(n, we, r) and r['cost'] == brute_mst(n, we), f.__name__ + ' random')
    ok(valid_scc(n, de, A.scc({'n':n,'edges':de})), 'scc random')
    ok(valid_topo(n, de, A.topo({'n':n,'edges':de})), 'topo random')
    if n:
        q = {'n':n,'edges':we,'source':random.randrange(n)}
        ok(valid_dag(q, A.dag(q)), 'dag random (cyclic mix)')
        # acyclic: edges only from lower to higher index
        ae = [[min(a,b), max(a,b), w] for a, b, w in we if a != b]
        q = {'n':n,'edges':ae,'source':random.randrange(n)}
        ok(valid_dag(q, A.dag(q)), 'dag random acyclic')
    ops = [[random.randrange(n), random.randrange(n)] for _ in range(random.randint(0, 8))] if n else []
    st = A.dsu({'n':n,'operations':ops})['states']
    for i in range(len(ops)):
        ok(st[i][0] == comps_count(n, ops[:i+1]), 'dsu components random')

# ---------- scale: full published limits ----------
N, M = 100000, 250000
chain = [[i, i+1] for i in range(N-1)]
ok(A.topo({'n':N,'edges':chain})['order'] == list(range(N)), 'topo chain 100000')
ok(len(set(A.scc({'n':N,'edges':chain})['component'])) == N, 'scc chain 100000')
cyc = chain + [[N-1, 0]]
ok(len(set(A.scc({'n':N,'edges':cyc})['component'])) == 1, 'scc one big cycle')
r = A.dag({'n':N,'source':0,'edges':[[i,i+1,-10**9] for i in range(N-1)]})
ok(r['distance'][-1] == -10**9*(N-1), 'dag chain 64-bit')
ok(A.reconstruct_path(0, N-1, r['parent_edge'], [[i,i+1,0] for i in range(N-1)]) == list(range(N)), 'route length 100000')
random.seed(7)
we = [[random.randrange(N), random.randrange(N), random.randint(-10**9, 10**9)] for _ in range(M)]
rk, rp = A.kruskal({'n':N,'edges':we}), A.prim({'n':N,'edges':we})
ok(rk['cost'] == rp['cost'] and rk['components'] == rp['components'], 'big kruskal==prim')
ok(valid_forest(N, we, rk) and valid_forest(N, we, rp), 'big forests valid')
ops = [[random.randrange(N), random.randrange(N)] for _ in range(M)]
ok(len(A.dsu({'n':N,'operations':ops})['states']) == M, 'dsu 250000 ops')

# ---------- state reset via the real process (mixed requests, repeated) ----------
reqs = [{'task':'dsu','n':3,'operations':[[0,1]]}, {'task':'scc','n':2,'edges':[[0,1]]},
        {'task':'dag','n':2,'source':0,'edges':[[0,1,-1]]}, {'task':'topo','n':2,'edges':[[0,1]]}, {'task':'ping'}]
data = ''.join(json.dumps(x) + '\n' for x in reqs * 2)
out = subprocess.run([sys.executable, os.path.join(ROOT, 'src', 'Python', 'main.py')], input=data,
                     capture_output=True, text=True).stdout.splitlines()
ok(len(out) == 10 and out[:5] == out[5:], 'process state reset, mixed requests')
print(f'ALL {passed} CHECKS PASSED')
