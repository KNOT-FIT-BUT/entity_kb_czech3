#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_slovak3 (https://knot.fit.vutbr.cz/wiki/index.php/entity_kb_slovak3)
Autor: Samuel Križan (xkriza06)
Popis suboru:
Subor je urceny na porovnanie dvoch verzii kb vo formate kb_sk (prvej fazy tvorby kb)
"""

import csv
import re
from re import split
import requests
import sys



NEW_ENTITIES_FILE = "new_entities.tsv"


'''
ID = 0
TYPE=1
NAME=2
DISAMB_NAME=3
ALIASES=4
DESCRIPTION=5
ROLES=6
FICTIONAL=7
WIKIPEDIA_URL=8
WIKIDATA_URL=9
DBPEDIA_URL=10
IMAGES=11

GENDER_LATITUDE=12
BIRTH_DATE_LONGITUDE = 13
BIRTH_PLACE_GEOTYPE = 14
DEATH_DATE_COUNTRY = 15
DEATH_PLACE_POPULATION = 16
NATIONALITIES = 17

WIKIDATA_ID = 18'''

ID = 0
TYPE = 1
NAME = 2
ALIASES = 3
REDIRECTS = 4
DESCRIPTION = 5
ORIGINAL_WIKINAME = 6
IMAGE = 7
WIKIPEDIA_LINK = 8
WIKIDATA_ID = 9

CONTINENT = 10
JOBS = 15
NATIONALITY = 16

GENERAL_ATTR_SIZE = WIKIDATA_ID + 1
WIKI_STATS_SIZE = 6

GEOGRAPHICAL_SUBCATEGORIES = [
    "country",
    "country:former",
    "settlement",
    "watercourse",
    "waterarea",
    "geo:relief",
    "geo:waterfall",
    "geo:island",
    "geo:peninsula",
    "geo:continent"
]

PERSON_SUBCATEGORIES = [
    "person",
    "person:fictional",
    "person:group"
]

TYPES = [
    "person",
    "person:fictional",
    "person:group",
    "country",
    "country:former",
    "settlement",
    "watercourse",
    "waterarea",
    "geo:relief",
    "geo:waterfall",
    "geo:island",
    "geo:peninsula",
    "geo:continent"
]


def load_head(file):
    '''Read entities from kb and return them in dict'''
    with open(file) as wd_to_read:
        rows = list(csv.reader(wd_to_read, delimiter="\t"))
    return rows


def load_kb(file):
    '''Read entities from kb and return them in dict'''
    wd_map = {}
    secondary_keys = {}
    wp_map = {}
    wp_map_all = {}
    with open(file) as kb_to_read:
        kb = list(csv.reader(kb_to_read, delimiter="\t"))
        if "VERSION" in kb[0][0]:
            kb = kb[8:]
        for wd_row in kb:
            if wd_row[WIKIPEDIA_LINK]:
                wp_map_all[wd_row[WIKIPEDIA_LINK]] = wd_row
            if wd_row[WIKIDATA_ID]:
                wd_map[wd_row[WIKIDATA_ID]] = wd_row
                secondary_keys[wd_row[WIKIDATA_ID]] = [wd_row[WIKIPEDIA_LINK]]
            else:
                wp_map[wd_row[WIKIPEDIA_LINK]] = wd_row
                secondary_keys[wd_row[WIKIPEDIA_LINK]] = [wd_row[WIKIPEDIA_LINK]]
    return wd_map, wp_map, wp_map_all, secondary_keys


class differences:
    def __init__(self, kb_new, kb_old):
        self.new_entities_cnt = 0
        self.added_attributes = dict()
        self.removed_attributes = dict()
        self.changed_attributes = dict()
        self.new_entities = []
        self.head = load_head(
            "/mnt/minerva1/nlp/projects/entity_kb_slovak3/entity_extraction/sk/HEAD-KB")

        [self.added_attributes.setdefault(x, [0]*20) for x in TYPES]
        [self.removed_attributes.setdefault(x, [0]*20) for x in TYPES]
        [self.changed_attributes.setdefault(x, [0]*20) for x in TYPES]

        new_wd_key_map, new_wp_key_map, _, secondary_keys = load_kb(kb_new)
        old_wd_key_map, old_wp_key_map, old_wp_key_map_all, _ = load_kb(kb_old)

        for new_key, new_row in (new_wd_key_map | new_wp_key_map).items():
            if (new_key not in old_wd_key_map) and (secondary_keys[new_key][0] not in old_wp_key_map_all):
                self.new_entities.append(new_row)
                self.new_entities_cnt += 1
            else:
                try:
                    old_row = old_wd_key_map[new_key]
                except:
                    try:
                        old_row = old_wp_key_map_all[secondary_keys[new_key][0]]
                    except:
                        # pass wd key, latter finds wp key
                        continue
                if old_row[TYPE] != new_row[TYPE]:
                    last_att_to_diff = WIKIDATA_ID
                else:
                    last_att_to_diff = len(new_row)
                for attr in range(1, last_att_to_diff):
                    if old_row[attr] != new_row[attr]:
                        if not old_row[attr]:
                            self.added_attributes[new_row[TYPE]][attr] += 1
                        elif not new_row[attr]:
                            self.removed_attributes[new_row[TYPE]][attr] += 1
                        elif attr in [ALIASES, REDIRECTS, IMAGE, JOBS, NATIONALITY, CONTINENT]:
                            new_diffs, old_diffs = diff_multiple(
                                new_row[attr], old_row[attr])
                            if new_diffs or old_diffs:
                                self.changed_attributes[new_row[TYPE]
                                                        ][attr] += 1
                        else:
                            self.changed_attributes[new_row[TYPE]][attr] += 1

    def write(self):
        print("NEW ENTITIES:", self.new_entities_cnt, "\n")

        aggr_general_attr_added = [0] * GENERAL_ATTR_SIZE
        aggr_general_attr_removed = [0] * GENERAL_ATTR_SIZE
        aggr_general_attr_changed = [0] * GENERAL_ATTR_SIZE
        for type_index in range(len(TYPES)):
            for attr_index in range(GENERAL_ATTR_SIZE):
                aggr_general_attr_added[attr_index] += self.added_attributes[TYPES[type_index]][attr_index]
                aggr_general_attr_removed[attr_index] += self.removed_attributes[TYPES[type_index]][attr_index]
                aggr_general_attr_changed[attr_index] += self.changed_attributes[TYPES[type_index]][attr_index]
        print("--------------------------------------------------------------")
        print("AGGREGATED GENERAL")
        print("\nAGGR ADDED ATTRIBUTES")
        for attr_index in range(1, GENERAL_ATTR_SIZE):
            print(self.head[type_index][attr_index], ":",
                  aggr_general_attr_added[attr_index])
        print("\nAGGR REMOVED ATTRIBUTES")
        for attr_index in range(1, GENERAL_ATTR_SIZE):
            print(self.head[type_index][attr_index], ":",
                  aggr_general_attr_removed[attr_index])
        print("\nAGGR CHANGED ATTRIBUTES")
        for attr_index in range(1, GENERAL_ATTR_SIZE):
            print(self.head[type_index][attr_index], ":",
                  aggr_general_attr_changed[attr_index])
        print("--------------------------------------------------------------")

        for type_index in range(len(TYPES)):
            print("--------------------------------------------------------------")
            print(TYPES[type_index])
            print("\nADDED ATTRIBUTES")
            for attr_index in range(GENERAL_ATTR_SIZE, len(self.head[type_index])-WIKI_STATS_SIZE):
                print(self.head[type_index][attr_index], ":",
                      self.added_attributes[TYPES[type_index]][attr_index])
            print("\nREMOVED ATTRIBUTES")
            for attr_index in range(GENERAL_ATTR_SIZE, len(self.head[type_index])-WIKI_STATS_SIZE):
                print(self.head[type_index][attr_index], ":",
                      self.removed_attributes[TYPES[type_index]][attr_index])
            print("\nCHANGED ATTRIBUTES")
            for attr_index in range(GENERAL_ATTR_SIZE, len(self.head[type_index])-WIKI_STATS_SIZE):
                print(self.head[type_index][attr_index], ":",
                      self.changed_attributes[TYPES[type_index]][attr_index])
            print("--------------------------------------------------------------")

        with open(NEW_ENTITIES_FILE, "w") as to_write:
            full_ent_diff = csv.writer(to_write, delimiter="\t")
            for ent in self.new_entities:
                full_ent_diff.writerow(ent)


def diff_multiple(new, old):
    new_splitted = new.split("|")
    new_splitted = list(new_splitted)
    old_splitted = old.split("|")
    old_splitted = list(old_splitted)
    new_diffs = []
    old_diffs = []
    for new_one in new_splitted:
        if new_one not in old_splitted:
            new_diffs.append(new_one)
    for old_one in old_splitted:
        if old_one not in new_splitted:
            old_diffs.append(new_one)
    return new_diffs, old_diffs


if __name__ == "__main__":
    differences(kb_old=sys.argv[1], kb_new=sys.argv[2]).write()
