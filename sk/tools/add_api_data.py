#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_slovak3 (https://knot.fit.vutbr.cz/wiki/index.php/entity_kb_slovak3)
Autor: Samuel Križan (xkriza06)
Popis suboru:
Subor je urceny na pridavanie dat z wikipedia api do kb
"""

import requests
import csv
import re
import time
import argparse



console_args_parser = argparse.ArgumentParser()
console_args_parser.add_argument(
    "src",
    default="../kb_sk",
    type=str,
)
console_args = console_args_parser.parse_args()

TYPE = 1
DESCRIPTION = 5
ORIGINAL_WIKINAME = 6
WIKIDATA_ID = 9
LATITUDE = 10
LONGITUDE = 11
GENDER = 10

WIKI_API_URL_SK = "https://sk.wikipedia.org/w/api.php"
WIKI_API_URL_CZ = "https://cs.wikipedia.org/w/api.php"
WIKI_API_PARAMS_BASE = {
    "action": "query",
    "format": "json",
}


def get_api_data(title) -> dict:
    wiki_api_params = WIKI_API_PARAMS_BASE.copy()
    wiki_api_params["prop"] = "coordinates|pageprops"
    wiki_api_params["titles"] = title
    data = dict()
    data["id"] = ""
    data["lat"] = ""
    data["lon"] = ""
    try:
        time.sleep(0.1)
        r = requests.get(WIKI_API_URL_SK, params=wiki_api_params)
        pages = r.json()["query"]["pages"]
        first_page = next(iter(pages))
        try:
            data["id"] = pages[first_page]["pageprops"]['wikibase_item']
        except:
            r = requests.get(WIKI_API_URL_CZ, params=wiki_api_params)
            pages = r.json()["query"]["pages"]
            first_page = next(iter(pages))
            try:
                data["id"] = pages[first_page]["pageprops"]['wikibase_item']
            except:
                pass
        try:
            if first_page != "-1":
                data["lat"] = pages[first_page]["coordinates"][0]["lat"]
                data["lon"] = pages[first_page]["coordinates"][0]["lon"]
        except:
            pass
    except:
        pass
    return data


def insert_api_data(old_row):
    if not old_row[WIKIDATA_ID]:
        data = get_api_data(old_row[ORIGINAL_WIKINAME])
        if data["id"] != "":
            old_row[WIKIDATA_ID] = data["id"]
        if data["lat"] != "":
            if old_row[TYPE] in ["country", "country:former", "geo:peninsula", "geo:continent"]:
                old_row[LATITUDE] = data["lat"]
            elif old_row[TYPE] in ["settlement", "watercourse", "waterarea", "geo:relief", "geo:waterfall", "geo:island"]:
                old_row[LATITUDE+1] = data["lat"]
        if data["lon"] != "":
            if old_row[TYPE] in ["country", "country:former", "geo:peninsula", "geo:continent"]:
                old_row[LONGITUDE] = data["lon"]
            elif old_row[TYPE] in ["settlement", "watercourse", "waterarea", "geo:relief", "geo:waterfall", "geo:island"]:
                old_row[LONGITUDE+1] = data["lon"]



if __name__ == "__main__":
    with open(console_args.src) as to_read:
        old = list(csv.reader(to_read, delimiter="\t"))
        with open(console_args.src+"new", "w") as to_write:
            new = csv.writer(to_write, delimiter="\t")
            for old_row in old:
                insert_api_data(old_row)
                new.writerow(old_row)
