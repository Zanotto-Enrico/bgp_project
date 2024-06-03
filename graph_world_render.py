import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
from models import get_country_by_asn
import pycountry

class CountryInfo:
    def __init__(self, name, isocode:str|None):
        self.name = name
        self.isocode=isocode.lower() if isocode else None

def find_node_by_country_iso(graph, country_iso:str):
    for node in graph.nodes:
        if graph.nodes[node]['info'].isocode == country_iso.lower():
            return node
    return None

# Load the world map data
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# Initialize a graph
G = nx.Graph()

# Add nodes and their geographical positions to the graph
for idx, row in world.iterrows():
    country_name = row['name']
    if row['continent']=='North America': continue
    if row['continent']=='Europe': continue
    isocode = pycountry.countries.get(alpha_3=row['iso_a3'])
    isocode=isocode.alpha_2 if isocode else None
    country_info = CountryInfo(name=country_name, isocode=isocode)
    centroid = row['geometry'].centroid
    G.add_node(country_name, pos=(centroid.x, centroid.y),info=country_info)





# Show the plot
ASpro=get_country_by_asn.ASNpro()
ASpro.start_new_search()

# Add edges (connections) between nodes
# Here, you can customize how you want to connect the countries
country_peers = set()
for asn1, asn2 in ASpro.bgp_data:
    try:
        country1 = ASpro.asn_lookup[asn1]
        country2 = ASpro.asn_lookup[asn2]
        if country1 != country2:  # Exclude self-loops
            country_peers.add((country1, country2))
    except Exception as e:
        print(f"Error processing pair ({asn1}, {asn2}): {e}")

# Creating a graph with countries
for country1, country2 in country_peers:
    name_nome_1=find_node_by_country_iso(G, country1)
    name_nome_2=find_node_by_country_iso(G, country2)
    if name_nome_1 and name_nome_2:
        G.add_edge(name_nome_1, name_nome_2)


# Get positions for all nodes
pos = nx.get_node_attributes(G, 'pos')

# Draw the world map using geopandas
ax = world.plot(figsize=(20, 15), color='white', edgecolor='black')

# Draw the networkx graph on top of the world map
nx.draw(G, pos, ax=ax.set_aspect(1.4), node_size=20, node_color='red', edge_color='blue', with_labels=False)
plt.show()
