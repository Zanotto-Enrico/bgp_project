import os
import networkx as nx
import matplotlib.pyplot as plt
import pycountry
import socket
from tqdm import tqdm
import pickle
import time
import plotly.graph_objects as go

SAVE_FILE1 = 'bgp_paths.pkl'
SAVE_FILE2 = 'asn_lookup.pkl'


def get_country_by_asn(asn_set):
    results = {}
    chunk_size = 200
    asn_list = list(asn_set)
    print(f"looking up coutry codes for {len(asn_list)} asn...")
    for i in tqdm(range(0, len(asn_list), chunk_size)):
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect(("whois.cymru.com", 43))
            asn_chunk = asn_list[i:i+chunk_size]
            conn.sendall(''.join([f" -v AS{asn}\n" for asn in asn_chunk]).encode())
            
            response = ""
            while True:
                data = conn.recv(30000) # 30000 bytes should be enough
                if not data:
                    break
                response += data.decode()
            conn.close()
            
            lines = response.splitlines()
            for line in (line for line in lines if not line.startswith("AS")):  # Skip the header line
                parts = line.split("|")
                if len(parts) >= 3:
                    asn = parts[0].strip()
                    country_code = parts[1].strip()
                    country = pycountry.countries.get(alpha_2=country_code) if country_code else None
                    country_name = country.name if country  else 'Unknown'
                    results[asn] = country_name
                else:
                    results[asn] = 'Unknown'
        except Exception as e:
            print(f"Error fetching country for ASNs {asn_chunk}: {e}")
            for asn in asn_chunk:
                results[asn] = 'Unknown'
    return results

def create_bgp_graph(peers, asn_lookup):
    G = nx.Graph()
    a = 0
    for peer in tqdm(peers):
        asn1, asn2 = peer
        try:
            if asn1 != asn2:  # Escludi i self-loop
                # TO DO: show countries in some way
                country1 = asn_lookup[asn1]
                country2 = asn_lookup[asn2]
                #print(country1, country2)
                G.add_edge(asn1, asn2, country1=country1, country2=country2)
        except Exception as e:
            print("Malformed data: ", peer)
    return G

def draw_bgp_graph(G):
    pos = nx.spring_layout(G)
    plt.figure(figsize=(12, 8))

    countries = nx.get_edge_attributes(G, 'country1')
    colors = {country: i for i, country in enumerate(set(countries.values()))}
    node_colors = [colors[countries[(u, v)]] for u, v in G.edges()]

    nx.draw(G, pos, edge_color=node_colors, with_labels=True, node_size=50, font_size=8)
    plt.title("BGP Peering Graph")
    plt.show()

def create_country_graph(bgp_data, asn_lookup):
    country_peers = set()
    for asn1, asn2 in bgp_data:
        try:
            country1 = asn_lookup[asn1]
            country2 = asn_lookup[asn2]
            if country1 != country2:  # Exclude self-loops
                country_peers.add((country1, country2))
        except Exception as e:
            print(f"Error processing pair ({asn1}, {asn2}): {e}")

    # Creating a graph with countries
    G = nx.Graph()
    for country1, country2 in tqdm(country_peers):
        G.add_edge(country1, country2)
    return G


# Drawing the country-level BGP graph
def draw_country_graph(G):
    pos = nx.spring_layout(G, k=0.9)  
    plt.figure(figsize=(15, 10))
    nx.draw(G, pos, with_labels=True, node_size=50, font_size=8, edge_color='gray', alpha=0.7)
    plt.title("Country-level BGP Peering Graph")
    plt.show()


# Main
with open(SAVE_FILE1, 'rb') as f:
    # loading links between AS
    bgp_data = pickle.load(f)
    
    #TODO loading possible asn_lookup data cached
    asn_lookup = {}
    #if os.path.exists(SAVE_FILE2):
    #    asn_lookup = pickle.load(open(SAVE_FILE2, 'rb')) 

    # looking for as number not yes looked up
    as_to_lookup = set([e[0] for e in bgp_data] + [e[1] for e in bgp_data])
    asn_lookup.update( get_country_by_asn(as_to_lookup))

    # saving the new found data
    #with open(SAVE_FILE2, 'wb') as f:
    #    pickle.dump(bgp_data, f)
    
    G1 = create_bgp_graph(bgp_data, asn_lookup)
    draw_bgp_graph(G1)
    G2 = create_country_graph(bgp_data, asn_lookup)
    draw_country_graph(G2)


    

