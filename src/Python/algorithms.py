"""Graph algorithms for the campus festival assignment"""
import heapq


class DSU:
    """Disjoint-set union with path compression and union by size"""

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]
        return True


def dsu(request):
    """DSU with path compression and union by size/rank; return states"""
    n = request["n"]
    operations = request["operations"]
    d = DSU(n)
    components = n
    largest = 1 if n > 0 else 0
    states = []
    for u, v in operations:
        if d.union(u, v):
            components -= 1
            root = d.find(u)
            if d.size[root] > largest:
                largest = d.size[root]
        states.append([components, largest])
    return {"states": states}


def kruskal(request):
    """Separate Kruskal implementation; return cost, edge_ids, components"""
    n = request["n"]
    edges = request["edges"]
    order = sorted(range(len(edges)), key=lambda i: edges[i][2])
    d = DSU(n)
    cost = 0
    chosen = []
    for i in order:
        u, v, w = edges[i]
        if d.union(u, v):
            cost += w
            chosen.append(i)
    return {"cost": cost, "edge_ids": chosen, "components": n - len(chosen)}


def prim(request):
    """Separate Prim implementation; restart for every unvisited component"""
    n = request["n"]
    edges = request["edges"]
    adj = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        if u != v:
            adj[u].append((w, i, v))
            adj[v].append((w, i, u))
    visited = [False] * n
    cost = 0
    chosen = []
    components = 0
    for start in range(n):
        if visited[start]:
            continue
        components += 1
        visited[start] = True
        heap = list(adj[start])
        heapq.heapify(heap)
        while heap:
            w, i, v = heapq.heappop(heap)
            if visited[v]:
                continue
            visited[v] = True
            cost += w
            chosen.append(i)
            for item in adj[v]:
                if not visited[item[2]]:
                    heapq.heappush(heap, item)
    return {"cost": cost, "edge_ids": chosen, "components": components}


def _finish_order(n, adj):
    """Iterative DFS over all vertices; returns vertices by finish time"""
    visited = [False] * n
    pos = [0] * n
    order = []
    for s in range(n):
        if visited[s]:
            continue
        visited[s] = True
        stack = [s]
        while stack:
            u = stack[-1]
            if pos[u] < len(adj[u]):
                v = adj[u][pos[u]]
                pos[u] += 1
                if not visited[v]:
                    visited[v] = True
                    stack.append(v)
            else:
                order.append(u)
                stack.pop()
    return order


def scc(request):
    """Kosaraju with two DFS passes; return component and condensation"""
    n = request["n"]
    edges = request["edges"]
    adj = [[] for _ in range(n)]
    radj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        radj[v].append(u)
    order = _finish_order(n, adj)
    comp = [-1] * n
    count = 0
    for s in reversed(order):
        if comp[s] != -1:
            continue
        comp[s] = count
        stack = [s]
        while stack:
            u = stack.pop()
            for v in radj[u]:
                if comp[v] == -1:
                    comp[v] = count
                    stack.append(v)
        count += 1
    pairs = set()
    for u, v in edges:
        if comp[u] != comp[v]:
            pairs.add((comp[u], comp[v]))
    return {"component": comp, "condensation": [list(p) for p in pairs]}


def _topo_order(n, adj):
    """Three-state iterative DFS. Returns order or None if a cycle exists"""
    state = [0] * n  # 0 unvisited, 1 active, 2 finished
    pos = [0] * n
    finish = []
    for s in range(n):
        if state[s]:
            continue
        state[s] = 1
        stack = [s]
        while stack:
            u = stack[-1]
            if pos[u] < len(adj[u]):
                v = adj[u][pos[u]]
                pos[u] += 1
                if state[v] == 1:
                    return None
                if state[v] == 0:
                    state[v] = 1
                    stack.append(v)
            else:
                state[u] = 2
                finish.append(u)
                stack.pop()
    finish.reverse()
    return finish


def topo(request):
    """Three-state DFS and reverse finish order; return acyclic and order"""
    n = request["n"]
    edges = request["edges"]
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
    order = _topo_order(n, adj)
    if order is None:
        return {"acyclic": False, "order": []}
    return {"acyclic": True, "order": order}


def dag(request):
    """Whole-graph cycle check and DAG relaxation; add your own route helper"""
    n = request["n"]
    source = request["source"]
    edges = request["edges"]
    adj = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        adj[u].append((v, w, i))
    plain = [[v for v, _, _ in lst] for lst in adj]
    order = _topo_order(n, plain)
    if order is None:
        return {"acyclic": False, "distance": [], "parent_edge": []}
    distance = [None] * n
    parent_edge = [-1] * n
    distance[source] = 0
    for u in order:
        du = distance[u]
        if du is None:
            continue
        for v, w, i in adj[u]:
            nd = du + w
            if distance[v] is None or nd < distance[v]:
                distance[v] = nd
                parent_edge[v] = i
    return {"acyclic": True, "distance": distance, "parent_edge": parent_edge}


def reconstruct_path(source, target, parent_edge, edges):
    """Vertex route source..target from parent edge IDs.

    The route to the source is [source]. An unreachable target gives []
    """
    if target == source:
        return [source]
    if parent_edge[target] == -1:
        return []
    path = [target]
    v = target
    while v != source:
        v = edges[parent_edge[v]][0]
        path.append(v)
    path.reverse()
    return path
