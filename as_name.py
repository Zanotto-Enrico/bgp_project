import os
import pickle
import requests
from tqdm import tqdm



def get_as_name(as_number):
    url = "https://stat.ripe.net/data/as-names/data.json?resource=AS{}".format(as_number)
    response = requests.get(url)
    data = response.json()
    if data["status"] == "ok":
        return data["data"]["names"][as_number]
    else:
        return "Nome non disponibile per ASN {}".format(as_number)


