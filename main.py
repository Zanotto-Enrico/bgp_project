import argparse

import pycountry
from models.as_name import get_as_name
from models.generate_graph_year import GenerateGraphYear
from matplotlib import pyplot as plt
import csv
import json
import geopandas as gpd
import numpy as np

parser = argparse.ArgumentParser(description='Process the year value.')

    # Add the arguments
parser.add_argument('year', type=int, help='The year value')
args = parser.parse_args()
year = args.year
# year=2024
def print_step(step):
    print(step)

countries = ['IT', 'IR', 'FR', 'DE', 'GB',  'CN' ]

graph=GenerateGraphYear(year)
graph.initialize_graph()
graph.calculate_centrality()
graph.calculate_country()
graph.calculate_ccp_crp_grp(countries=countries)
# Dumping graph values into a CSV file
with open('savedresults/{0}/ccp__grp_crp_values.json'.format(year), 'w') as jsonfile:
    data = {
        'Country': countries,
        'ccp': [graph.ccp[country] for country in countries],
        'crp': [graph.crp[country] for country in countries],
        'grp': [graph.grp[country] for country in countries]
    }
    json.dump(data, jsonfile)

# Reading from the same file
data=dict()
with open('savedresults/{0}/ccp__grp_crp_values.json'.format(year), 'r') as jsonfile:
    data = json.load(jsonfile)

print_step("CSV file created.")

def iso_a2_to_iso_a3(iso_a2_code):
    try:
        country = pycountry.countries.get(alpha_2=iso_a2_code)
        if country:
            return country.alpha_3
        else:
            return None
    except Exception as e:
        print("Errore durante la conversione:", e)
        return None


##############################################  Get Top 10 ASes by Betweenness Centrality

print_step("Selecting Top 10 ASes by Betweenness Centrality...")
top_10_betweenness = sorted(graph.betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
top_10_betweenness_as = [get_as_name(x[0])[:45] for x in top_10_betweenness]
top_10_betweenness_values = [x[1] for x in top_10_betweenness]

##############################################  Get Top 10 ASes by Load Centrality

print_step("Selecting Top 10 ASes by Load Centrality...")
top_10_load = sorted(graph.load_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
top_10_load_as = [get_as_name(x[0])[:45] for x in top_10_load]
top_10_load_values = [x[1] for x in top_10_load]

##############################################  Plot Top 10 Betweenness Centrality

print_step("Plotting Top 10 Betweenness Centrality...")
plt.figure(figsize=(8, 6))
plt.barh( top_10_betweenness_as, top_10_betweenness_values, color='blue')
plt.xlabel('Betweenness Centrality')
plt.ylabel('AS')
plt.title('Top 10 ASes by Betweenness Centrality')
plt.tight_layout()
plt.savefig('results/{0}/top_10_betweenness_centrality.png'.format(year))

# Plot Top 10 Load Centrality
print_step("Plotting Top 10 Load Centrality...")
plt.figure(figsize=(8, 6))
plt.barh(top_10_load_as, top_10_load_values, color='green')
plt.xlabel('Load Centrality')
plt.ylabel('AS')
plt.title('Top 10 ASes by Load Centrality')
plt.tight_layout()
plt.savefig('results/{0}/top_10_load_centrality.png'.format(year))


##############################################  Aggregating ASes by Country

print_step("Aggregating ASes by Country...")

country_betweenness = {}
country_load = {}

for as_id, bc in graph.betweenness_centrality.items():
    country = iso_a2_to_iso_a3(graph.as_to_country.get(as_id, 'Unknown'))
    country_betweenness[country] = country_betweenness.get(country, 0) + bc  * 100 + 1e-6
    country_load[country] = country_load.get(country, 0) + graph.load_centrality.get(as_id, 0) * 100 + 1e-6

##############################################  Plot World Map with Betweenness Centrality

print_step("Plotting World Map with Betweenness Centrality...")
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

world['betweenness'] = np.log(world['iso_a3'].map(country_betweenness))

plt.figure(figsize=(20, 15))
ax = plt.gca()
world.boundary.plot(ax=ax)
world.plot(column='betweenness', cmap='OrRd', legend=True, ax=ax)
plt.title('World Map by Betweenness Centrality')
ax.axis('off')  # Remove axes
plt.savefig('results/{0}/world_map_betweenness.png'.format(year), bbox_inches='tight')

##############################################  Plot World Map with Load Centrality

print_step("Plotting World Map with Load Centrality...")
world['load_centrality'] = np.log(world['iso_a3'].map(country_load))

plt.figure(figsize=(20, 15))
ax = plt.gca()
world.boundary.plot(ax=ax)
world.plot(column='load_centrality', cmap='OrRd', legend=True, ax=ax)
plt.title('World Map by Load Centrality')
ax.axis('off')  # Remove axes
plt.savefig('results/{0}/world_map_load_centrality.png'.format(year), bbox_inches='tight')

print_step("All graphs and images saved.")


##############################################  CRP and GRP

print_step("Calculating CCP, CRP and GRP...")

countries = ['IT', 'IR', 'FR', 'DE', 'GB',  'CN' ]

print_step("Plotting CCP...")

for country in countries:
    top_ccp = graph.ccp[country][:10]
    as_names = [get_as_name(x[0])[:45] for x in top_ccp]
    ccp_values = [x[1] for x in top_ccp]
    
    plt.figure(figsize=(8, 6))
    plt.barh(as_names, ccp_values, color='purple')
    plt.xlabel('Choke Potential')
    plt.ylabel('AS')
    plt.title(f'Top {len(top_ccp)} Choking Border ASes in {country}')
    plt.tight_layout()
    plt.savefig('results/{0}/ccp_{1}.png'.format(year, country))

    # Calculate cumulative CCP values for the top 10
    cumulative_ccp = [sum(ccp_values[:i+1]) for i in range(len(ccp_values))]

    # Plot the cumulative CCP line chart with area filled
    plt.figure(figsize=(8, 6))
    plt.plot([str(s)for s in top_ccp], cumulative_ccp, label='Cumulative CCP', color='blue')
    plt.fill_between([str(s)for s in top_ccp], cumulative_ccp, color='blue', alpha=0.2)
    plt.xlabel('AS')
    plt.ylabel('Cumulative Choke Potential')
    plt.title(f'Cumulative Choking Potential in {country}')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('results/{0}/cumulative_ccp_{1}.png'.format(year, country))

print_step("Plotting CRP...")

plt.figure(figsize=(10, 8))
for country in countries:
    plt.plot(range(1, len(graph.crp[country]) + 1), graph.crp[country], label=country)

plt.xlabel('Number of Top Border ASes')
plt.ylabel('Censorship Resilience Potential')
plt.title('CRP for Different Countries')
plt.legend()
plt.tight_layout()
plt.savefig('results/{0}/crp.png'.format(year))

print_step("All graphs and images saved.")


print_step("Plotting GRP...")

plt.figure(figsize=(10, 8))
for country in countries:
    plt.plot(range(1, len(graph.grp[country]) + 1), graph.grp[country], label=country)

plt.xlabel('Number of Top Border ASes')
plt.ylabel('Censorship Resilience Potential')
plt.title('GRP for Different Countries')
plt.legend()
plt.tight_layout()
plt.savefig('results/{0}/grp.png'.format(year))

print_step("All graphs and images saved.")
