import pickle
from matplotlib import pyplot as plt
import networkx as nx
import numpy as np
import pycountry
from country_by_asn import *
import pandas as pd
import geopandas as gpd
from as_ip_number import *
from as_name import *
import random

MAX_AS = 100000
PERCENT_OF_AS_TO_USE_BTWENNESS = 0.01
PERCENT_OF_AS_TO_USE_GRP = 0.1
PERCENT_OF_AS_TO_USE_CRP = 0.1
CHOKING_AS_TO_REMOVE = 20

def print_step(step):
    print(step)

def create_as_graph(as_rel_file):
    a = set()
    G = nx.Graph()
    
    print_step("Generating The AS relational graph...")

    with open(as_rel_file, 'r') as f:
        for line in f:
            if (len(a) >= MAX_AS): break
            if line.startswith('#'):
                continue
            parts = line.strip().split('|')
            if len(parts) > 1 :
                if len(parts) == 4: 
                    provider, customer, relation, protocol = parts
                if len(parts) == 3: 
                    provider, customer, relation = parts
                if relation == '-1':
                    G.add_edge(provider, customer, relation='p2c')
                elif relation == '0':
                    G.add_edge(provider, customer, relation='p2p')
                a.add(customer)
                a.add(provider)

    print(f"found {len(a)} distinct ASN")

    # Adding IP counts as a node attribute
    as_ip_counts = get_as_ipv4_addresses(a)
    for asn in a:
        G.nodes[asn]['ip_count'] = as_ip_counts[asn]

    return G

as_rel_file = './data/2012/20120601.as-rel.txt'

def iso_a2_to_iso_a3(iso_a2_code):
    try:
        country = pycountry.countries.get(alpha_2=iso_a2_code)
        if country:
            return country.alpha_3
        else:
            return None
    except Exception as e:
        print("Errore durante la conversione:", e)
        return None

def calculate_centrality(G):

    betweenness_centrality = {node: 0 for node in G.nodes()}
    load_centrality = {node: 0 for node in G.nodes()}
    
    # Sample a percentage of nodes
    sample_size = int(len(G.nodes()) * PERCENT_OF_AS_TO_USE_BTWENNESS)
    sampled_nodes = random.sample(list(G.nodes()), sample_size)

    for source in tqdm(sampled_nodes,desc="Calculating centrality of each AS... "):
        shortest_paths = nx.single_source_shortest_path(G, source)
        source_ip_count = G.nodes[source]['ip_count']
        for target, path in shortest_paths.items():
            if source != target:
                target_ip_count = G.nodes[target]['ip_count']
                weight = source_ip_count * target_ip_count
                for node in path[1:-1]:
                    betweenness_centrality[node] += 1
                    load_centrality[node] += weight
    
    # Normalize Betweenness Centrality
    total_betweenness = sum(betweenness_centrality.values())
    if total_betweenness > 0:
        betweenness_centrality = {node: centrality / total_betweenness for node, centrality in betweenness_centrality.items()}
    
    # Normalize Load Centrality
    total_load = sum(load_centrality.values())
    if total_load > 0:
        load_centrality = {node: centrality / total_load for node, centrality in load_centrality.items()}
    
    return betweenness_centrality, load_centrality


def calculate_ccp_crp_grp(G, as_to_country, countries):
    ccp = dict()
    crp = dict()
    grp = dict()
    
    for country in countries:
        country_as = [as_id for as_id, c in as_to_country.items() if c == country]
        border_as = [as_id for as_id in country_as if any(neighbor not in country_as for neighbor in G.neighbors(as_id))]
        foreign_as = [as_id for as_id, c in as_to_country.items() if c != country]
        
        sample_size = int(len(G.nodes()) * PERCENT_OF_AS_TO_USE_GRP)
        sampled_foreign_nodes = random.sample(foreign_as, sample_size)

        # Find all internal paths (for crp)
        internal_paths = []
        for as_id in tqdm(country_as, desc=f"Calculating CRP of {country}"):
            for target in country_as:
                try:
                    path = nx.shortest_path(G, source=as_id, target=target)
                    internal_paths.append(path)
                except nx.NetworkXNoPath:
                    continue
        
        internal_paths_count = len(internal_paths)

        # Find all outflow paths of the country (for grp)
        outflow_paths = []
        for as_id in tqdm(country_as, desc=f"Calculating GRP of {country}"):
            for target in sampled_foreign_nodes:
                try:
                    path = nx.shortest_path(G, source=as_id, target=target)
                    outflow_paths.append(path)
                except nx.NetworkXNoPath:
                    continue
        
        outflow_paths_count = len(outflow_paths)


        # founding the country's AS with the biggest choking potential
        ccp_values = []
        for as_id in border_as:
            choke_paths_count = sum(1 for path in outflow_paths if as_id in path)
            ccp_values.append((as_id, choke_paths_count / outflow_paths_count))
        
        ccp_values = sorted(ccp_values, key=lambda x: x[1], reverse=True)

        ccp[country] = ccp_values


        # founding the country's border AS with the biggest choking potential
        ccp_values_border = []
        for as_id in border_as:
            choke_paths_count = sum(1 for path in outflow_paths if as_id in path)
            ccp_values_border.append((as_id, choke_paths_count / outflow_paths_count))
        
        ccp_values_border = sorted(ccp_values_border, key=lambda x: x[1], reverse=True)
        

        # calculating the Censorship Resilience Potential removing the AS in the country with the biggest CCP
        for i in range(min(len(ccp_values), 20)):
            top_as = [x[0] for x in ccp_values[:i+1]]
            choked_paths_count = sum(1 for path in internal_paths if any(as_id in path for as_id in top_as))
            if country not in crp:
                crp[country] = []
            crp[country].append(1- (choked_paths_count / internal_paths_count))

        
        # calculating the Global Reachability potential removing the border AS with the biggest CCP
        for i in range(min(len(ccp_values_border), 20)):
            top_as = [x[0] for x in ccp_values_border[:i+1]]
            choked_paths_count = sum(1 for path in outflow_paths if any(as_id in path for as_id in top_as))
            if country not in grp:
                grp[country] = []
            grp[country].append(1- (choked_paths_count / outflow_paths_count))
    
    return ccp, crp ,grp










G = create_as_graph(as_rel_file)

##############################################  Calculate Betweenness Centrality and Load centrality

betweenness_centrality, load_centrality = calculate_centrality(G)

# saving the data
with open("betweenness_centrality.pickle", 'wb') as f:
    pickle.dump(betweenness_centrality, f)
with open("load_centrality.pickle", 'wb') as f:
    pickle.dump(load_centrality, f)

##############################################  Get Top 10 ASes by Betweenness Centrality

print_step("Selecting Top 10 ASes by Betweenness Centrality...")
top_10_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
top_10_betweenness_as = [get_as_name(x[0])[:45] for x in top_10_betweenness]
top_10_betweenness_values = [x[1] for x in top_10_betweenness]

##############################################  Get Top 10 ASes by Load Centrality

print_step("Selecting Top 10 ASes by Load Centrality...")
top_10_load = sorted(load_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
top_10_load_as = [get_as_name(x[0])[:45] for x in top_10_load]
top_10_load_values = [x[1] for x in top_10_load]

##############################################  Plot Top 10 Betweenness Centrality

print_step("Plotting Top 10 Betweenness Centrality...")
plt.figure(figsize=(8, 6))
plt.barh( top_10_betweenness_as, top_10_betweenness_values, color='blue')
plt.xlabel('Betweenness Centrality')
plt.ylabel('AS')
plt.title('Top 10 ASes by Betweenness Centrality')
plt.tight_layout()
plt.savefig('results/top_10_betweenness_centrality.png')

# Plot Top 10 Load Centrality
print_step("Plotting Top 10 Load Centrality...")
plt.figure(figsize=(8, 6))
plt.barh(top_10_load_as, top_10_load_values, color='green')
plt.xlabel('Load Centrality')
plt.ylabel('AS')
plt.title('Top 10 ASes by Load Centrality')
plt.tight_layout()
plt.savefig('results/top_10_load_centrality.png')

##############################################  Aggregating ASes by Country

print_step("Aggregating ASes by Country...")

as_to_country = get_country_by_asn(betweenness_centrality.keys())
country_betweenness = {}
country_load = {}

for as_id, bc in betweenness_centrality.items():
    country = iso_a2_to_iso_a3(as_to_country.get(as_id, 'Unknown'))
    country_betweenness[country] = country_betweenness.get(country, 0) + bc  * 100 + 1e-6
    country_load[country] = country_load.get(country, 0) + load_centrality.get(as_id, 0) * 100 + 1e-6

##############################################  Plot World Map with Betweenness Centrality

print_step("Plotting World Map with Betweenness Centrality...")
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

world['betweenness'] = np.log(world['iso_a3'].map(country_betweenness))

plt.figure(figsize=(20, 15))
ax = plt.gca()
world.boundary.plot(ax=ax)
world.plot(column='betweenness', cmap='OrRd', legend=True, ax=ax)
plt.title('World Map by Betweenness Centrality')
ax.axis('off')  # Remove axes
plt.savefig('results/world_map_betweenness.png', bbox_inches='tight')

##############################################  Plot World Map with Load Centrality

print_step("Plotting World Map with Load Centrality...")
world['load_centrality'] = np.log(world['iso_a3'].map(country_load))

plt.figure(figsize=(20, 15))
ax = plt.gca()
world.boundary.plot(ax=ax)
world.plot(column='load_centrality', cmap='OrRd', legend=True, ax=ax)
plt.title('World Map by Load Centrality')
ax.axis('off')  # Remove axes
plt.savefig('results/world_map_load_centrality.png', bbox_inches='tight')

print_step("All graphs and images saved.")


##############################################  CRP and GRP

print_step("Calculating CCP, CRP and GRP...")

countries = ['IT', 'IR', 'FR', 'DE', 'GB',  'CN' ]
ccp, crp, grp = calculate_ccp_crp_grp(G, as_to_country, countries)

print_step("Plotting CCP...")

for country in countries:
    top_ccp = ccp[country][:10]
    as_names = [get_as_name(x[0])[:45] for x in top_ccp]
    ccp_values = [x[1] for x in top_ccp]
    
    plt.figure(figsize=(8, 6))
    plt.barh(as_names, ccp_values, color='purple')
    plt.xlabel('Cumulative Choke Potential')
    plt.ylabel('AS')
    plt.title(f'Top {len(top_ccp)} Choking Border ASes in {country}')
    plt.tight_layout()
    plt.savefig(f'results/ccp_{country}.png')

print_step("Plotting CRP...")

plt.figure(figsize=(10, 8))
for country in countries:
    plt.plot(range(1, len(crp[country]) + 1), crp[country], label=country)

plt.xlabel('Number of Top Border ASes')
plt.ylabel('Censorship Resilience Potential')
plt.title('CRP for Different Countries')
plt.legend()
plt.tight_layout()
plt.savefig('results/crp.png')

print_step("All graphs and images saved.")


print_step("Plotting GRP...")

plt.figure(figsize=(10, 8))
for country in countries:
    plt.plot(range(1, len(grp[country]) + 1), grp[country], label=country)

plt.xlabel('Number of Top Border ASes')
plt.ylabel('Censorship Resilience Potential')
plt.title('GRP for Different Countries')
plt.legend()
plt.tight_layout()
plt.savefig('results/grp.png')

print_step("All graphs and images saved.")