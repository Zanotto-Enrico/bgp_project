import pybgpstream
import networkx as nx
import matplotlib.pyplot as plt
import pycountry
import socket
from tqdm import tqdm

#############################################################
####### CHANGE THIS VAR TO STOP AFTER N ASN FOUND ###########
#############################################################
AS_TO_DISCOVER = 10000
#############################################################

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

def get_bgp_data():
    stream = pybgpstream.BGPStream(
        from_time="2024-05-01 00:00:00",  
        until_time="2024-05-01 23:59:59",
        collectors=["route-views.wide"],
        record_type="ribs",
        filter="type updates"
    )
    
    progress_bar = tqdm(total=AS_TO_DISCOVER)
    bgp_data = set()
    for rec in stream:
        if  len(bgp_data) > 10000: break
        for elem in rec.record:
            if elem.type == "A":  # BGP Announcement
                as_path = elem.fields["as-path"].split(" ")
                for i in range(len(as_path) - 1):
                    src_as = as_path[i]
                    dst_as = as_path[i + 1]
                    bgp_data.add((src_as, dst_as))
                    progress_bar.update(len(bgp_data))
    return bgp_data

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
bgp_data = get_bgp_data()
G = create_bgp_graph(bgp_data, asn_lookup)
draw_bgp_graph(G)
asn_lookup.close()
