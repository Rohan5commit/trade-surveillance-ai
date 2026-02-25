from __future__ import annotations

from collections import defaultdict
import networkx as nx

try:
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover
    GraphDatabase = None


class EntityGraph:
    def __init__(self, uri: str = "", user: str = "", password: str = "") -> None:
        self.local_graph = nx.DiGraph()
        self.driver = None
        if uri and GraphDatabase is not None:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        if self.driver:
            self.driver.close()

    def add_relationship(self, src: str, relation: str, dst: str) -> None:
        self.local_graph.add_node(src)
        self.local_graph.add_node(dst)
        self.local_graph.add_edge(src, dst, relation=relation)

        if self.driver:
            with self.driver.session() as session:
                session.run(
                    """
                    MERGE (a:Entity {id: $src})
                    MERGE (b:Entity {id: $dst})
                    MERGE (a)-[r:REL {type: $relation}]->(b)
                    """,
                    src=src,
                    dst=dst,
                    relation=relation,
                )

    def related_accounts(self, account_id: str, depth: int = 2) -> set[str]:
        related = set()
        if account_id not in self.local_graph:
            return related

        for node, distance in nx.single_source_shortest_path_length(self.local_graph, account_id, cutoff=depth).items():
            if node != account_id:
                related.add(node)
        return related

    def suspicious_cycles(self, max_cycle_len: int = 6) -> list[list[str]]:
        cycles = []
        for cycle in nx.simple_cycles(self.local_graph):
            if 2 <= len(cycle) <= max_cycle_len:
                cycles.append(cycle)
        return cycles

    def co_trading_clusters(self, threshold: int = 3) -> list[set[str]]:
        undirected = self.local_graph.to_undirected()
        clusters = []
        for component in nx.connected_components(undirected):
            if len(component) >= threshold:
                clusters.append(component)
        return clusters
