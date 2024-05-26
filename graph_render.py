import pybgpstream
import networkx as nx
import matplotlib.pyplot as plt
import pycountry
import socket
from tqdm import tqdm
import pickle

SAVE_FILE = 'bgp_data.pkl'

class ASNLookup:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect(("whois.cymru.com", 43))
        except Exception as e:
            print(f"Error connecting to WHOIS server: {e}")
            self.conn = None

    def get_country_by_asn(self, asn):
        try:
            if not self.conn:
                self.connect()
            self.conn.sendall((f" -f -o {asn}\n").encode())
            response = ""
            while True:
                data = self.conn.recv(4096)
                if not data:
                    break
                response += data.decode()
            
            lines = response.splitlines()
            if len(lines) > 1 and len(lines[1].split("|")) >= 3:
                country_code = lines[1].split("|")[3].strip()
                return pycountry.countries.get(alpha_2=country_code).name if country_code else 'Unknown'
            return 'Unknown'
        except Exception as e:
            print(f"Error fetching country for ASN {asn}: {e}")
            self.conn.close()
            self.conn = None
            return 'Unknown'

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None


def get_country_by_asn(asn):
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect(("whois.cymru.com", 43))
        conn.sendall((f" -f -o {asn}\n").encode())
        response = ""
        while True:
            data = conn.recv(4096)
            if not data:
                break
            response += data.decode()
        conn.close()
        
        lines = response.splitlines()
        if len(lines) > 1 and len(lines[1].split("|")) >= 3:
            country_code = lines[1].split("|")[3].strip()
            return pycountry.countries.get(alpha_2=country_code).name if country_code else 'Unknown'
        return 'Unknown'
    except Exception as e:
        print(f"Error fetching country for ASN {asn}: {e}")
        return 'Unknown'

def create_bgp_graph(peers, asn_lookup):
    G = nx.Graph()
    for peer in tqdm(peers):
        asn1, asn2 = peer
        if asn1 != asn2:  # Escludi i self-loop
            # TO DO: show countries in some way
            #country1 = asn_lookup.get_country_by_asn(asn1)
            #country2 = asn_lookup.get_country_by_asn(asn2)
            G.add_edge(asn1, asn2, country1=asn1, country2=asn2)
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

# Main
asn_lookup = ASNLookup()
with open(SAVE_FILE, 'rb') as f:
    bgp_data = pickle.load(f)
    G = create_bgp_graph(bgp_data, asn_lookup)
    draw_bgp_graph(G)
    asn_lookup.close()
