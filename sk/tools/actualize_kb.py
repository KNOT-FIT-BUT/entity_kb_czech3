#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_slovak3 (https://knot.fit.vutbr.cz/wiki/index.php/entity_kb_slovak3)
Autor: Samuel Križan (xkriza06)
Popis suboru:
Subor je urceny na aktualizaciu kb z wikipedie
"""

import csv
import re
from re import split
import requests
import copy
import sys
from hashlib import sha224


NEW_ENTITIES_FILE = "added_entities.tsv"

WIKIPEDIA_URL = 8
WIKIDATA_URL = 9


def load_kb(file):
    '''Read entities from kb and return them in dict'''
    wd_map = {}
    secondary_keys = {}
    wp_map = {}
    wp_map_all = {}

    entity_count=0

    with open(file) as kb_to_read:
        kb = list(csv.reader(kb_to_read, delimiter="\t"))
        
        if "VERSION" in kb[0][0]:
            kb = kb[8:]
        entity_count = len(kb)
        for row in kb:
            if row[WIKIPEDIA_URL]:
                wp_map_all[row[WIKIPEDIA_URL]] = row
            if row[WIKIDATA_URL]:
                wd_map[row[WIKIDATA_URL]] = row
                secondary_keys[row[WIKIDATA_URL]] = [row[WIKIPEDIA_URL]]
            else:
                wp_map[row[WIKIPEDIA_URL]] = row
                secondary_keys[row[WIKIPEDIA_URL]] = [row[WIKIPEDIA_URL]]
    return wd_map, wp_map, wp_map_all, secondary_keys, entity_count


class Actualize:
    '''Class to actualize kb'''
    def __init__(self, kb_new, kb_old):
        self.new_entities = []
        self.new_kb=kb_new
        self.entity_count = 0
        
        new_wd_key_map, new_wp_key_map, new_wp_key_map_all, _, self.entity_count = load_kb(kb_new)
        old_wd_key_map, old_wp_key_map, _, secondary_keys, _ = load_kb(kb_old)

        for old_key, old_row in (old_wd_key_map | old_wp_key_map).items():
            if (old_key not in new_wd_key_map) and (secondary_keys[old_key][0] not in new_wp_key_map_all):
                self.new_entities.append(old_row)

    def write(self):
         with open(self.new_kb, "a") as to_write:
            write_to_kb = csv.writer(to_write, delimiter="\t")
            for ent in self.new_entities:
                self.entity_count += 1
                ent[0] = sha224(str(self.entity_count).encode("utf-8")).hexdigest()[:10]
                write_to_kb.writerow(ent)
                print(ent)


if __name__ == "__main__":
    Actualize(kb_new=sys.argv[1], kb_old=sys.argv[2]).write()
