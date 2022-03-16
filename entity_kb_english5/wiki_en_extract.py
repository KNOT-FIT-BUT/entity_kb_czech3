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
import xml.etree.cElementTree as CElTree
from itertools import repeat, tee

from ent_person import *
from ent_country import *
from ent_settlement import *
from ent_waterarea import *

TESTING_PATH = "./testing_data/more_waterareas.xml"

class WikiExtract(object):
    def __init__(self):
        """
        inicializace třídy
        """
        # TODO: inicializace
        pass

    def parse_xml_dump(self):
        """
        Parsuje XML dump Wikipedie, prochází jednotlivé stránky a vyhledává entity.
        Poznámky:
        - založeno na: http://effbot.org/zone/element-iterparse.htm
        """
        # TODO: xml parser
        context = CElTree.iterparse(TESTING_PATH, events=("start", "end"))

        # langmap?
        it_context_langmap, it_context_pages = tee(context)
        #event, root = next(it_context_langmap)

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
            # TODO: multiprocessing
            counter = 0
            with open("kb_en", "w", encoding="utf-8") as file:
                for i in range(len(ent_titles)):
                    entity = self.process_entity(ent_titles[i], ent_pages[i])
                    if entity:
                        file.write(f"{entity}\n")
                        counter += 1
            print(counter)

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
            return person.serialize()

        # TODO: country
        if (EntCountry.is_country(page_content)):
            country = EntCountry(page_title, "country", self._get_link(page_title))
            country.get_data(page_content)
            country.assign_values()
            return country.serialize()

        # TODO: settlement
        if (EntSettlement.is_settlement(page_content)):
            settlement = EntSettlement(page_title, "settlement", self._get_link(page_title))
            settlement.get_data(page_content)
            settlement.assign_values()
            return settlement.serialize()

        # TODO: watercourse

        # TODO: waterarea
        if (EntWaterArea.is_water_area(page_content)):
            water_area = EntWaterArea(page_title, "waterarea", self._get_link(page_title))
            water_area.get_data(page_content)
            water_area.assign_values()
            return water_area.serialize()

        # TODO: geo
        pass

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

        # remove break lines
        clean_content = re.sub(r"<.*?/?>", "", clean_content, flags=re.DOTALL)

        # TODO: clean this up
        # remove comments
        #clean_content = re.sub(r"<!--.+?-->", "", clean_content, flags=re.DOTALL)

        return clean_content


if __name__ == "__main__":
    wiki_extract = WikiExtract()
    
    wiki_extract.parse_xml_dump()