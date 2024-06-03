import os

import networkx as nx
import matplotlib.pyplot as plt
import pycountry
import socket
from tqdm import tqdm
import pickle
import time


SAVE_FILE1 = 'bgp_paths.pkl'
SAVE_FILE2 = 'asn_lookup.pkl'

class ASNpro:
    def __init__(self):
        # loading links between AS
        with open(SAVE_FILE1, 'rb') as f:
            self.bgp_data = pickle.load(f)
    
        #TODO loading possible asn_lookup data cached
        self.asn_lookup = {}
        #if os.path.exists(SAVE_FILE2):
        #    asn_lookup = pickle.load(open(SAVE_FILE2, 'rb')) 

        # looking for as number not yes looked up
        self.as_to_lookup = set([e[0] for e in self.bgp_data] + [e[1] for e in self.bgp_data])
        

    def start_new_search(self):
        self.asn_lookup.update( self.get_country_by_asn(self.as_to_lookup))

    def get_country_by_asn(self,asn_set):
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
                        results[asn] = country_code if country_code else 'Unknown'
                    else:
                        results[asn] = 'Unknown'
            except Exception as e:
                print(f"Error fetching country for ASNs {asn_chunk}: {e}")
                for asn in asn_chunk:
                    results[asn] = 'Unknown'
        return results
