import pybgpstream
import networkx as nx
import matplotlib.pyplot as plt
import pycountry
import socket
from tqdm import tqdm
import pickle

#############################################################
####### CHANGE THIS VAR TO STOP AFTER N ASN FOUND ###########
#############################################################
AS_TO_DISCOVER = 10000
#############################################################
SAVE_FILE = 'bgp_paths.pkl'

def get_bgp_data():
    stream = pybgpstream.BGPStream(
        from_time="2024-05-01 00:00:00",  
        until_time="2024-05-01 23:59:59",
        collectors=["route-views.wide"],
        record_type="ribs"  # Using RIB records for a full routing table snapshot
    )

    print("Finding AS numbers and paths ...")

    progress_bar = tqdm(total=AS_TO_DISCOVER)
    bgp_data = set()
    asn_found = set()
    counter = 0

    for rec in stream:
        if len(asn_found) >= AS_TO_DISCOVER:
            break
        for elem in rec.record:
            if elem.type == "R":  # RIB record
                print(elem)
                as_path = elem.fields["as-path"].split(" ")
                for i in range(len(as_path) - 1):
                    src_as = as_path[i]
                    dst_as = as_path[i + 1]
                    print(src_as, dst_as)
                    bgp_data.add((src_as, dst_as))
                    if src_as not in asn_found:
                        asn_found.add(src_as)
                        progress_bar.update(1)
                    if dst_as not in asn_found:
                        asn_found.add(dst_as)
                        progress_bar.update(1)
                    counter = len(asn_found)
    progress_bar.close()
    return bgp_data

# Main

bgp_data = get_bgp_data()

print(f"Saving data...")
with open(SAVE_FILE, 'wb') as f:
    pickle.dump(bgp_data, f)
print(f"Data saved in {SAVE_FILE}.")
