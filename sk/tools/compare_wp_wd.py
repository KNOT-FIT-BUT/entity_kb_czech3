#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_slovak3 (https://knot.fit.vutbr.cz/wiki/index.php/entity_kb_slovak3)
Autor: Samuel Križan (xkriza06)
Popis suboru:
Subor je urceny na porovnanie kb z wikipedie s kb z wikidat
"""

import csv
import re
from re import split
import requests
import copy
import sys


NEW_ENTITIES_FILE = "new_entities.tsv"


ID = 0
TYPE = 1
NAME = 2
DISAMB_NAME = 3
ALIASES = 4
DESCRIPTION = 5
ROLES = 6
FICTIONAL = 7
WIKIPEDIA_URL = 8
WIKIDATA_URL = 9
DBPEDIA_URL = 10
IMAGES = 11

NATIONALITY = 17

GENERAL_ATTR_SIZE = IMAGES + 1
WIKI_STATS_SIZE = 6


TYPES = [
    "person",
    "group",
    "artist",
    "geographical"
]

wd_files = [
    "artist",
    "event",
    "group",
    "location",
    "organization",
    "person",
    "general"
]

wd_path_common = "/mnt/minerva1/nlp/projects/wikidata2/tsv_extracted_from_wikidata/wikidata-20211004-all.json/wikidata-20211004"


def merge_wikidata(kb_wd):
    '''Filter out entities from wikidata kb that are not found in wikipedia kb and write it to 'filtered_file' '''
    wp_full = dict()
    wd_full = dict()
    wp_all_full = dict()
    for wd_file in wd_files:
        wd, wp, wp_all, _ = load_kb(kb_wd+"-sk-"+wd_file+".tsv")
        wp_full.update(wp)
        wd_full.update(wd)
        wp_all_full.update(wp_all)
    return wd_full, wp_full, wp_all_full


def load_head(file):
    '''Read header'''
    with open(file) as wd_to_read:
        rows = list(csv.reader(wd_to_read, delimiter="\t"))
        head_raw = rows[1:6]
        head = []
    for row_index in range(len(TYPES)):
        head.append(copy.deepcopy(head_raw[0]))
        head[row_index].extend(head_raw[row_index+1])
    return head


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
            if wd_row[WIKIPEDIA_URL]:
                wp_map_all[wd_row[WIKIPEDIA_URL]] = wd_row
            if wd_row[WIKIDATA_URL]:
                wd_map[wd_row[WIKIDATA_URL]] = wd_row
                secondary_keys[wd_row[WIKIDATA_URL]] = [wd_row[WIKIPEDIA_URL]]
            else:
                wp_map[wd_row[WIKIPEDIA_URL]] = wd_row
                secondary_keys[wd_row[WIKIPEDIA_URL]] = [wd_row[WIKIPEDIA_URL]]
    return wd_map, wp_map, wp_map_all, secondary_keys


class differences:
    '''Class to compare two KBs'''
    def __init__(self, kb_wp, kb_wd):
        self.new_entities_cnt = 0
        self.added_attributes = dict()
        self.removed_attributes = dict()
        self.changed_attributes = dict()
        self.generalized = dict()
        self.all_entities = dict()
        self.compared_cnt = 0
        self.new_entities = []

        self.aliases_wp_win = 0
        self.aliases_wd_win = 0
        self.aliases_draw = 0

        self.head = load_head(kb_wp)

        [self.added_attributes.setdefault(x, [0]*25) for x in TYPES]
        [self.removed_attributes.setdefault(x, [0]*25) for x in TYPES]
        [self.changed_attributes.setdefault(x, [0]*25) for x in TYPES]
        [self.generalized.setdefault(x, 0) for x in TYPES]
        [self.all_entities.setdefault(x, 0) for x in TYPES]

        wikipedia_wd_key_map, wikipedia_wp_key_map,  _, secondary_keys  = load_kb(kb_wp)
        wikidata_wd_key_map, wikidata_wp_key_map, wikidata_wp_key_map_all= merge_wikidata(kb_wd)
        
        for wikipedia_key, wikipedia_row in (wikipedia_wd_key_map | wikipedia_wp_key_map).items():
            if wikipedia_row[WIKIDATA_URL] not in wikidata_wd_key_map and (secondary_keys[wikipedia_key][0] not in wikidata_wp_key_map_all):
                self.new_entities.append(wikipedia_row)
                self.new_entities_cnt += 1
            else:
                try:
                    wikidata_row = wikidata_wd_key_map[wikipedia_key]
                except:
                    wikidata_row = wikidata_wp_key_map_all[secondary_keys[wikipedia_key][0]]
                self.compared_cnt += 1
                if wikidata_row[TYPE] == wikipedia_row[TYPE] or (wikidata_row[TYPE] == "location" and wikipedia_row[TYPE] == "geographical"):
                    last_att_to_diff = len(wikipedia_row) - WIKI_STATS_SIZE
                else:
                    last_att_to_diff = GENERAL_ATTR_SIZE
                for attr in range(1, last_att_to_diff):

                    if attr == TYPE and wikidata_row[TYPE] != "general":
                            self.all_entities[wikipedia_row[TYPE]] += 1

                    if wikidata_row[attr] != wikipedia_row[attr]:
                        if attr == TYPE and wikidata_row[TYPE] == "general":
                            self.generalized[wikipedia_row[TYPE]] += 1

                        elif attr == TYPE and wikidata_row[TYPE] == "location" and wikipedia_row[TYPE] == "geographical":
                            continue

                        elif not wikidata_row[attr]:
                            self.added_attributes[wikipedia_row[TYPE]
                                                  ][attr] += 1
                            if attr == ALIASES:
                                self.aliases_wp_win += 1

                        elif not wikipedia_row[attr]:
                            self.removed_attributes[wikipedia_row[TYPE]
                                                    ][attr] += 1
                            if attr == ALIASES:
                                self.aliases_wd_win += 1

                        elif attr == ALIASES:
                            is_differ = self.diff_aliases(
                                wikipedia_row[attr], wikidata_row[attr])
                            if is_differ:
                                self.changed_attributes[wikipedia_row[TYPE]
                                                        ][attr] += 1

                        elif attr in [IMAGES, ROLES, NATIONALITY]:
                            wp_diff_items, wd_diff_items = diff_multiple(
                                wikipedia_row[attr], wikidata_row[attr])
                            if wp_diff_items or wd_diff_items:
                                self.changed_attributes[wikipedia_row[TYPE]
                                                        ][attr] += 1

                        else:
                            self.changed_attributes[wikipedia_row[TYPE]
                                                    ][attr] += 1

    def write(self):
        '''Print stats to stdout'''
        print("NEW ENTITIES:", self.new_entities_cnt, "\n")

        aggr_general_attr_added = [0] * GENERAL_ATTR_SIZE
        aggr_general_attr_removed = [0] * GENERAL_ATTR_SIZE
        aggr_general_attr_changed = [0] * GENERAL_ATTR_SIZE
        aggr_generalized = 0
        for type_index in range(len(TYPES)):
            aggr_generalized += self.generalized[TYPES[type_index]]
            for attr_index in range(GENERAL_ATTR_SIZE):
                aggr_general_attr_added[attr_index] += self.added_attributes[TYPES[type_index]][attr_index]
                aggr_general_attr_removed[attr_index] += self.removed_attributes[TYPES[type_index]][attr_index]
                aggr_general_attr_changed[attr_index] += self.changed_attributes[TYPES[type_index]][attr_index]
        print("--------------------------------------------------------------")
        print("AGGREGATED GENERAL")
        print("ALL COMPARED ENTITIES:", self.compared_cnt, "\n")
        print("GENERALIZED ENTITIES:", aggr_generalized, "\n")
        print("\nAGGR MORE ATTRIBUTES")
        for attr_index in range(1, GENERAL_ATTR_SIZE):
            print(self.head[type_index][attr_index], ":",
                  aggr_general_attr_added[attr_index])
        print("\nAGGR LESS ATTRIBUTES")
        for attr_index in range(1, GENERAL_ATTR_SIZE):
            print(self.head[type_index][attr_index], ":",
                  aggr_general_attr_removed[attr_index])
        print("\nAGGR DIFFERENT ATTRIBUTES")
        for attr_index in range(1, GENERAL_ATTR_SIZE):
            print(self.head[type_index][attr_index], ":",
                  aggr_general_attr_changed[attr_index])
        print("--------------------------------------------------------------")
        print("\nALIASES")
        print("wikipedia win:", self.aliases_wp_win)
        print("wikidata win:", self.aliases_wd_win)
        print("draw:", self.aliases_draw)
        print("--------------------------------------------------------------")
        for type_index in range(len(TYPES)):
            print("--------------------------------------------------------------")
            print(TYPES[type_index], self.all_entities[TYPES[type_index]])
            print("\nMORE ATTRIBUTES")
            for attr_index in range(GENERAL_ATTR_SIZE, len(self.head[type_index])):
                print(self.head[type_index][attr_index], ":",
                      self.added_attributes[TYPES[type_index]][attr_index])
            print("\nLESS ATTRIBUTES")
            for attr_index in range(GENERAL_ATTR_SIZE, len(self.head[type_index])):
                print(self.head[type_index][attr_index], ":",
                      self.removed_attributes[TYPES[type_index]][attr_index])
            print("\nDIFFERENT ATTRIBUTES")
            for attr_index in range(GENERAL_ATTR_SIZE, len(self.head[type_index])):
                print(self.head[type_index][attr_index], ":",
                      self.changed_attributes[TYPES[type_index]][attr_index])
            print("--------------------------------------------------------------")

        with open(NEW_ENTITIES_FILE, "w") as to_write:
            full_ent_diff = csv.writer(to_write, delimiter="\t")
            for ent in self.new_entities:
                full_ent_diff.writerow(ent)

    def diff_aliases(self, wp_ent, wd_ent):
        '''Compare aliases'''
        diff = False
        wikipedia_aliases_no_lang = re.sub(r"#lang=([^|]*)", "", wp_ent)
        wp_aliases = wikipedia_aliases_no_lang.split("|")
        wd_aliases = wd_ent.split("|")

        for kb_alias in wp_aliases[:]:
            for wd_alias in wd_aliases[:]:
                if kb_alias == wd_alias:
                    wp_aliases.remove(kb_alias)
                    wd_aliases.remove(wd_alias)

        if len(wd_aliases) + len(wp_aliases) > 0:
            diff = True
            if len(wd_aliases) > len(wp_aliases):
                self.aliases_wd_win += 1
            elif len(wd_aliases) < len(wp_aliases):
                self.aliases_wp_win += 1
            else:
                self.aliases_draw += 1
        return diff


def diff_multiple(wp_ent, wd_ent):
    '''Compare multivalue attributes'''
    wp_splitted = wp_ent.split("|")
    wp_splitted = list(wp_splitted)
    wd_splitted = wd_ent.split("|")
    wd_splitted = list(wd_splitted)
    wp_diff_items = []
    wd_diff_items = []
    for new_one in wp_splitted:
        if new_one not in wd_splitted:
            wp_diff_items.append(new_one)
    for old_one in wd_splitted:
        if old_one not in wp_splitted:
            wd_diff_items.append(new_one)
    return wp_diff_items, wd_diff_items


if __name__ == "__main__":
    differences(kb_wp=sys.argv[1], kb_wd=sys.argv[2]).write()
