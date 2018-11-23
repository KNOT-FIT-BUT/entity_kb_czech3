#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autor: Michal Planička (xplani02)

Popis souboru:
Soubor obsahuje třídu 'WikiExtract', jež uchovává metody pro parsování argumentů příkazové řádky, parsování XML dumpu Wikipedie, vytvoření znalostní báze a hlavičkového souboru a správu entit a jejich údajů.

Poznámky:
[\-–—−]
[^\W\d_] - pouze písmena
"""

import xml.etree.cElementTree as CElTree
from ent_person import *
from ent_country import *
from ent_settlement import *
from ent_watercourse import *
from ent_waterarea import *
from ent_geo import *
from os import remove
import argparse


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

    _get_title_and_url(title) - vygeneruje název entity bez kulatých závorek a URL stránky
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
            "<person>ID\tTYPE\tNAME\t{m}ALIASES\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<person:fictional>ID\tTYPE\tNAME\t{m}ALIASES\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<country>ID\tTYPE\tNAME\t{m}ALIASES\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<country:former>ID\tTYPE\tNAME\t{m}ALIASES\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<settlement>ID\tTYPE\tNAME\t{m}ALIASES\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tCOUNTRY\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<watercourse>ID\tTYPE\tNAME\t{m}ALIASES\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLENGTH\tAREA\tSTREAMFLOW\tSOURCE_LOC\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<waterarea>ID\tTYPE\tNAME\t{m}ALIASES\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tAREA\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<geo:relief>ID\tTYPE\tNAME\t{m}ALIASES\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<geo:waterfall>ID\tTYPE\tNAME\t{m}ALIASES\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tTOTAL HEIGHT\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<geo:island>ID\tTYPE\tNAME\t{m}ALIASES\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<geo:peninsula>ID\tTYPE\tNAME\t{m}ALIASES\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<geo:continent>ID\tTYPE\tNAME\t{m}ALIASES\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<organisation>ID\tTYPE\tNAME\t{m}ALIASES\tFOUNDED\tCANCELLED\tORGANIZATION TYPE\tLOCATION\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            "<event>ID\tTYPE\tNAME\t{m}ALIASES\tSTART\tEND\tLOCATION\tDESCRIPTION\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n"
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
            remove(kb_name)
        except OSError:
            pass

    @staticmethod
    def _get_title_and_url(title):
        """
        Vygeneruje název entity bez kulatých závorek a URL stránky.

        Parametry:
        title - původní název stránky (str)

        Návratové hodnoty:
        Dvojice (str, str) obsahující modifikovaný název entity a URL stránky. (Tuple[str])
        """
        mod_title = re.sub(r"\s+\(.+?\)\s*$", "", title)
        wiki_url = "https://cs.wikipedia.org/wiki/" + title.replace(" ", "_")

        return mod_title, wiki_url

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
        if title.startswith(("Wikipedie:", "Redaktor:", "Soubor:", "MediaWiki:", "Šablona:", "Pomoc:", "Kategorie:", "Speciální:", "Portál:", "Modul:", "Seznam", "Geografie", "Společenstvo")):
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

    def parse_args(self):
        """
        Parsuje argumenty zadané při spuštění skriptu.
        """
        console_args_parser = argparse.ArgumentParser()
        console_args_parser.add_argument("src_file", nargs="?", default="/mnt/minerva1/nlp/corpora_datasets/monolingual/czech/wikipedia/cswiki-latest-pages-articles.xml", type=str, help="zdrojový soubor")
        # console_args_parser.add_argument("-d", "--dir", nargs="?", default="/mnt/minerva1/nlp/projects/entity_kb_czech/data/cs/", type=str, help="složka, ve které se nachází soubory s entitami")
        self.console_args = console_args_parser.parse_args()

    def parse_xml_dump(self):
        """
        Parsuje XML dump Wikipedie, prochází jednotlivé stránky a vyhledává entity.

        Poznámky:
        - založeno na: http://effbot.org/zone/element-iterparse.htm
        """
        # # načtení entit
        # self._load_entities()

        # parsování XML souboru
        context = CElTree.iterparse(self.console_args.src_file, events=("start", "end"))
        context = iter(context)
        event, root = next(context)

        for event, elem in context:
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
                                    if re.search(r"#(?:redirect|přesměruj)|{{\s*Rozcestník", grandchild.text, flags=re.I):
                                        continue

                                    # odstraňuje citace, reference a HTML poznámky
                                    et_cont = re.sub(r"</?nowiki>", "", grandchild.text, flags=re.I)  # kvůli ref
                                    et_cont = re.sub(r"<ref[^>]*>(?:[^<]*</ref>)?", "", et_cont, flags=re.I)
                                    et_cont = re.sub(r"{{citace[^}]+?}}", "", et_cont, flags=re.I)
                                    et_cont = re.sub(r"{{cite[^}]+?}}", "", et_cont, flags=re.I)
                                    et_cont = re.sub(r"{{#tag:ref[^}]+?}}", "", et_cont, flags=re.I)
                                    et_cont = re.sub(r"<!--.+?-->", "", et_cont, flags=re.DOTALL)

                                    # stránka pojednává o osobě
                                    if EntPerson.is_person(et_cont) >= 2:
                                        et_mod_title, et_url = self._get_title_and_url(et_full_title)
                                        et_person = EntPerson(et_mod_title, "person", et_url)
                                        et_person.get_data(et_cont)
                                        et_person.write_to_file()
                                        continue

                                    # stránka pojednává o státu
                                    if EntCountry.is_country(et_cont):
                                        et_mod_title, et_url = self._get_title_and_url(et_full_title)
                                        et_country = EntCountry(et_mod_title, "country", et_url)
                                        et_country.get_data(et_cont)
                                        et_country.write_to_file()
                                        continue

                                    # stránka pojednává o sídle
                                    id_level, id_type = EntSettlement.is_settlement(et_full_title, et_cont)
                                    if id_level:
                                        et_mod_title, et_url = self._get_title_and_url(et_full_title)
                                        et_settlement = EntSettlement(et_mod_title, "settlement", et_url)
                                        et_settlement.get_data(et_cont)
                                        et_settlement.write_to_file()
                                        continue

                                    # stránka pojednává o vodním toku
                                    id_level, id_type = EntWatercourse.is_watercourse(et_full_title, et_cont)
                                    if id_level:
                                        et_mod_title, et_url = self._get_title_and_url(et_full_title)
                                        et_watercourse = EntWatercourse(et_mod_title, "watercourse", et_url)
                                        et_watercourse.get_data(et_cont)
                                        et_watercourse.write_to_file()
                                        continue

                                    # stránka pojednává o vodní ploše
                                    id_level, id_type = EntWaterArea.is_water_area(et_full_title, et_cont)
                                    if id_level:
                                        et_mod_title, et_url = self._get_title_and_url(et_full_title)
                                        et_water_area = EntWaterArea(et_mod_title, "waterarea", et_url)
                                        et_water_area.get_data(et_cont)
                                        et_water_area.write_to_file()
                                        continue

                                    # stránka pojednává o geografické entitě
                                    id_level, id_type = EntGeo.is_geo(et_full_title, et_cont)
                                    if id_level:
                                        et_mod_title, et_url = self._get_title_and_url(et_full_title)
                                        et_geo = EntGeo(et_mod_title, "geo", et_url)
                                        et_geo.set_entity_subtype(id_type)
                                        et_geo.get_data(et_cont)
                                        et_geo.write_to_file()
                                        continue

                root.clear()


# hlavní část programu
if __name__ == "__main__":
    wiki_extract = WikiExtract()

    wiki_extract.parse_args()
    wiki_extract.create_head_kb()
    wiki_extract.del_knowledge_base("kb_cs")
    wiki_extract.parse_xml_dump()
