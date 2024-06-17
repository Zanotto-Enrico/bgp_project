import os
import pickle
import socket
from tqdm import tqdm


CACHE_FILE = "as_nationality_cache.pickle"

def load_cache(asn_set):
    """Load cache from pickle file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return {k: v for k, v in pickle.load(f).items() if k in asn_set}

    return {}

def save_cache(cache):
    """Save cache to pickle file."""
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache, f)

def get_country_by_asn(asn_set):
    results = load_cache(asn_set)
    chunk_size = 200
    asn_list = [n for n in asn_set if n not in results]
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

    save_cache(results)
    return results
