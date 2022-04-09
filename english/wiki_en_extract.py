"""
Projekt: entity_kb_english5
Autor: Jan Kapsa (xkapsa00)
Popis souboru:
    Soubor obsahuje třídu 'WikiExtract', jež uchovává metody pro parsování argumentů příkazové řádky, 
    parsování XML dumpu Wikipedie, vytvoření znalostní báze a hlavičkového souboru a správu entit a jejich údajů.
Poznámky:
    založeno na projektu entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
"""

import re
import os
import xml.etree.cElementTree as CElTree
from itertools import repeat, tee
import argparse
import time
from multiprocessing import Pool

from ent_person import *
from ent_country import *
from ent_settlement import *
from ent_waterarea import *
from ent_watercourse import *
from ent_geo import *

TESTING_PATH = "./testing_data/xml/people.xml"
LANG_MAP = {"cz": "cs"}

class WikiExtract(object):
    def __init__(self):
        """
        inicializace třídy
        """
        # TODO: inicializace
        self.console_args = None

    @staticmethod
    def create_head_kb():
        """
        Vytváří hlavičkový soubor HEAD-KB, který upřesňuje množinu záznamů znalostní báze.
        """
        entities = [
            "<person>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
            #"<person>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\n",
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

        with open("../HEAD-KB", "w", encoding="utf-8") as file:
            for entity in entities:
                file.write(entity)

    def parse_args(self):
        """
        Parsuje argumenty zadané při spuštění skriptu.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-I",
            "--indir",
            # default="/mnt/minerva1/nlp/corpora_datasets/monolingual/czech/wikipedia/",
            default="./testing_data/xml/",
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
            self.console_args.redirects, "redirects_from_{}wiki-{}-pages-articles.xml"
        )
        if self.console_args.dev:
            self.console_args._kb_stability = "dev"
        elif self.console_args.test:
            self.console_args._kb_stability = "test"
        else:
            self.console_args._kb_stability = ""

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
        with open("../VERSION", "w") as f:
            f.write(
                "{}_{}-{}{}".format(
                    self.console_args.lang,
                    dump_version,
                    int(round(time.time())),
                    str_kb_stability,
                )
            )

    def parse_xml_dump(self):
        """
        Parsuje XML dump Wikipedie, prochází jednotlivé stránky a vyhledává entity.
        Poznámky:
        - založeno na: http://effbot.org/zone/element-iterparse.htm
        """
        # TODO: xml parser
        context = CElTree.iterparse(self.pages_dump_fpath, events=("start", "end"))

        # langmap?
        it_context_langmap, it_context_pages = tee(context)
        #event, root = next(it_context_langmap)

        # TODO: make json file out of https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes

        ent_titles = []
        ent_pages = []
        event, root = next(it_context_pages)
        for event, elem in it_context_pages:
            # hledá <page> element
            if event == "end" and "page" in elem.tag:
                # xml -> <page> -> <title>
                # xml -> <page> -> <revision>
                is_entity = False
                title = ""

                for child in elem:
                    # získá title stránky
                    if "title" in child.tag:
                        is_entity = self.is_entity(child.text)
                        if is_entity:
                            title = child.text
                    # získá text stránky
                    elif "revision" in child.tag:
                        for grandchild in child:
                            if "text" in grandchild.tag:
                                if is_entity and grandchild.text:                        
                                    # TODO: přeskoč redirecty a rozcestníky
                                    #print(grandchild.text)
                                    ent_titles.append(title)
                                    ent_pages.append(grandchild.text)
                    elif "redirect" in child.tag:
                        break
                root.clear()

        if len(ent_titles):
            with open("../kb_en", "w", encoding="utf-8") as file:
                pool = Pool(processes=self.console_args.m)
                serialized_entities = pool.starmap(
                    self.process_entity,
                    zip(ent_titles, ent_pages),
                )
                file.write("\n".join(filter(None, serialized_entities)))
                pool.close()
                pool.join()
            print(len(list(filter(None, serialized_entities))))

    # filters out wikipedia special pages and date pages
    @staticmethod
    def is_entity(title):
        # special pages
        # TODO: add more special tags
        if title.startswith(
            (
                "Wikipedia:",
                "Category:",
                "Help:",
                "Template:",
                "Module:",
                "Portal:"
            )
        ):
            return False
        
        # dates
        # TODO: is this regex pattern correct? the second part is for years but can there be a title with numbers that is not a date?
        # this is different to czech wiki e.g.: czech: 28. říjen | english: September 28
        if re.search("[^\W\d_]+? \d{1,2}|\d{2,4}", title):
            return False

        return True

    def process_entity(self, page_title, page_content):
        # TODO:
        page_content = self._remove_not_improtant(page_content)

        #print("DEBUG: processing: " + page_title)

        # TODO: person
        if (EntPerson.is_person(page_content)):
            person = EntPerson(page_title, "person", self._get_link(page_title))
            person.get_data(page_content)
            person.assign_values()
            return person.__repr__()

        # TODO: country
        if (EntCountry.is_country(page_content, page_title)):
            country = EntCountry(page_title, "country", self._get_link(page_title))
            country.get_data(page_content)
            country.assign_values()
            return country.__repr__()

        # TODO: settlement
        if (EntSettlement.is_settlement(page_content)):
            settlement = EntSettlement(page_title, "settlement", self._get_link(page_title))
            settlement.get_data(page_content)
            settlement.assign_values()
            return settlement.__repr__()

        # TODO: watercourse
        if (EntWaterCourse.is_water_course(page_content)):
            water_course = EntWaterCourse(page_title, "watercourse", self._get_link(page_title))
            water_course.get_data(page_content)
            water_course.assign_values()
            return water_course.__repr__()

        # TODO: waterarea
        if (EntWaterArea.is_water_area(page_content)):
            water_area = EntWaterArea(page_title, "waterarea", self._get_link(page_title))
            water_area.get_data(page_content)
            water_area.assign_values()
            return water_area.__repr__()

        # TODO: geo
        is_geo, prefix = EntGeo.is_geo(page_content, page_title)
        if is_geo:
            geo = EntGeo(page_title, f"geo:{prefix}", self._get_link(page_title))
            geo.get_data(page_content)
            geo.assign_values()
            return geo.__repr__()

    @staticmethod
    def _get_link(link):
        wiki_link = link.replace(" ", "_")
        return f"https://en.wikipedia.org/wiki/{wiki_link}"

    # TODO: change name later?
    @staticmethod
    def _remove_not_improtant(page_content):
        # odstraní referencí a HTML komentáře
        clean_content = page_content

        # TODO: QUESTION:
        # I'm doing this with regex and not splitting by <
        # maybe there is more tags not covered here though
        # but do I really need to do this for the whole page?
        # I'm only gonna use first paragraph and category part at the end

        # remove comments
        clean_content = re.sub(r"<!--.*?-->", "", clean_content, flags=re.DOTALL)

        # remove references        
        clean_content = re.sub(r"<ref.*?/(?:ref)?>", "", clean_content, flags=re.DOTALL)

        # remove {{efn ... }}
        arr = []
        for m in re.finditer(r"{{efn", clean_content):
            index = m.start()+1
            indentation = 1            
            while (indentation != 0):
                if clean_content[index] == "{":
                    indentation += 1
                elif clean_content[index] == "}":
                    indentation -= 1
                index += 1
            arr.append((m.start(), index))
        arr = sorted(arr, reverse=True)
        for i in arr:
            clean_content = clean_content[:i[0]] + clean_content[i[1]:]
        
        # remove break lines
        clean_content = re.sub(r"<.*?/?>", "", clean_content, flags=re.DOTALL)

        # TODO: clean this up
        # remove comments
        #clean_content = re.sub(r"<!--.+?-->", "", clean_content, flags=re.DOTALL)

        return clean_content



if __name__ == "__main__":
    wiki_extract = WikiExtract()
    
    wiki_extract.parse_args()
    wiki_extract.create_head_kb()
    wiki_extract.parse_xml_dump()
    wiki_extract.assign_version()