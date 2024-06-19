import argparse
from models.as_name import get_as_name
from models.generate_graph_year import GenerateGraphYear
from matplotlib import pyplot as plt
import csv
import json

# parser = argparse.ArgumentParser(description='Process the year value.')

    # Add the arguments
# parser.add_argument('year', type=int, help='The year value')
# args = parser.parse_args()
# year = args.year
def print_step(step):
    print(step)

countries = ['IT', 'IR', 'FR', 'DE', 'GB',  'CN' ]
years=[2005,2008,2012,2016,2020,2024]

# g_2024=GenerateGraphYear(year)
# g_2024.initialize_graph()
# g_2024.calculate_centrality()
# g_2024.calculate_country()
# g_2024.calculate_ccp_crp_grp(countries=countries)
# # Dumping g_2024 values into a CSV file
# with open('savedresults/{0}/ccp__grp_crp_values.json'.format(year), 'w') as jsonfile:
#     data = {
#         'Country': countries,
#         'ccp': [g_2024.ccp[country] for country in countries],
#         'crp': [g_2024.crp[country] for country in countries],
#         'grp': [g_2024.grp[country] for country in countries]
#     }
#     json.dump(data, jsonfile)
datas=dict()
for i in years:    
    with open('savedresults/{0}/ccp__grp_crp_values.json'.format(i), 'r') as jsonfile:
        datas[i] = json.load(jsonfile)
# Reading from the same file
data={}
data['country']=[]
data_country=[]
for i in range(len(countries)):
    
    ofeachcountry={}
    ofeachcountry['ccp'] = []
    ofeachcountry['crp'] = []
    ofeachcountry['grp'] = []
    ccp=[]
    crp=[]
    grp=[]
    for iyear in years:
            usedata={}
            usedata=datas[iyear]
            ccp.append(usedata['ccp'][i])
            crp.append(usedata['crp'][i])
            grp.append(usedata['grp'][i])

    ofeachcountry['ccp'] = ccp
    ofeachcountry['crp'] = crp
    ofeachcountry['grp'] = grp
    data['country'] = data_country.append(ofeachcountry)
data = data_country

print_step("Divided for each country - Done.")


print_step("Plotting CCP...")
for z in range(len(countries)):
    plt.figure(figsize=(10, 8))
    target=data[z]['ccp']
    targettops=len(target)-1
    top_ccp = target[targettops][:10]
    as_names = [get_as_name(x[0])[:45] for x in top_ccp]
    ccp_values = [x[1] for x in top_ccp]

    for i in range(len(top_ccp)):
        values=[]
        for y in range(len(years)):
            for x in data[z]['ccp'][y]:
                if x[0] == top_ccp[i][0]:
                    values.append(x[1])
            if len(values) < y+1:
                values.append(0)
        plt.plot(years, values, label=as_names[i])
    plt.xlabel('Years')
    plt.xticks(years)
    plt.ylabel('CCP Values')
    plt.title('CCP of {0} though years'.format(countries[z]))
    plt.legend()
    plt.tight_layout()
    plt.savefig('results/ccp_years_{0}.png'.format(countries[z]))


print_step("Generated plot of CCP for italy - Done.")




print_step("Plotting CRP...")

plt.figure(figsize=(10, 8))
for i in range(len(countries)):
    values=[]
    for y in range(len(years)):
        lunghezza=len(data[i]['crp'][y]) 
        values.append(data[i]['crp'][y][lunghezza-1])
    
    plt.plot(years, values, label=countries[i])

plt.xlabel('Years')
plt.xticks(years)
plt.ylabel('Censorship Resilience Potential')
plt.title('CRP after 5 removes')
plt.legend()
plt.tight_layout()
plt.savefig('results/crp_years.png')

print_step("Generated plot of CRP for each Country - Done.")

print_step("Plotting GRP...")

plt.figure(figsize=(10, 8))
for i in range(len(countries)):
    
    values=[]
    for y in range(len(years)):
        values.append(data[i]['grp'][y][4])
    plt.plot(years, values, label=countries[i])

plt.xlabel('Years')
plt.xticks(years)
plt.ylabel('Censorship Resilience Potential')
plt.title('GRP after 5 removes during years')
plt.legend()
plt.tight_layout()
plt.savefig('results/grp_years.png')
print_step("Generated plot of GRP for each Country - Done.")

    
