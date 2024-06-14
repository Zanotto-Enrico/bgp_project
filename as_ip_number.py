import os
import pickle
import requests
from tqdm import tqdm

CACHE_FILE = "as_ipv4_addresses_cache.pickle"

def load_cache():
    """Load cache from pickle file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_cache(cache):
    """Save cache to pickle file."""
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache, f)

def get_as_ipv4_addresses(as_numbers):

    as_ipv4_addresses = {}
    cache = load_cache()

    for as_number in tqdm(as_numbers):

        # Use cached data if available
        if as_number in cache:
            as_ipv4_addresses[as_number] = cache[as_number]
            continue  

        try:
            # Query the RIPE NCC REST API for AS number information
            response = requests.get(f"https://stat.ripe.net/data/announced-prefixes/data.json?resource={as_number}")
            data = response.json()

            if response.status_code == 200 and 'data' in data and 'prefixes' in data['data']:
                prefixes = data['data']['prefixes']
                total_addresses = 0
                for prefix in prefixes:
                    prefix = prefix["prefix"]
                    if ':' in prefix:
                        continue
                    # Extract the network mask from the prefix
                    network_mask = int(prefix[prefix.find("/")+1:])
                    # Calculate the number of available IPv4 addresses
                    available_addresses = 2 ** (32 - network_mask)
                    total_addresses += available_addresses

                as_ipv4_addresses[as_number] = total_addresses
                cache[as_number] = total_addresses
            else:
                as_ipv4_addresses[as_number] = {'error': 'No data found'}

        except Exception as e:
            as_ipv4_addresses[as_number] = {'error': str(e)}

    save_cache(cache) 
    return as_ipv4_addresses
