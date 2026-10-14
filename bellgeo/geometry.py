"""Graph geometry helpers (pure Python): paths, ancilla candidates, cycle metrics.

These quantify *why* a coupling graph helps or hurts the Bell + check task:
port distance, number of shortest routes, the shortest ring through both ports (an
alternative route for checks / redundancy), girth, degree profile and how much room
there is around the ports for ancillas.
"""

from __future__ import annotations

from collections import deque

INF = 10**9


def adjacency(edges, n):
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    return [sorted(a) for a in adj]


def bfs(adj, src, blocked=frozenset()):
    dist = [INF] * len(adj)
    dist[src] = 0
    dq = deque([src])
    while dq:
        u = dq.popleft()
        for v in adj[u]:
            if v in blocked or dist[v] != INF:
                continue
            dist[v] = dist[u] + 1
            dq.append(v)
    return dist


def all_shortest_paths(adj, a, b, limit=2000):
    """All shortest paths a -> b as node lists (deterministic order, capped at ``limit``)."""
    da = bfs(adj, a)
    if da[b] == INF:
        return []
    db = bfs(adj, b)
    paths, stack = [], [[a]]
    while stack and len(paths) < limit:
        p = stack.pop()
        u = p[-1]
        if u == b:
            paths.append(p)
            continue
        for v in reversed(adj[u]):
            if da[v] == da[u] + 1 and da[v] + db[v] == da[b]:
                stack.append(p + [v])
    return sorted(paths)


def ancilla_candidates(adj, ports, radius=4, max_candidates=60):
    """Qubits within ``radius`` couplers of BOTH ports, nearest first."""
    a, b = ports
    da, db = bfs(adj, a), bfs(adj, b)
    cand = [q for q in range(len(adj)) if q not in ports and da[q] <= radius and db[q] <= radius]
    cand.sort(key=lambda q: (da[q] + db[q], q))
    return cand[:max_candidates]


def girth(adj):
    """Length of the shortest cycle (None for a tree)."""
    best = INF
    for r in range(len(adj)):
        dist = {r: 0}
        parent = {r: -1}
        dq = deque([r])
        while dq:
            u = dq.popleft()
            for v in adj[u]:
                if v not in dist:
                    dist[v], parent[v] = dist[u] + 1, u
                    dq.append(v)
                elif parent[u] != v:
                    best = min(best, dist[u] + dist[v] + 1)
    return None if best == INF else best


def ring_through_ports(adj, a, b):
    """Shortest cycle through both ports (two internally disjoint routes), or None."""
    best = INF
    for p in all_shortest_paths(adj, a, b, limit=200):
        dist = bfs(adj, a, blocked=frozenset(p[1:-1]))
        if len(p) == 2:  # adjacent ports: forbid the direct edge by hand
            continue
        if dist[b] != INF:
            best = min(best, (len(p) - 1) + dist[b])
    return None if best == INF else best


def graph_metrics(edges, n, ports):
    adj = adjacency(edges, n)
    a, b = ports
    da, db = bfs(adj, a), bfs(adj, b)
    paths = all_shortest_paths(adj, a, b)
    deg = [len(x) for x in adj]
    inner = {q for p in paths for q in p[1:-1]}
    return {
        "qubits": n,
        "couplers": len(edges),
        "avg_degree": sum(deg) / n,
        "max_degree": max(deg),
        "port_distance": da[b],
        "n_shortest_paths": len(paths),
        "ring_through_ports": ring_through_ports(adj, a, b),
        "girth": girth(adj),
        "free_neighbours_of_path": sorted(
            {v for q in inner for v in adj[q] if v not in inner and v not in ports}
        ),
        "qubits_within_4_of_both_ports": sum(
            1 for q in range(n) if q not in ports and da[q] <= 4 and db[q] <= 4
        ),
        "port_degrees": (deg[a], deg[b]),
    }
