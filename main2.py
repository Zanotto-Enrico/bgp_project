import argparse
from as_name import get_as_name
from models.generate_graph_year import GenerateGraphYear
from matplotlib import pyplot as plt
import csv
import json

parser = argparse.ArgumentParser(description='Process the year value.')

    # Add the arguments
parser.add_argument('year', type=int, help='The year value')
# args = parser.parse_args()
# year = args.year
year=2024
def print_step(step):
    print(step)

countries = ['IT', 'IR', 'FR', 'DE', 'GB',  'CN' ]

g_2024=GenerateGraphYear(year)
g_2024.initialize_graph()
g_2024.calculate_centrality()
g_2024.calculate_country()
g_2024.calculate_ccp_crp_grp(countries=countries)
# Dumping g_2024 values into a CSV file
with open('savedresults/{0}/ccp__grp_crp_values.json'.format(year), 'w') as jsonfile:
    data = {
        'Country': countries,
        'ccp': [g_2024.ccp[country] for country in countries],
        'crp': [g_2024.crp[country] for country in countries],
        'grp': [g_2024.grp[country] for country in countries]
    }
    json.dump(data, jsonfile)

# Reading from the same file
data=dict()
with open('savedresults/{0}/ccp__grp_crp_values.json'.format(year), 'r') as jsonfile:
    data = json.load(jsonfile)

print_step("CSV file created.")
