#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autoři:
    Michal Planička (xplani02)
    Tomáš Volf (ivolf)

Popis souboru:
Soubor obsahuje třídu 'WikiExtract', jež uchovává metody pro parsování argumentů příkazové řádky, parsování XML dumpu Wikipedie, vytvoření znalostní báze a hlavičkového souboru a správu entit a jejich údajů.

Poznámky:
[\-–—−]
[^\W\d_] - pouze písmena
"""

import json
import os
import sys
import argparse
import datetime
import time
import xml.etree.cElementTree as CElTree

from multiprocessing import Pool
from itertools import repeat, tee

from ent_person import *
from ent_country import *
from ent_settlement import *
from ent_watercourse import *
from ent_waterarea import *
from ent_geo import *


LANG_MAP = {"cz": "cs"}
WIKI_LANG_FILE = "languages.json"
LANG_TRANSFORMATIONS = {
    "aština": "ašsky",
    "ština": "sky",
    "čtina": "cky",
    "atina": "atinsky",
    "o": "u",
}


class WikiExtract(object):
    """
    Hlavní třída uchovávající metody pro parsování argumentů příkazové řádky, parsování XML dumpu Wikipedie, vytvoření znalostní báze a hlavičkového souboru a správu entit a jejich údajů.

    Instanční atributy:
    console_args - jmenný prostor s argumenty zadanými v konzoli (Namespace)
    entities - seznam entit, u nichž mají být získány údaje; prozatím nevyužito (dict)

    Metody:
    create_head_kb() - vytváří hlavičkový soubor HEAD-KB
    del_knowledge_base(kb_name) - odstraní zadanou znalostní bázi
    parse_args() - parsuje argumenty zadané při spuštění skriptu
    parse_xml_dump() - parsuje XML dump Wikipedie, prochází jednotlivé stránky a vyhledává entity

    _get_url(title) - vygeneruje URL stránky
    _is_entity(title) - z názvu stránky určuje, zda stránka pojednává o entitě, či nikoliv
    _load_entities() - načte entity ze složky, jež byla zadána jako argument při spuštění skriptu; prozatím nevyužito
    """

    def __init__(self):
        """
        Inicializuje třídu 'WikiExtract'.
        """
        self.console_args = None
        # self.entities = dict()

    @staticmethod
    def create_head_kb():
        """
        Vytváří hlavičkový soubor HEAD-KB, který upřesňuje množinu záznamů znalostní báze.
        """
        entities = [
            "<person>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
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
            # <organisation>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tFOUNDED\tCANCELLED\tORGANIZATION TYPE\tLOCATION\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            # "<event>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tSTART\tEND\tLOCATION\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n"
        ]

        with open("HEAD-KB", "w", encoding="utf-8") as fl:
            for entity in entities:
                fl.write(entity)

    @staticmethod
    def del_knowledge_base(kb_name):
        """
        Odstraní zadanou znalostní bázi před začátkem extrakce, pokud existuje.

        Parametry:
        kb_name - název znalostní báze, která má být odstraněna (str)
        """
        try:
            os.remove(kb_name)
        except OSError:
            pass

    @staticmethod
    def _get_url(title):
        """
        Vygeneruje  URL stránky.

        Parametry:
        title - původní název stránky (str)

        Návratové hodnoty:
        str obsahující URL stránky.
        """
        wiki_url = "https://cs.wikipedia.org/wiki/" + title.replace(" ", "_")

        return wiki_url

    @staticmethod
    def _is_entity(title):
        """
        Na základě názvu stránky určuje, zda stránka pojednává o entitě, či nikoliv.

        Parametry:
        title - název stránky (str)

        Návratové hodnoty:
        True, pokud stránka pojednává o entitě, jinak False. (bool)
        """
        # speciální stránky Wikipedie nepojednávají o entitách
        if title.startswith(
            (
                "Wikipedie:",
                "Redaktor:",
                "Soubor:",
                "MediaWiki:",
                "Šablona:",
                "Pomoc:",
                "Kategorie:",
                "Speciální:",
                "Portál:",
                "Modul:",
                "Seznam",
                "Geografie",
                "Společenstvo",
            )
        ):
            return False

        # stránky pro data (datumy) nepojednávají o entitách
        if re.search(r"^\d{1,2}\. [^\W\d_]+$", title):
            return False

        # ostatní stránky mohou pojednávat o entitách
        return True

    # def _load_entities(self):
    #     """
    #     Načte entity ze složky, jež byla zadána jako argument při spuštění skriptu.
    #     """
    #     try:
    #         with open(self.console_args.dir + "people/wp_list") as fl:
    #             self.entities["people"] = fl.read().splitlines()
    #
    #         with open(self.console_args.dir + "countries/wp_list") as fl:
    #             self.entities["countries"] = fl.read().splitlines()
    #
    #         with open(self.console_args.dir + "settlements/wp_list") as fl:
    #             self.entities["settlements"] = fl.read().splitlines()
    #
    #         with open(self.console_args.dir + "watercourses/wp_list") as fl:
    #             self.entities["watercourses"] = fl.read().splitlines()
    #
    #         with open(self.console_args.dir + "waterareas/wp_list") as fl:
    #             self.entities["waterareas"] = fl.read().splitlines()
    #
    #         with open(self.console_args.dir + "geos/wp_list") as fl:
    #             self.entities["geos"] = fl.read().splitlines()
    #     except FileNotFoundError:
    #         print("[[ CHYBA ]] Zadaná složka s entitami je neplatná nebo některé soubory v ní neexistují")
    #         exit(1)

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

    def parse_args(self):
        """
        Parsuje argumenty zadané při spuštění skriptu.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-I",
            "--indir",
            default="/mnt/minerva1/nlp/corpora_datasets/monolingual/czech/wikipedia/",
            type=str,
            help="Directory, where input files are located (applied for files withoud directory location only).",
        )
        parser.add_argument(
            "-l",
            "--lang",
            default="cs",
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
            self.console_args.redirects, "redirects_from_{}wiki-{}-pages-articles.xml"
        )
        if self.console_args.dev:
            self.console_args._kb_stability = "dev"
        elif self.console_args.test:
            self.console_args._kb_stability = "test"
        else:
            self.console_args._kb_stability = ""

    def parse_xml_dump(self):
        """
        Parsuje XML dump Wikipedie, prochází jednotlivé stránky a vyhledává entity.

        Poznámky:
        - založeno na: http://effbot.org/zone/element-iterparse.htm
        """
        # # načtení entit
        # self._load_entities()

        redirects = dict()
        try:
            with open(self.redirects_dump_fpath, "r") as f:
                for line in f:
                    redirect_from, redirect_to = line.strip().split("\t")
                    if not redirect_to in redirects:
                        redirects[redirect_to] = set()
                    redirects[redirect_to].add(redirect_from)
        except OSError:
            print(f'File "{self.redirects_dump_fpath}" was not found - skipping...')

        langmap = dict()
        try:
            with open(WIKI_LANG_FILE, "r", encoding="utf8") as f:
                try:
                    langmap = json.load(f)
                except (ValueError, UnicodeDecodeError):
                    pass  # File is not valid -> we generate new one
        except OSError:
            pass  # Do nothing - it does not matter, because in this case we generate new one

        # parsování XML souboru
        context = CElTree.iterparse(self.pages_dump_fpath, events=("start", "end"))

        it_context_langmap, it_context_pages = tee(context)
        event, root = next(it_context_langmap)

        if len(langmap) == 0:
            pg_languages = None
            found_639_2 = False
            for event, elem in it_context_langmap:
                if event == "end" and "page" in elem.tag:
                    for child in elem:
                        if (
                            "title" in child.tag
                            and child.text == "Seznam kódů ISO 639-2"
                        ):
                            found_639_2 = True
                        if found_639_2 and "revision" in child.tag:
                            for grandchild in child:
                                if "text" in grandchild.tag:
                                    pg_languages = grandchild.text
                                    break
                            break
                    if found_639_2:
                        break
            if found_639_2:
                tbl_languages = re.search(r"{\|(.*?)\|}", pg_languages, flags=re.S)
                if tbl_languages:
                    tbl_languages = tbl_languages.group(1)
                    tbl_lang_header = re.search(
                        r"^\s*!([^!]+(?:!![^!]+)+)$", tbl_languages, flags=re.M
                    )
                    if tbl_lang_header:
                        tbl_lang_header = tbl_lang_header.group(1).split("!!")
                        i_639_1 = tbl_lang_header.index("ISO 639-1")
                        i_639_2 = tbl_lang_header.index("ISO 639-2")
                        i_langname = tbl_lang_header.index("Název jazyka")

                        for lang_row in re.findall(
                            r"^\s*\|(.+?(?:\|\|.+?)+)$", tbl_languages, flags=re.M
                        ):
                            i_lang_col = None
                            lang_cols = lang_row.split("||")
                            langnames = re.sub(r"\(.*?\)", "", lang_cols[i_langname])
                            if (
                                lang_cols[i_639_1].strip()
                                and lang_cols[i_639_1].strip() != "&nbsp;"
                            ):
                                i_lang_col = i_639_1
                            else:
                                i_lang_col = i_639_2

                            for langnames2 in langnames.split(","):
                                for langname in langnames2.split(" a "):
                                    langname_normalized = None
                                    langname = (
                                        re.sub(r"\[\[(.*?)\]\]", r"\1", langname)
                                        .strip()
                                        .lower()
                                    )
                                    if not langname:
                                        continue
                                    for langname in langname.split("|"):
                                        for (
                                            suffix,
                                            replacement,
                                        ) in LANG_TRANSFORMATIONS.items():
                                            if langname.endswith(suffix):
                                                langname_normalized = (
                                                    langname[: -len(suffix)]
                                                    + replacement
                                                )
                                                break

                                        lang_abbr = re.sub(
                                            r"{{.*?}}", "", lang_cols[i_lang_col]
                                        ).strip()
                                        langmap[langname] = lang_abbr
                                        if langname_normalized:
                                            langmap[langname_normalized] = lang_abbr

                        if len(langmap):
                            langmap["krymskotatarština"] = "crh"
                            with open(WIKI_LANG_FILE, "w", encoding="utf8") as f:
                                json.dump(langmap, f, ensure_ascii=False)

        ent_titles = []
        ent_pages = []
        # context = CElTree.iterparse(self.pages_dump_fpath, events=("start", "end"))
        event, root = next(it_context_pages)
        with open("kb_cs", "a", encoding="utf-8") as fl:
            for event, elem in it_context_pages:
                if event == "end" and "page" in elem.tag:
                    is_entity = True
                    et_full_title = ""

                    for child in elem:
                        # na základě názvu stránky rozhodne, zda se jedná o entitu, či nikoliv
                        if "title" in child.tag:
                            is_entity = self._is_entity(child.text)
                            et_full_title = child.text

                        # získá obsah stránky
                        elif "revision" in child.tag:
                            for grandchild in child:
                                if "text" in grandchild.tag:
                                    if is_entity and grandchild.text:
                                        # přeskakuje stránky s přesměrováním a rozcestníkové stránky
                                        if re.search(
                                            r"#(?:redirect|přesměruj)|{{\s*Rozcestník",
                                            grandchild.text,
                                            flags=re.I,
                                        ):
                                            print(
                                                "[{}] skipping {}".format(
                                                    str(datetime.datetime.now().time()),
                                                    et_full_title,
                                                ),
                                                file=sys.stderr,
                                                flush=True,
                                            )
                                            continue

                                        ent_titles.append(et_full_title)
                                        ent_pages.append(grandchild.text)
                                        """
                                        pools[cur_pool] = pool.apply_async(self.process_entity, (et_full_title, grandchild.text, redirects, langmap))
                                        cur_pool = (cur_pool + 1) % max_pool
                                        if pools[cur_pool] == None:
                                            continue

                                        serialized_entity = pools[cur_pool].get()
                                        if serialized_entity:
                                            fl.write(serialized_entity + "\n")
                                        """
                    root.clear()

            if len(ent_titles) > 0:
                pool = Pool(processes=self.console_args.m)
                serialized_entities = pool.starmap(
                    self.process_entity,
                    zip(ent_titles, ent_pages, repeat(redirects), repeat(langmap)),
                )
                fl.write("\n".join(filter(None, serialized_entities)))
                pool.close()
                pool.join()

    def process_entity(self, et_full_title, page_content, redirects, langmap):
        # odstraňuje citace, reference a HTML poznámky
        print(
            "[{}] processing {}".format(
                str(datetime.datetime.now().time()), et_full_title
            ),
            file=sys.stderr,
            flush=True,
        )
        delimiter = "<"
        text_parts = page_content.split(delimiter)
        re_tag = r"^/?[^ />]+(?=[ />])"
        delete_mode = False
        tag_close = None

        for i_part, text_part in enumerate(
            text_parts[1:], 1
        ):  # skipping first one which is not begin of tag
            if delete_mode and tag_close:
                if text_part.startswith(tag_close):
                    text_parts[i_part] = text_part[len(tag_close) :]
                    delete_mode = False
                else:
                    text_parts[i_part] = ""
            else:
                matched_tag = re.search(re_tag, text_part)
                if matched_tag:
                    matched_tag = matched_tag.group(0)
                    if matched_tag in ["nowiki", "ref", "refereces"]:
                        tag_close = "/" + matched_tag + ">"
                        text_len = len(text_part)
                        text_part = re.sub(r"^.*?/>", "", text_part, 1)
                        if text_len == len(text_part):
                            delete_mode = True
                        text_parts[i_part] = "" if delete_mode else text_part
                    else:
                        tag_close = None
                        text_parts[i_part] = delimiter + text_part

        et_cont = "".join(text_parts)
        et_cont = re.sub(r"{{citace[^}]+?}}", "", et_cont, flags=re.I | re.S)
        et_cont = re.sub(r"{{cite[^}]+?}}", "", et_cont, flags=re.I)
        et_cont = re.sub(
            r"{{#tag:ref\s*\|(?:[^\|\[{]|\[\[[^\]]+\]\]|(?<!\[)\[[^\[\]]+\]|{{[^}]+}})*(\|[^}]+)?}}",
            "",
            et_cont,
            flags=re.I | re.S,
        )
        et_cont = re.sub(r"<!--.+?-->", "", et_cont, flags=re.DOTALL)

        link_multilines = re.findall(
            r"\[\[(?:Soubor|File)(?:(?:[^\[\]\n{]|{{[^}]+}}|\[\[[^\]]+\]\])*\n)+(?:[^\[\]\n{]|{{[^}]+}}|\[\[[^\]]+\]\])*\]\]",
            et_cont,
            flags=re.S,
        )
        for link_multiline in link_multilines:
            fixed_link_multiline = link_multiline.replace("\n", " ")
            et_cont = et_cont.replace(link_multiline, fixed_link_multiline)
        et_cont = re.sub(r"(<br(?:\s*/)?>)\n", r"\1", et_cont, flags=re.S)
        et_cont = re.sub(
            r"{\|(?!\s+class=(?:\"|')infobox(?:\"|')).*?\|}", "", et_cont, flags=re.S
        )
        ent_redirects = redirects[et_full_title] if et_full_title in redirects else []

        # stránka pojednává o osobě
        if EntPerson.is_person(et_cont) >= 2:
            et_url = self._get_url(et_full_title)
            et_person = EntPerson(
                et_full_title, "person", et_url, ent_redirects, langmap
            )
            return et_person.get_data(et_cont)

        # stránka pojednává o státu
        if EntCountry.is_country(et_cont):
            et_url = self._get_url(et_full_title)
            et_country = EntCountry(
                et_full_title, "country", et_url, ent_redirects, langmap
            )
            return et_country.get_data(et_cont)

        min_level = None
        ent_type = None

        # kontrola pojednávání o sídle
        id_level, id_subtype = EntSettlement.is_settlement(et_full_title, et_cont)
        if id_level:
            ent_type = "settlement"
            min_level = id_level

        # kontrola pojednávání o vodním toku
        id_level, tmp_subtype = EntWatercourse.is_watercourse(et_full_title, et_cont)
        if id_level and (min_level == None or id_level < min_level):
            ent_type = "watercourse"
            min_level = id_level
            id_subtype = tmp_subtype

        # kontrola pojednávání o vodní ploše
        id_level, tmp_subtype = EntWaterArea.is_water_area(et_full_title, et_cont)
        if id_level and (min_level == None or id_level < min_level):
            ent_type = "waterarea"
            min_level = id_level
            id_subtype = tmp_subtype

        # kontrola pojednávání o geografické entitě
        id_level, tmp_subtype = EntGeo.is_geo(et_full_title, et_cont)
        if id_level and (min_level == None or id_level < min_level):
            ent_type = "geo"
            min_level = id_level
            id_subtype = tmp_subtype

        # stránka pojednává o sídle
        if ent_type == "settlement":
            et_url = self._get_url(et_full_title)
            et_settlement = EntSettlement(
                et_full_title, ent_type, et_url, ent_redirects, langmap
            )
            return et_settlement.get_data(et_cont)

        # stránka pojednává o vodním toku
        if ent_type == "watercourse":
            et_url = self._get_url(et_full_title)
            et_watercourse = EntWatercourse(
                et_full_title, ent_type, et_url, ent_redirects, langmap
            )
            return et_watercourse.get_data(et_cont)

        # stránka pojednává o vodní ploše
        if ent_type == "waterarea":
            et_url = self._get_url(et_full_title)
            et_water_area = EntWaterArea(
                et_full_title, ent_type, et_url, ent_redirects, langmap
            )
            return et_water_area.get_data(et_cont)

        # stránka pojednává o geografické entitě
        if ent_type == "geo":
            et_url = self._get_url(et_full_title)
            et_geo = EntGeo(et_full_title, ent_type, et_url, ent_redirects, langmap)
            et_geo.set_entity_subtype(id_subtype)
            return et_geo.get_data(et_cont)

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


# hlavní část programu
if __name__ == "__main__":
    wiki_extract = WikiExtract()

    wiki_extract.parse_args()
    wiki_extract.create_head_kb()
    wiki_extract.del_knowledge_base("kb_cs")
    wiki_extract.parse_xml_dump()
    wiki_extract.assign_version()
