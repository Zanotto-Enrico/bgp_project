# BGP Peering analisy Project

## Overview

This project aims to analize the Border Gateway Protocol (BGP) peering relationships between Autonomous Systems (AS) worldwide. The graph highlights the direct connections between AS, providing insight into the structure and connectivity of the internet at the AS level. This project is part of the Network Security course at Ca' Foscari University of Venice.

## Features

- **Data Collection**: Uses the `pybgpstream` library to fetch BGP announcement data.
- **Graph Construction**: Constructs a graph where nodes represent AS and edges represent direct peering relationships.
- **Country Mapping**: Maps each AS to its respective country.
- **Visualization**: Visualizes the BGP peering graph using `networkx` and `matplotlib`.

## Requirements

- Python 3.x
- `pybgpstream`
- `networkx`
- `matplotlib`
- `pycountry`

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Zanotto-Enrico/bgp_project
   cd bgp_project
    ```

2. **Install the required libraries:**

    - bgpstream library:

        https://github.com/CAIDA/libbgpstream

    - Python dependencies:

        ```bash
        pip install pybgpstream networkx matplotlib pycountry
        ```
## Usage
1. Run the scripts:

    ```bash
    python downloader.py

    python graph_render.py
    ```

2. Explanation of the script:

    - Data Collection (get_bgp_data):

        - Configures pybgpstream to fetch BGP announcement data for a specified time range.
        - Filters only the announcement records (type A).
        - Extracts AS paths and considers only direct AS connections.

    - Country Mapping (get_country_by_asn):

        - Uses the Cymru WHOIS service to map AS numbers to country codes.
        - Converts country codes to country names using pycountry.
    
    - Graph Construction (create_bgp_graph):

        - Creates a NetworkX graph.
        - Adds nodes and edges representing AS and their direct peering relationships.
        - Annotates edges with country information.
    
    - Visualization (draw_bgp_graph):

        - Uses matplotlib to draw the BGP peering graph.
        - Colors nodes based on country information.
Example
The resulting graph provides a visual representation of the BGP peering relationships between AS. Each node represents an AS, and each edge represents a direct peering relationship. The nodes are colored based on their respective countries, allowing for a clear view of the international connectivity.

## other things

Global Internet Reachability. Prior research shows that certain countries exhibit hegemonic influence on global reachability [8], while many depend on Western countries to access common Internet destinations [10]. These instances not only jeopardize global reachability due to direct dependence on other countries and their Internet infrastructure [10], but also raise concerns about potential surveillance [22]–[24] and collateral damage [18].



Threat Model. Given the graph G(V, E), communication between any two nodes s, d ∈ V could be censored, intercepted, blocked, or in any way tampered with, ultimately harming communication between nodes s and d. This can be done anywhere on the path between s and d, and caused by nodes on this path which are unreliable, potentially malicious, with interests of deteriorating communication between s and d, or simply not trusted. Given that our assessment is done at the level of ASes, we assume that the ASes as a whole pose this threat. 





