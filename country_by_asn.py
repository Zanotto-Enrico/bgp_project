import socket
from tqdm import tqdm

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
                    results[asn] = country_code if country_code else 'Unknown'
                else:
                    results[asn] = 'Unknown'
        except Exception as e:
            print(f"Error fetching country for ASNs {asn_chunk}: {e}")
            for asn in asn_chunk:
                results[asn] = 'Unknown'

    return results
