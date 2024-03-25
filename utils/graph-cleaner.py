import networkx as nx

### Small script to remove nodes and edges that have 0 outgoing edges except for the destination nodes


def remove_nodes_with_zero_edges_except_final_node(graph, final_node):
    nodes_to_remove = [
        node
        for node in graph.nodes()
        if graph.degree(node) == 0 and node not in final_node
    ]
    graph.remove_nodes_from(nodes_to_remove)
    graph.remove_edges_from(
        [
            (u, v)
            for u, v in graph.edges()
            if u in nodes_to_remove or v in nodes_to_remove
        ]
    )


# Load the GML file
graph = nx.read_gml("data/routing_graph.gml")

final_node = [
    (10, 0, 31000),
    (10, 0, 33000),
    (10, 0, 35000),
    (10, 0, 37000),
    (10, 0, 39000),
]

remove_nodes_with_zero_edges_except_final_node(graph, final_node)

nx.write_gml(graph, "data/modified_graph.gml")
