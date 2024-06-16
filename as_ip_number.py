import os
import pickle
import requests
from tqdm import tqdm

file_path = "data/routeviews-rv2-20240613-0800.pfx2as"

def get_as_ipv4_addresses(as_numbers):
    
    with open(file_path, 'r') as f:
        total_lines = sum(1 for _ in f)

    as_ip_dict = { n:0 for n in as_numbers }
    
    with open(file_path, 'r') as f:
        for line in tqdm(f, total=total_lines, desc="Calculating the size of each AS...   "):
            _, mask, as_number = line.strip().split()
            as_numbers = as_number.split(",")
            mask = int(mask)
            # Calculate the number of IP addresses based on the subnet mask
            num_ips = 2**(32 - mask)
            # Add the number of IPs to the AS number
            for n in as_numbers: 
                if n in as_ip_dict:
                    as_ip_dict[n] = as_ip_dict[n] + num_ips

    return as_ip_dict

