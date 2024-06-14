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

MAX_AS = 12407

def print_step(step):
    print(step)

def create_as_graph(as_rel_file):
    a = set()
    G = nx.Graph()
    with open(as_rel_file, 'r') as f:
        for line in f:
            if (len(a) >= MAX_AS): break
            if line.startswith('#'):
                continue
            parts = line.strip().split('|')
            if len(parts) == 4:
                provider, customer, relation, protocol = parts
                if relation == '-1':
                    G.add_edge(provider, customer, relation='p2c')
                    a.add(customer)
                    a.add(provider)
                elif relation == '0':
                    G.add_edge(provider, customer, relation='p2p')
                    a.add(customer)
                    a.add(provider)
    print(f"found {len(a)} disctinct ASN")
    return G

as_rel_file = './20160601.as-rel2.txt'

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

G = create_as_graph(as_rel_file)

#for node, centrality in betweenness.items():
#    print(f"AS {node}: Betweenness Centrality = {centrality}")

##############################################  Calculate Betweenness Centrality
#print_step("Calculating Betweenness Centrality...")
#betweenness_centrality = nx.betweenness_centrality(G)
with open("betweenness_centrality.pickle", 'rb') as f:
    betweenness_centrality = pickle.load(f)


# saving the data
with open("betweenness_centrality.pickle", 'wb') as f:
    pickle.dump(betweenness_centrality, f)

##############################################  Calculate Load Centrality

print_step("Calculating Load Centrality...")
as_ip_counts = get_as_ipv4_addresses(betweenness_centrality.keys())
load_centrality = {as_id: bc * as_ip_counts.get(as_id, 1) for as_id, bc in betweenness_centrality.items()}

##############################################  Get Top 10 ASes by Betweenness Centrality

print_step("Selecting Top 10 ASes by Betweenness Centrality...")
top_10_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
top_10_betweenness_as = [get_as_name(x[0]) for x in top_10_betweenness]
top_10_betweenness_values = [x[1] for x in top_10_betweenness]

##############################################  Get Top 10 ASes by Load Centrality

print_step("Selecting Top 10 ASes by Load Centrality...")
top_10_load = sorted(load_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
top_10_load_as = [get_as_name(x[0]) for x in top_10_load]
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


##############################################  CCP and CRP

print_step("Calculating CCP and CRP...")

def calculate_ccp_crp(G, as_to_country, countries):
    ccp = dict()
    crp = dict()
    
    for country in countries:
        print_step(f"Calculating CCP and CRP of {country}")
        country_as = [as_id for as_id, c in as_to_country.items() if c == country]
        border_as = [as_id for as_id in country_as if any(neighbor not in country_as for neighbor in G.neighbors(as_id))]
        
        # Find all outflow paths
        outflow_paths = []
        for as_id in tqdm(country_as):
            for target in G.nodes:
                if target not in country_as:
                    try:
                        path = nx.shortest_path(G, source=as_id, target=target)
                        outflow_paths.append(path)
                    except nx.NetworkXNoPath:
                        continue
        
        outflow_paths_count = len(outflow_paths)

        ccp_values = []
        for as_id in border_as:
            choke_paths_count = sum(1 for path in outflow_paths if as_id in path)
            ccp_values.append((as_id, choke_paths_count / outflow_paths_count))
        
        ccp_values = sorted(ccp_values, key=lambda x: x[1], reverse=True)
        
        ccp[country] = ccp_values
        
        for i in range(min(len(ccp_values), 20)):
            top_as = [x[0] for x in ccp_values[:i+1]]
            choked_paths_count = sum(1 for path in outflow_paths if any(as_id in path for as_id in top_as))
            if country not in crp:
                crp[country] = []
            crp[country].append(1- (choked_paths_count / outflow_paths_count))
    
    return ccp, crp
    

countries = ['IT', 'IR', 'FR', 'DE']#, 'GB',  'CN' ]
ccp, crp = calculate_ccp_crp(G, as_to_country, countries)

print_step("Plotting CCP...")

for country in countries:
    top_ccp = ccp[country][:10]
    as_names = [get_as_name(x[0]) for x in top_ccp]
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