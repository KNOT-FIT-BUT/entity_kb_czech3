##
# @mainpage Entity KB English index page
# see https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_english5 for more information...

##
# @file wiki_en_extract.py
# @brief main script that contains WikiExtract class that extracts and identifies entities
# 
# code is based on an earlier project with different language - entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
# @section how_it_works how it works
# - parses arguments
# - creates head and version
# - parses wikipedia xml dump
# - logs errors and statistics to a file
# @section parsing_xml_dump parsing the xml dump
# - loads the redirect, first sentence, identification patterns and langmap files
# - goes through the xml file and identifies entities
# - for each entity:
#   - extracts important data
#   - identifies the entity
#   - assigns a class to the entity
# - outputs extracted entities into a file
# 
# @author created by Jan Kapsa (xkapsa00)
# @date 14.07.2022

import re
import os
import xml.etree.cElementTree as CElTree
from itertools import repeat, tee
import argparse
import time
from multiprocessing import Pool
import json
import datetime
import sys

import mwparserfromhell as parser
from collections import Counter

from entities.ent_person import *
from entities.ent_country import *
from entities.ent_settlement import *
from entities.ent_waterarea import *
from entities.ent_watercourse import *
from entities.ent_geo import *
from entities.ent_organisation import *
from entities.ent_event import *

from debugger import Debugger

TESTING_PATH = "./testing_data/xml/people.xml"
LANG_MAP = {"cz": "cs"}

##
# @class WikiExtract
# @brief main class of the project, one istance is created to execute the main functions
class WikiExtract(object):
    ##
    # @brief initializes the console_args variable and debugger class
    def __init__(self):
        self.console_args = None
        self.d = Debugger()

        # self.first_sentence_version = "20210101"
        # self.first_sentences_path = f"/mnt/minerva1/nlp/corpora_datasets/monolingual/english/wikipedia/1st_sentences_from_enwiki-20210101-pages-articles.tsv"
        self.first_sentences_path = f"testing_data/xml/1st_sentences_from_enwiki-20210101-pages-articles.tsv"

    ##
    # @brief creates the HEAD-KB file
    # HEAD-KB file contains individual fields of each entity
    @staticmethod
    def create_head_kb():
        entities = [
            "<person>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<person:artist>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<person:fictional>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<person:group>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<country>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<country:former>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<settlement>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tCOUNTRY\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<watercourse>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tLENGTH\tAREA\tSTREAMFLOW\tSOURCE_LOC\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<waterarea>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tAREA\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<geo:relief>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<geo:waterfall>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tTOTAL HEIGHT\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<geo:island>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<geo:peninsula>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<geo:continent>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<organisation>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tFOUNDED\tCANCELLED\tORGANISATION_TYPE\tLOCATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<event>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tSTART\tEND\tLOCATION\tEVENT_TYPE\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n"
        ]

        with open("HEAD-KB", "w", encoding="utf-8") as file:
            for entity in entities:
                file.write(entity)

    ##
    # @brief parses the console arguments
    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-I",
            "--indir",
            default="/mnt/minerva1/nlp/corpora_datasets/monolingual/english/wikipedia/",
            type=str,
            help="Directory, where input files are located (applied for files withoud directory location only).",
        )
        parser.add_argument(
            "-l",
            "--lang",
            default="en",
            type=str,
            help="Language of processing also used for input files, when defined by version (by default) and not by files (default: %(default)s).",
        )
        parser.add_argument(
            "-d",
            "--dump",
            default="latest",
            type=str,
            help='Dump version to process (in format "yyyymmdd"; default: %(default)s).',
        )
        parser.add_argument(
            "-m",
            default=2,
            type=int,
            help="Number of processors of multiprocessing.Pool() for entity processing.",
        )
        parser.add_argument(
            "-g",
            "--geotags",
            action="store",
            type=str,
            help="Source file of wiki geo tags (with GPS locations) dump.",
        )
        parser.add_argument(
            "-p",
            "--pages",
            action="store",
            type=str,
            help="Source file of wiki pages dump.",
        )
        parser.add_argument(
            "-r",
            "--redirects",
            action="store",
            type=str,
            help="Source file of wiki redirects dump.",
        )
        parser.add_argument(
            "--dev",
            action="store_true",
            help="Development version of KB",
        )
        parser.add_argument(
            "--test",
            action="store_true",
            help="Test version of KB",
        )
        self.console_args = parser.parse_args()

        if self.console_args.m < 1:
            self.console_args.m = 1

        self.console_args.lang = self.console_args.lang.lower()
        if self.console_args.lang in LANG_MAP:
            self.console_args.lang = LANG_MAP[self.console_args.lang]

        self.pages_dump_fpath = self.get_dump_fpath(
            self.console_args.pages, "{}wiki-{}-pages-articles.xml"
        )
        self.geotags_dump_fpath = self.get_dump_fpath(
            self.console_args.geotags, "{}wiki-{}-geo_tags.sql"
        )
        self.redirects_dump_fpath = self.get_dump_fpath(
            self.console_args.redirects, "redirects_from_{}wiki-{}-pages-articles.tsv"
        )
        if self.console_args.dev:
            self.console_args._kb_stability = "dev"
        elif self.console_args.test:
            self.console_args._kb_stability = "test"
        else:
            self.console_args._kb_stability = ""

    ##
    # @brief gets arguments from a config file
    def get_config(self):

        try:    
            with open(os.path.join(os.path.dirname(sys.argv[0]), "kb.config"), "r") as file:
                lines = file.readlines()
                config = dict()
                for line in lines:
                    if line.startswith("="):
                        continue
                    if "=" in line:
                        key, value = line.split("=")
                        config[key.strip()] = value.strip()
                
                # fails if config file is not properly setup
                if config["USE_CONFIG"].strip() == "TRUE":
                    sys.argv = [
                        sys.argv[0], 
                        "-d", config["DUMP_NAME"],
                        "-I", config["DUMP_PATH"]
                    ]
        except:
            pass

    ##
    # @brief creates a path to the dump file
    # @param dump_file
    # @param dump_file_mask
    # @return string file path
    def get_dump_fpath(self, dump_file, dump_file_mask):
        if dump_file is None:
            dump_file = dump_file_mask.format(
                self.console_args.lang, self.console_args.dump
            )
        elif dump_file[0] == "/":
            return dump_file
        elif dump_file[0] == "." and (dump_file[1] == "/" or dump_file[1:3] == "./"):
            return os.path.join(os.getcwd(), dump_file)

        return os.path.join(self.console_args.indir, dump_file)

    ##
    # @brief creates the VERSION file
    def assign_version(self):
        str_kb_stability = ""
        if self.console_args._kb_stability:
            str_kb_stability = f"-{self.console_args._kb_stability}"
        try:
            target = os.readlink(self.pages_dump_fpath)
            matches = re.search(self.console_args.lang + r"wiki-([0-9]{8})-", target)
            if matches:
                dump_version = matches[1]
        except OSError:
            try:
                target = os.readlink(self.redirects_dump_fpath)
                matches = re.search(
                    self.console_args.lang + r"wiki-([0-9]{8})-", target
                )
                if matches:
                    dump_version = matches[1]
            except OSError:
                dump_version = self.console_args.dump
        with open("VERSION", "w") as f:
            f.write(
                "{}_{}-{}{}".format(
                    self.console_args.lang,
                    dump_version,
                    int(round(time.time())),
                    str_kb_stability,
                )
            )

    ## 
    # @brief loads redirects, first sentences, langmap and patterns, then parses xml dump
    def parse_xml_dump(self):
        # redirects
        redirects = dict()
        try:
            with open(self.redirects_dump_fpath, "r") as f:
                self.d.print("loading redirects")
                i = 0
                for line in f:
                    i += 1
                    self.d.update(i)
                    redirect_from, redirect_to = line.strip().split("\t")

                    if redirect_to not in redirects:
                        redirects[redirect_to] = [redirect_from]
                    else:
                        redirects[redirect_to].append(redirect_from)

                self.d.print(f"loaded redirects ({i})")
        except OSError:            
            self.d.print("redirect file was not found - skipping...")

        # first sentences
        first_sentences = dict()
        try:
            with open(self.first_sentences_path, "r") as f:
                self.d.print("loading first sentences")
                i = 0
                for line in f:
                    i += 1
                    self.d.update(i)
                    split = line.strip().split("\t")
                    link = split[0]
                    sentence = split[1] if len(split) > 1 else ""
                    first_sentences[link] = sentence

                self.d.print(f"loaded first sentences ({i})")
        except OSError:            
            self.d.print("first sentence file was not found - skipping...")

        # načtení langmapy
        langmap = dict()
        try:
            with open(os.path.join(os.path.dirname(sys.argv[0]), "json/langmap.json"), "r") as file:
                self.d.print("loading langmap")
                langmap = json.load(file)
                self.d.print("loaded langmap")
        except OSError:
            self.d.print(f"langmap file 'langmap.json' was not found")
            self.d.print(f"please generate langmap.json (use generate_langmap.json)")
            exit(1)

        # patterns for entity recognition
        patterns = dict()
        try:
            with open(os.path.join(os.path.dirname(sys.argv[0]), "json/identification.json"), "r") as file:
                patterns = json.load(file)
        except OSError:
            self.d.print("entity identification patterns were not found - exiting...")
            exit(1)

        # xml parser
        context = CElTree.iterparse(self.pages_dump_fpath, events=("start", "end"))

        ent_titles = []
        ent_pages = []
        ent_redirects = []
        ent_sentences = []
        
        curr_page_cnt = 0
        all_page_cnt = 0
        ent_count = 0

        # LIMIT = skript bude číst a extrahovat data po blocích o velikosti [LIMIT]
        LIMIT = 4000
        debug_limit_hit = False

        with open("kb", "a+", encoding="utf-8") as file:
            file.truncate(0)
            event, root = next(context)
            for event, elem in context:

                if debug_limit_hit:
                    break

                # hledá <page> element
                if event == "end" and "page" in elem.tag:
                    # xml -> <page> -> <title>
                    # xml -> <page> -> <revision>
                    is_entity = False
                    title = ""

                    for child in elem:
                        # získá title stránky
                        if "title" in child.tag:
                            is_entity = self.is_entity(child.text.lower())
                            if is_entity:
                                title = child.text
                        # získá text stránky
                        elif "revision" in child.tag:
                            for grandchild in child:
                                if "text" in grandchild.tag:
                                    if is_entity and grandchild.text:
                                        if re.search(r"{{[^}]*?(?:disambiguation|disambig|dab)(?:\|[^}]*?)?}}", grandchild.text, re.I):
                                            self.d.update("found disambiguation")
                                            break                    

                                        # nalezení nové entity
                                        ent_titles.append(title)
                                        ent_pages.append(grandchild.text)
                                        link = self.get_link(title)
                                        ent_redirects.append(redirects[link] if link in redirects else [])
                                        ent_sentences.append(first_sentences[link] if link in first_sentences else "")

                                        curr_page_cnt += 1
                                        all_page_cnt += 1

                                        self.d.update(f"found new page ({all_page_cnt})")

                                        if self.d.debug_limit is not None and all_page_cnt >= self.d.debug_limit:
                                            self.d.print(f"debug limit hit (number of pages: {all_page_cnt})")
                                            debug_limit_hit = True
                                            break

                                        if curr_page_cnt == LIMIT:
                                            ent_count += self.output(file, ent_titles, ent_pages, langmap, ent_redirects, ent_sentences, patterns)
                                            ent_titles.clear()
                                            ent_pages.clear()
                                            ent_redirects.clear()
                                            ent_sentences.clear()
                                            curr_page_cnt = 0    
                        elif "redirect" in child.tag:
                            self.d.update(f"found redirect ({all_page_cnt})")
                            break

                    root.clear()

            if len(ent_titles):
                ent_count += self.output(file, ent_titles, ent_pages, langmap, ent_redirects, ent_sentences, patterns)

        self.d.print("----------------------------", print_time=False)
        self.d.print(f"parsed xml dump (number of pages: {all_page_cnt})", print_time=False)
        self.d.print(f"processed {ent_count} entities", print_time=False)

    ##
    # @brief extracts the entities with multiprocessing and outputs the data to a file
    # @param file - output file ("kb" file)
    # @param ent_titles - ordered array of strings containing entity titles
    # @param ent_pages - ordered array of strings containing entity pages
    # @param langmap - dictionary of language abbreviations
    # @param ent_redirects - ordered array of arrays of strings containing entity redirects
    # @param ent_sentences - ordered array of strings containing entity sentences
    # @param patterns - dictionary containing identification patterns
    # @return number of pages that were identified as entities (count of extracted entities)
    def output(self, file, ent_titles, ent_pages, langmap, ent_redirects, ent_sentences, patterns):
        if len(ent_titles):
            start_time = datetime.datetime.now()

            pool = Pool(processes=self.console_args.m)
            serialized_entities = pool.starmap(
                self.process_entity,
                zip(ent_titles, ent_pages, repeat(langmap), ent_redirects, ent_sentences, repeat(patterns))                    
            )
            l = list(filter(None, serialized_entities))
            file.write("\n".join(l) + "\n")
            pool.close()
            pool.join()
            count = len(l)

            end_time = datetime.datetime.now()
            tdelta = end_time - start_time
            self.d.print(f"processed {count} entities (in {self.d.pretty_time_delta(tdelta.total_seconds())})")
            self.d.log_message(f"time_avg,{tdelta},{len(ent_pages)};")
            return count

    ##
    # @brief determines if page is an entity or not
    #  
    # filters out wikipedia special pages and date pages
    @staticmethod
    def is_entity(title):
        # special pages
        if title.startswith(
            (
                "wikipedia:",
                "file",
                "mediawiki:",
                "template:",
                "help:",
                "category:",
                "special:",
                "portal:",
                "module:",
                "draft:",
                "user:",
                "list of",
                "geography of",
                "history of",
                "economy of",
                "politics of",
                "culture of",
                "bibliography of",
                "outline of",
                "music of",
                "flag of",
                "index of",
                "timeline of"
            )
        ):
            return False

        if re.search(r"(?:january|february|march|april|may|june|july|august|september|october|november|december)(?:\s[0-9]+)?", title, re.I):
            return False

        return True

    ##
    # @brief extracts entity data, identifies the type of the entity and assigns a class
    # @param page_title - string containing the page title
    # @param page_content - string containing the page content
    # @param langmap - dictionary of language abbreviations
    # @param ent_redirects - array of string containing the redirects
    # @param ent_sentence - string containing the first sentence
    # @param patterns - dictionary containing identification patterns
    # @return tab separated string with entity data or None if entity is unidentified
    def process_entity(self, page_title, page_content, langmap, ent_redirects, ent_sentence, patterns):
        self.d.update(f"processing {page_title}")

        # if ent_sentence != "":
        #     self.d.log_message(f"sentence: {ent_sentence}")            
        
        extracted = self.extract_entity_data(page_content)

        identification = self.identify_entity(page_title, extracted, patterns).most_common()

        count = 0
        for _, value in identification:
            count += value

        if count != 0:
            self.d.log_message(f"id_stats,{identification[0][0]},{identification[0][1]};")

        entities = {
            "person":       EntPerson,
            "country":      EntCountry,
            "settlement":   EntSettlement,
            "waterarea":    EntWaterArea,
            "watercourse":  EntWaterCourse,
            "geo":          EntGeo,
            "organisation": EntOrganisation,
            "event":        EntEvent
        }

        if count != 0:
            key = identification[0][0]
            if key in entities:
                entity = entities[key](page_title, key, self.get_link(page_title), extracted, langmap, ent_redirects, ent_sentence, self.d)
                entity.assign_values()
                return repr(entity)

        # TODO: log unidentified
        return None

    ##
    # @brief tries to extract infobox, first paragraph, categories and coordinates
    # @param content - string containing page content 
    # @return dictionary of extracted entity data
    #
    # uses the mwparserfromhell library
    def extract_entity_data(self, content):
        content = self.remove_not_improtant(content)

        result = {
            "found": False,
            "name": "",
            "data": dict(),
            "paragraph": "",
            "categories": [],
            "coords": ""
        }

        wikicode = parser.parse(content)
        templates = wikicode.filter_templates()

        infobox = None

        # look for infobox
        for t in templates:
            name = t.name.lower().strip()
            if name.startswith("infobox") and infobox is None:
                infobox = t
                name = name.split()
                name.pop(0)
                name = " ".join(name)
                result["found"] = True
                result["name"] = name
            elif "coord" in name or "coords" in name:
                result["coords"] = str(t)

        # extract infobox
        if result["found"]:
            for p in infobox.params:
                field = p.strip()
                field = [item.strip() for item in field.split("=")]
                key = field.pop(0).lower()
                value = "=".join(field)
                result["data"][key] = value

        # extract first paragraph
        sections = wikicode.get_sections()
        if len(sections):
            section = sections[0]
            templates = section.filter_templates()
            
            for t in templates:
                if t.name.lower().startswith("infobox"):
                    section.remove(t)
                    break
            
            split = [s for s in section.strip().split("\n") if s != ""]
            for s in split:
                if s.startswith("'''") or s.startswith("The '''"):
                    result["paragraph"] = s.strip()
                    break

        # extract categories
        lines = content.splitlines()
        for line in lines:
            if line.startswith("[[Category:"):
                result["categories"].append(line[11:-2].strip())
        
        return result

    ##
    # @brief uses patterns to score the entity, prefix with the highest score is later chosen as the entity identification
    # @param title - string containing page title 
    # @param extracted - dictionary with extracted entity data (infobox, categories, ...)
    # @param patterns - dictionary containing identification patterns
    # @return Counter instance with identification scores
    #
    # entity is given a point for each matched pattern
    # it looks at categories, infobox names, titles and infobox fields
    # these patterns are located in a en/json/identification.json file
    #
    # @todo better algorithm for faster performance
    # @todo score weight system
    @staticmethod
    def identify_entity(title, extracted, patterns):
        counter = Counter({key: 0 for key in patterns.keys()})

        # categories
        for c in extracted["categories"]:
            for entity in patterns.keys():
                for p in patterns[entity]["categories"]:
                    if re.search(p, c, re.I):
                        # print("matched category")
                        counter[entity] += 1

        # infobox names
        for entity in patterns.keys():
            for p in patterns[entity]["names"]:
                if re.search(p, extracted["name"], re.I):
                    # print("matched name")
                    counter[entity] += 1

        # titles
        for entity in patterns.keys():
            for p in patterns[entity]["titles"]:
                if re.search(p, title, re.I):
                    # print("matched title")
                    counter[entity] += 1

        # infobox fields
        for entity in patterns.keys():
            for field in patterns[entity]["fields"]:
                if field in extracted["data"]:
                    # print("matched field")
                    counter[entity] += 1

        return counter

    ##
    # @brief creates a wikipedia link given the page name
    # @param page - string containing page title
    # @return wikipedia link
    @staticmethod
    def get_link(page):
        wiki_link = page.replace(" ", "_")
        return f"https://en.wikipedia.org/wiki/{wiki_link}"

    ##
    # @brief deletes references, comments, etc. from a page content
    # @param page_content - string containing page_content
    # @return page content withou reference tags, comments, etc...
    def remove_not_improtant(self, page_content):
        clean_content = page_content

        # remove comments
        clean_content = re.sub(r"<!--.*?-->", "", clean_content, flags=re.DOTALL)

        # remove references        
        clean_content = re.sub(r"<ref.*?/(?:ref)?>", "", clean_content, flags=re.DOTALL)

        # remove {{efn ... }} and {{refn ...}}
        clean_content = self.remove_references(clean_content, r"{{efn")
        clean_content = self.remove_references(clean_content, r"{{refn")
        
        # remove break lines
        clean_content = re.sub(r"<br />", " ", clean_content, flags=re.DOTALL)
        clean_content = re.sub(r"<.*?/?>", "", clean_content, flags=re.DOTALL)

        return clean_content

    ##
    # @brief removes a specific references from a string
    # @param string - input string
    # @param ref_pattern - specific reference pattern
    # @return string without the references
    @staticmethod
    def remove_references(string, ref_pattern):
        clean_content = string
        arr = []
        for m in re.finditer(ref_pattern, clean_content):
            index = m.start()+1
            indentation = 1            
            while indentation != 0 and index != len(clean_content):
                if clean_content[index] == "{":
                    indentation += 1
                elif clean_content[index] == "}":
                    indentation -= 1
                index += 1
            arr.append((m.start(), index))
        arr = sorted(arr, reverse=True)
        for i in arr:
            clean_content = clean_content[:i[0]] + clean_content[i[1]:]
        return clean_content

if __name__ == "__main__":
    wiki_extract = WikiExtract()
    
    wiki_extract.get_config()
    wiki_extract.parse_args()
    wiki_extract.create_head_kb()
    wiki_extract.assign_version()
    
    wiki_extract.parse_xml_dump()

    wiki_extract.d.log()