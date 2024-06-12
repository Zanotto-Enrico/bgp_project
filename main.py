import pickle
from matplotlib import pyplot as plt
import networkx as nx
import get_country_by_asn
import pandas as pd
import geopandas as gpd
import get_as_ip_number

def print_step(step):
    print(step)

def create_as_graph(as_rel_file):
    a = set()
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
                    a.add(provider)
                elif relation == '0':
                    G.add_edge(provider, customer, relation='p2p')
                    a.add(customer)
    print(f"found {len(a)} disctinct ASN")
    return G

as_rel_file = './20160601.as-rel2.txt'

G = create_as_graph(as_rel_file)

#for node, centrality in betweenness.items():
#    print(f"AS {node}: Betweenness Centrality = {centrality}")

##############################################  Calculate Betweenness Centrality
print_step("Calculating Betweenness Centrality...")
betweenness_centrality = nx.betweenness_centrality(G)

# saving the data
with open("SAVE_FILE", 'wb') as f:
    pickle.dump(betweenness_centrality, f)

##############################################  Calculate Load Centrality

print_step("Calculating Load Centrality...")
as_ip_counts = get_as_ip_number(betweenness_centrality.items())
load_centrality = {as_id: bc * as_ip_counts.get(as_id, 1) for as_id, bc in betweenness_centrality.items()}

##############################################  Get Top 20 ASes by Betweenness Centrality

print_step("Selecting Top 20 ASes by Betweenness Centrality...")
top_20_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:20]
top_20_betweenness_as, top_20_betweenness_values = zip(*top_20_betweenness)

##############################################  Get Top 20 ASes by Load Centrality

print_step("Selecting Top 20 ASes by Load Centrality...")
top_20_load = sorted(load_centrality.items(), key=lambda x: x[1], reverse=True)[:20]
top_20_load_as, top_20_load_values = zip(*top_20_load)

##############################################  Plot Top 20 Betweenness Centrality

print_step("Plotting Top 20 Betweenness Centrality...")
plt.figure(figsize=(10, 5))
plt.bar(top_20_betweenness_as, top_20_betweenness_values)
plt.xlabel('AS')
plt.ylabel('Betweenness Centrality')
plt.title('Top 20 ASes by Betweenness Centrality')
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig('results/top_20_betweenness_centrality.png')

# Step 7: Plot Top 20 Load Centrality
print_step("Plotting Top 20 Load Centrality...")
plt.figure(figsize=(10, 5))
plt.bar(top_20_load_as, top_20_load_values)
plt.xlabel('AS')
plt.ylabel('Load Centrality')
plt.title('Top 20 ASes by Load Centrality')
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig('results/top_20_load_centrality.png')

##############################################  Plot World Map with Betweenness Centrality

print_step("Aggregating ASes by Country...")

as_to_country = get_country_by_asn(betweenness_centrality.items())
country_betweenness = {}
country_load = {}

for as_id, bc in betweenness_centrality.items():
    country = as_to_country.get(as_id, 'Unknown')
    country_betweenness[country] = country_betweenness.get(country, 0) + bc
    country_load[country] = country_load.get(country, 0) + load_centrality.get(as_id, 0)
 
print_step("Plotting World Map with Betweenness Centrality...")
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
world['betweenness'] = world['name'].map(country_betweenness)

plt.figure(figsize=(15, 10))
world.boundary.plot()
world.plot(column='betweenness', cmap='OrRd', legend=True)
plt.title('World Map by Betweenness Centrality')
plt.savefig('results/world_map_betweenness.png')

##############################################  Plot World Map with Load Centrality

print_step("Plotting World Map with Load Centrality...")
world['load_centrality'] = world['name'].map(country_load)

plt.figure(figsize=(15, 10))
world.boundary.plot()
world.plot(column='load_centrality', cmap='OrRd', legend=True)
plt.title('World Map by Load Centrality')
plt.savefig('results/world_map_load_centrality.png')

print_step("All graphs and images saved.")
