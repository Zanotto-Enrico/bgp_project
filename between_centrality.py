import networkx as nx

def create_as_graph(as_rel_file):
    G = nx.Graph()
    with open(as_rel_file, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            parts = line.strip().split('|')
            if len(parts) == 4:
                provider, customer, relation, protocol = parts
                if relation == '-1':
                    G.add_edge(provider, customer, relation='p2c')
                elif relation == '0':
                    G.add_edge(provider, customer, relation='p2p')
    return G

as_rel_file = './20160601.as-rel2.txt'

G = create_as_graph(as_rel_file)

betweenness = nx.betweenness_centrality(G)

for node, centrality in betweenness.items():
    print(f"AS {node}: Betweenness Centrality = {centrality}")
