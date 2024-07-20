import pickle
from matplotlib import pyplot as plt
import networkx as nx
import numpy as np
import pycountry
from models.country_by_asn import *
import pandas as pd
import geopandas as gpd
from models.as_ip_number import *
from models.as_name import *
import random


MAX_AS = 100000
PERCENT_OF_AS_TO_USE_BTWENNESS = 1
PERCENT_OF_AS_TO_USE_GRP = 0.9
PERCENT_OF_AS_TO_USE_CRP = 0.9
CHOKING_AS_TO_REMOVE = 20

class GenerateGraphYear:

    def __init__(self,year):

        self.year = year
        self.as_rel_file="data/{0}/{0}0601.as-rel2.txt".format(year)
        self.routeviews_file="data/{0}/routeviews-{0}0601.pfx2as".format(year)
        self.G= nx.Graph()
        self.ccp = dict()
        self.crp = dict()
        self.grp = dict()

    def print_step(self,step):
        print(step)

    def is_valid_path(self,path):
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = self.G.get_edge_data(u, v)

            if 'relation' in edge_data and edge_data['relation'] == 'p2c':
                continue
            elif i < len(path) - 2:
                next_hop = path[i + 2]
                next_edge_data = self.G.get_edge_data(v, next_hop)
                if 'relation' not in next_edge_data or next_edge_data['relation'] != 'p2c':
                    return False

        return True

    def find_all_valid_shortest_paths(self, source):
        valid_paths = {}
        queue = [[source]]
        visited = {source}

        while queue:
            path = queue.pop(0)
            current_node = path[-1]

            for neighbor in self.G.neighbors(current_node):
                if neighbor not in visited:
                    new_path = path + [neighbor]

                    if self.is_valid_path(new_path):
                        if neighbor not in valid_paths or len(new_path) < len(valid_paths[neighbor]):
                            valid_paths[neighbor] = new_path
                        
                        queue.append(new_path)
                        visited.add(neighbor)
        return valid_paths
    
    def initialize_graph(self):
        a = set()
        
        self.print_step("Generating The AS relational graph of year {0}...".format(self.year))

        with open(self.as_rel_file, 'r') as f:
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
                        self.G.add_edge(provider, customer, relation='p2c')
                    elif relation == '0':
                        self.G.add_edge(provider, customer, relation='p2p')
                    a.add(customer)
                    a.add(provider)

        print(f"found {len(a)} distinct ASN")

        # Adding IP counts as a node attribute
        as_ip_counts = get_as_ipv4_addresses(self.routeviews_file,a)
        for asn in a:
            self.G.nodes[asn]['ip_count'] = as_ip_counts[asn]
        self.print_step("Generated The AS relational graph of year {0}...".format(self.year))

        # Test valid path
        # source = random.choice(list(a))
        # valid_paths = self.find_all_valid_shortest_paths(source)

        # rand_path = random.choice(list(valid_paths.values()))
        # print(rand_path)

        # for i in range(len(rand_path) - 1):
        #    u, v = rand_path[i], rand_path[i + 1]
        #    edge_data = self.G.get_edge_data(u, v)
        #    print(f"{u} -> {v} : {edge_data['relation']}")
    
    def calculate_centrality(self):


        betweenness_centrality = {node: 0 for node in self.G.nodes()}
        load_centrality = {node: 0 for node in self.G.nodes()}
        
        # Sample a percentage of nodes
        sample_size = int(len(self.G.nodes()) * PERCENT_OF_AS_TO_USE_BTWENNESS)
        sampled_nodes = random.sample(list(self.G.nodes()), sample_size)

        for source in tqdm(sampled_nodes,desc="Calculating centrality of each AS... "):
            # shortest_paths = nx.single_source_shortest_path(self.G, source)
            shortest_paths = self.find_all_valid_shortest_paths(source)
            source_ip_count = self.G.nodes[source]['ip_count']
            for target, path in shortest_paths.items():
                if source != target:
                    target_ip_count = self.G.nodes[target]['ip_count']
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
        
        self.betweenness_centrality=betweenness_centrality
        self.load_centrality=load_centrality
        self.print_step("Generated Centrality of year {0}...".format(self.year))

    def calculate_country(self):
        self.as_to_country = get_country_by_asn(self.betweenness_centrality.keys())



    def find_internal_paths(self, country, country_as):
        
        # Find all internal paths (for crp)
        internal_paths = []
        for as_id in tqdm(country_as, desc=f"Calculating CRP of {country}"):
            for target in country_as:
                try:
                    path = nx.shortest_path(self.G, source=as_id, target=target)
                    internal_paths.append(path)
                except nx.NetworkXNoPath:
                    continue

        return internal_paths
    
    def find_outflow_paths(self, country, country_as, sampled_foreign_nodes):

        # Find all outflow paths of the country (for grp)
        outflow_paths = []
        for as_id in tqdm(country_as, desc=f"Calculating GRP of {country}"):
            for target in sampled_foreign_nodes:
                try:
                    path = nx.shortest_path(self.G, source=as_id, target=target)
                    outflow_paths.append(path)
                except nx.NetworkXNoPath:
                    continue

        return outflow_paths
            


    def calculate_ccp_crp_grp(self, countries):
        self.print_step("Generating ccp_crp_grp of year {0}...".format(self.year))
        for country in countries:
            country_as = [as_id for as_id, c in self.as_to_country.items() if c == country]
            border_as = [as_id for as_id in country_as if any(neighbor not in country_as for neighbor in self.G.neighbors(as_id))]
            foreign_as = [as_id for as_id, c in self.as_to_country.items() if c != country]

            sample_size = int(len(self.G.nodes()) * PERCENT_OF_AS_TO_USE_GRP)
            sampled_foreign_nodes = random.sample(foreign_as, sample_size)
            sample_size_country=int(len(country_as) * PERCENT_OF_AS_TO_USE_CRP)
            country_as=random.sample(country_as, sample_size_country)


            internal_paths = self.find_internal_paths( country, country_as)
            original_internal_paths = internal_paths.copy()
            internal_paths_count = len(internal_paths)
            
            outflow_paths = self.find_outflow_paths(country, country_as, sampled_foreign_nodes)
            original_outflow_paths = outflow_paths.copy()
            outflow_paths_count = len(outflow_paths)

            original_country_as = country_as.copy()

            # finding the country's AS with the biggest choking potential
            ccp_values = []
            
            for as_id in tqdm(country_as.copy(), desc=f"Calculating internal CRP of {country}"):
                choke_paths_count = sum(1 for path in internal_paths if as_id in path)
                if internal_paths_count == 0:
                    ccp_values.append((as_id, 0))
                else:
                    ccp_values.append((as_id, choke_paths_count / internal_paths_count))

                country_as.remove(as_id)
                internal_paths = self.find_internal_paths(country, country_as)
                internal_paths_count = len(internal_paths)
                
            
            ccp_values = sorted(ccp_values, key=lambda x: x[1], reverse=True)

            self.ccp[country] = ccp_values
            self.print_step("Generated CCP of year {0}...".format(self.year))


            # finding the country's border AS with the biggest choking potential
            country_as = original_country_as.copy()
            ccp_values_border = []
            for as_id in tqdm(border_as, desc=f"Calculating outbound CRP of {country}"):
                choke_paths_count = sum(1 for path in outflow_paths if as_id in path)
                if outflow_paths_count == 0:
                    ccp_values_border.append((as_id, 0))
                else:
                    ccp_values_border.append((as_id, choke_paths_count / outflow_paths_count))

                country_as.remove(as_id)
                outflow_paths = self.find_outflow_paths(country, country_as, sampled_foreign_nodes)
                outflow_paths_count = len(outflow_paths)
            
            ccp_values_border = sorted(ccp_values_border, key=lambda x: x[1], reverse=True)
            

            
            internal_paths = original_internal_paths
            internal_paths_count = len(internal_paths)
            outflow_paths = original_outflow_paths
            outflow_paths_count = len(outflow_paths)

            # calculating the Censorship Resilience Potential removing the AS in the country with the biggest CCP
            for i in range(min(len(ccp_values), CHOKING_AS_TO_REMOVE)):
                top_as = [x[0] for x in ccp_values[:i+1]]
                choked_paths_count = sum(1 for path in internal_paths if any(as_id in path for as_id in top_as))
                if country not in self.crp:
                    self.crp[country] = []
                if internal_paths_count == 0:
                    self.crp[country].append(1)
                else:
                    self.crp[country].append(1- (choked_paths_count / internal_paths_count))
            self.print_step("Generated CRP of year {0}...".format(self.year))

            
            # calculating the Global Reachability potential removing the border AS with the biggest CCP
            for i in range(min(len(ccp_values_border), CHOKING_AS_TO_REMOVE)):
                top_as = [x[0] for x in ccp_values_border[:i+1]]
                choked_paths_count = sum(1 for path in outflow_paths if any(as_id in path for as_id in top_as))
                if country not in self.grp:
                    self.grp[country] = []
                if outflow_paths_count == 0:
                    self.grp[country].append(1)
                else:
                    self.grp[country].append(1- (choked_paths_count / outflow_paths_count))
            self.print_step("Generated GRP of year {0}...".format(self.year))
    


        
